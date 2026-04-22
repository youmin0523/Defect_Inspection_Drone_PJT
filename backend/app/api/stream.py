# =============================================
# app/api/stream.py
# 역할: 카메라 영상 스트리밍, 모드 전환, 녹화 제어 API 엔드포인트
#       - GET  /stream/rgb      → RGB 카메라 MJPEG 스트리밍
#       - GET  /stream/thermal  → 열화상 카메라 MJPEG 스트리밍
#       - GET  /stream/blend    → RGB+열화상 합성 MJPEG 스트리밍
#       - POST /stream/mode     → 카메라 모드 전환 + WS 브로드캐스트
#       - GET  /stream/mode     → 현재 활성 카메라 모드 조회
#       - POST /stream/record/start  → 녹화 시작
#       - POST /stream/record/stop   → 녹화 중지
#       - GET  /stream/record/status → 녹화 상태 조회
#       - GET  /stream/record/list   → 녹화 파일 목록
#       - GET  /stream/record/{filename} → 녹화 파일 다운로드
#       - DELETE /stream/record/{filename} → 녹화 파일 삭제
# =============================================

import os
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse, FileResponse
from pydantic import BaseModel

from app.config import settings
from app.dependencies import get_rgb_camera, get_thermal_camera, get_ws_manager, get_recording_service
from app.services.camera import CameraService
from app.services.recording import RecordingService
from app.core.streaming import mjpeg_generator, mjpeg_blend_generator
from app.core.stream_inference import stream_inference_worker
from app.core.ws_manager import ConnectionManager
from app.schemas.monitoring import StreamStatsResponse
from app.services.lidar import lidar_service
from app.services.telemetry_cache import telemetry_cache

router = APIRouter()

# 현재 활성 카메라 모드 상태 (모듈 레벨 상태 — 단일 워커 보장)
_active_mode: str = "rgb"

# MJPEG multipart 미디어 타입
MJPEG_CONTENT_TYPE = "multipart/x-mixed-replace; boundary=frame"


class StreamModeRequest(BaseModel):
    mode: Literal["rgb", "thermal", "blend"]


@router.get("/rgb")
async def stream_rgb(
    rgb_camera: CameraService = Depends(get_rgb_camera),
):
    """
    RGB 카메라 MJPEG 스트리밍.
    브라우저 <img src="/api/v1/stream/rgb"> 태그로 직접 소비 가능.
    """
    return StreamingResponse(
        mjpeg_generator(rgb_camera),
        media_type=MJPEG_CONTENT_TYPE,
    )


@router.get("/thermal")
async def stream_thermal(
    thermal_camera: CameraService = Depends(get_thermal_camera),
):
    """
    열화상 카메라 MJPEG 스트리밍.
    IRC-256CA 의사색상(INFERNO 컬러맵) 적용 후 스트리밍.
    """
    return StreamingResponse(
        mjpeg_generator(thermal_camera),
        media_type=MJPEG_CONTENT_TYPE,
    )


@router.get("/blend")
async def stream_blend(
    rgb_camera: CameraService = Depends(get_rgb_camera),
    thermal_camera: CameraService = Depends(get_thermal_camera),
):
    """
    RGB + 열화상 알파 합성 MJPEG 스트리밍.
    config.THERMAL_BLEND_ALPHA 값으로 투명도 조절.
    """
    return StreamingResponse(
        mjpeg_blend_generator(rgb_camera, thermal_camera),
        media_type=MJPEG_CONTENT_TYPE,
    )


@router.post("/mode")
async def set_stream_mode(
    request: StreamModeRequest,
    manager: ConnectionManager = Depends(get_ws_manager),
):
    """
    카메라 모드 전환.
    변경 후 WebSocket "camera" 채널로 mode_changed 이벤트 브로드캐스트.
    프론트엔드에서 이 이벤트를 수신하여 다중 클라이언트 동기화.
    """
    global _active_mode
    _active_mode = request.mode

    # 모든 연결된 클라이언트에게 모드 변경 알림
    await manager.broadcast("camera", {
        "type": "camera.mode_changed",
        "data": {"mode": _active_mode},
    })

    return {"mode": _active_mode, "message": f"카메라 모드가 '{_active_mode}'로 변경되었습니다."}


