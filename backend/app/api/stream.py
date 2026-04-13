# =============================================
# app/api/stream.py
# 역할: 카메라 영상 스트리밍 및 모드 전환 API 엔드포인트
#       - GET  /stream/rgb      → RGB 카메라 MJPEG 스트리밍
#       - GET  /stream/thermal  → 열화상 카메라 MJPEG 스트리밍
#       - GET  /stream/blend    → RGB+열화상 합성 MJPEG 스트리밍
#       - POST /stream/mode     → 카메라 모드 전환 + WS 브로드캐스트
#       - GET  /stream/mode     → 현재 활성 카메라 모드 조회
# =============================================

from typing import Literal

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.dependencies import get_rgb_camera, get_thermal_camera, get_ws_manager
from app.services.camera import CameraService
from app.core.streaming import mjpeg_generator, mjpeg_blend_generator
from app.core.ws_manager import ConnectionManager

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