@router.get("/mode")
async def get_stream_mode():
    """현재 활성 카메라 모드 조회"""
    return {"mode": _active_mode}


@router.get("/stats", response_model=StreamStatsResponse)
async def get_stream_stats() -> StreamStatsResponse:
    """
    WebSocket 실시간 추론 워커 상태 + LiDAR/telemetry 헬스 조회.
    대시보드 좌측 상단 배지 및 운영 모니터링 용도.
    """
    return StreamStatsResponse(
        worker={
            "running": stream_inference_worker.is_running,
            **stream_inference_worker.stats,
        },
        telemetry_cache={
            "ready": telemetry_cache.is_ready,
            "age_sec": telemetry_cache.age_sec,
        },
        lidar={
            "connected": lidar_service.latest_distance_m is not None,
            "distance_m": lidar_service.latest_distance_m,
        },
    )


# ── 녹화 제어 엔드포인트 ─────────────────────────────
# 녹화 시 RGB + Thermal 동시에 별도 파일로 저장


@router.post("/record/start")
async def start_recording(
    rgb_camera: CameraService = Depends(get_rgb_camera),
    thermal_camera: CameraService = Depends(get_thermal_camera),
    recorder: RecordingService = Depends(get_recording_service),
):
    """
    영상 녹화 시작.
    RGB와 Thermal 카메라를 동시에 각각 별도 mp4 파일로 녹화.
    """
    try:
        files = await recorder.start(
            rgb_camera=rgb_camera,
            thermal_camera=thermal_camera,
        )
        return {"message": "녹화가 시작되었습니다.", **files}
    except RuntimeError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.post("/record/stop")
async def stop_recording(
    recorder: RecordingService = Depends(get_recording_service),
):
    """영상 녹화 중지 및 파일 저장."""
    try:
        result = await recorder.stop()
        return {"message": "녹화가 중지되었습니다.", **result}
    except RuntimeError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.get("/record/status")
async def recording_status(
    recorder: RecordingService = Depends(get_recording_service),
):
    """현재 녹화 상태 조회"""
    return recorder.status


@router.get("/record/list")
async def list_recordings(
    recorder: RecordingService = Depends(get_recording_service),
):
    """저장된 녹화 파일 목록 조회 (타임스탬프 기준 세션 그룹핑)"""
    return {"recordings": recorder.list_recordings()}


@router.get("/record/{filename}")
async def download_recording(filename: str):
    """녹화 파일 다운로드"""
    safe_name = os.path.basename(filename)
    filepath = os.path.join(settings.RECORDING_OUTPUT_DIR, safe_name)

    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="파일을 찾을 수 없습니다.")

    return FileResponse(
        filepath,
        media_type="video/mp4",
        filename=safe_name,
    )


@router.delete("/record/{filename}")
async def delete_recording(
    filename: str,
    recorder: RecordingService = Depends(get_recording_service),
):
    """녹화 파일 삭제 (개별 파일)"""
    if recorder.delete_recording(filename):
        return {"message": f"'{filename}' 파일이 삭제되었습니다."}
    raise HTTPException(status_code=404, detail="파일을 찾을 수 없습니다.")


@router.delete("/record/session/{timestamp}")
async def delete_recording_session(
    timestamp: str,
    recorder: RecordingService = Depends(get_recording_service),
):
    """녹화 세션 삭제 (동일 타임스탬프의 rgb+thermal 파일 일괄 삭제)"""
    deleted = recorder.delete_session(timestamp)
    if deleted:
        return {"message": f"세션 '{timestamp}' 삭제 완료 ({deleted}개 파일)"}
    raise HTTPException(status_code=404, detail="해당 세션을 찾을 수 없습니다.")
