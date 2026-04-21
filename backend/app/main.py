# =============================================
# app/main.py
# 역할: FastAPI 애플리케이션 진입점
#       - lifespan 컨텍스트 매니저로 시작/종료 시 리소스 초기화/해제
#       - CORS 미들웨어 설정
#       - 모든 API 라우터 마운트
#       - 서비스 싱글톤(카메라, YOLO, WebSocket 매니저) 초기화
# 실행: uvicorn app.main:app --reload --port 8000
# =============================================

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.core.logging import configure_logging, get_logger
from app.core.middleware import RequestIDMiddleware
from app.db.init_db import init_db
from app.api.router import api_router
from app.services.camera import rgb_camera_service, thermal_camera_service
from app.services.recording import recording_service
from app.services.yolo_inference import yolo_service
from app.services.inference_pipeline import pipeline as inference_pipeline
from app.services.wallpaper_classifier import wallpaper_classifier
from app.services.lidar import lidar_service
from app.services.telemetry_cache import telemetry_cache
from app.core.stream_inference import stream_inference_worker
from app.services.defect_taxonomy import WALLPAPER_CLASSES

# 로깅 설정 (앱 import 시점에 1회)
configure_logging(
    json_output=settings.LOG_JSON,
    level=settings.LOG_LEVEL,
)
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    애플리케이션 시작/종료 시 실행되는 lifespan 핸들러.
    순서: DB 초기화 → 카메라 오픈 → YOLO 모델 로드
    """
    # ── 시작 ─────────────────────────────────
    print("[AeroInspect] 서버 시작 중...")

    # DB 테이블 생성 (처음 실행 시)
    try:
        await init_db()
        print("[AeroInspect] DB 초기화 완료")
    except Exception as e:
        print(f"[AeroInspect] DB 초기화 실패 (DB 연결 안 됨, 임시 무시): {e}")

    # RGB 카메라 (USB Capture Card) 열기
    await rgb_camera_service.open()
    print(f"[AeroInspect] RGB 카메라 (index={settings.RGB_CAMERA_INDEX}) 열림")

    # 열화상 카메라 (IRC-256CA) 열기
    await thermal_camera_service.open()
    print(f"[AeroInspect] 열화상 카메라 (index={settings.THERMAL_CAMERA_INDEX}) 열림")

    # 3-모델 추론 파이프라인 로드 (YOLO thermal + delam + ResNet 벽지)
    # 가중치 파일 누락 시 FileNotFoundError가 나지만 서버 자체는 기동 유지 (503 반환)
    try:
        yolo_service.load_model()  # shim → inference_pipeline.load_models()
        print("[AeroInspect] 3-모델 추론 파이프라인 로드 완료")
    except FileNotFoundError as e:
        print(f"[AeroInspect] AI 모델 로드 실패 (가중치 없음): {e}")

    # TF-Luna LiDAR 시리얼 연결 (실패해도 서버는 계속)
    try:
        await lidar_service.start()
    except Exception as e:
        print(f"[AeroInspect] LiDAR 시작 실패 (좌표 없이 계속): {e}")

    # WebSocket 스트림 추론 워커 시작 (드롭 큐)
    await stream_inference_worker.start()

    print("[AeroInspect] 서버 준비 완료")

    yield  # 앱 실행 중

    # ── 종료 ─────────────────────────────────
    print("[AeroInspect] 서버 종료 중...")

    # LiDAR 시리얼 종료
    try:
        await lidar_service.stop()
    except Exception as e:
        print(f"[AeroInspect] LiDAR 종료 중 오류: {e}")

    # 텔레메트리 캐시 초기화
    telemetry_cache.clear()

    # 스트림 추론 워커 종료
    await stream_inference_worker.stop()

    # 녹화 중이면 안전하게 중지
    if recording_service.is_recording:
        await recording_service.stop()
        print("[AeroInspect] 녹화 중지 완료")

    await rgb_camera_service.release()
    await thermal_camera_service.release()
    print("[AeroInspect] 카메라 자원 해제 완료")


# FastAPI 앱 생성
app = FastAPI(
    title="AeroInspect API",
    description="실제 드론 기반 자율 하자 점검 플랫폼 - FastAPI 백엔드",
    version="1.3.0",
    lifespan=lifespan,
)

# ── 미들웨어 ─────────────────────────────────
# RequestIDMiddleware 먼저 (가장 바깥) → CORS
# add_middleware는 LIFO 순서로 dispatch되므로 마지막에 추가한 것이 가장 바깥.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RequestIDMiddleware)

# ── 라우터 마운트 ─────────────────────────────
app.include_router(api_router, prefix="/api/v1")

# ── 정적 파일 서빙 (업로드된 프로필 이미지 등) ──
import os
os.makedirs("./uploads/profiles", exist_ok=True)
app.mount("/uploads", StaticFiles(directory="./uploads"), name="uploads")


@app.get("/", tags=["Health"])
async def root():
    """서버 상태 확인용 헬스체크 엔드포인트"""
    return {"status": "ok", "service": "AeroInspect API", "version": "1.3.0"}


@app.get("/health", tags=["Health"])
async def health_check():
    """
    카메라 + AI 3-모델 + 스트림 워커 상태 확인.
    프롬프트 스펙대로 models_loaded / device / frame_skip / wallpaper_classes_count 포함.
    """
    models = inference_pipeline.models_loaded
    all_loaded = models.yolo_thermal and models.yolo_delam and models.wallpaper
    return {
        "status": "ok" if all_loaded else "degraded",
        "device": inference_pipeline.device,
        "models_loaded": {
            "yolo_thermal": models.yolo_thermal,
            "yolo_delam": models.yolo_delam,
            "wallpaper": models.wallpaper,
        },
        "wallpaper_classes_count": len(WALLPAPER_CLASSES),
        "stream_worker_running": stream_inference_worker.is_running,
        "frame_skip": settings.FRAME_SKIP,
        "rgb_camera": rgb_camera_service.is_open,
        "thermal_camera": thermal_camera_service.is_open,
        "lidar": {
            "distance_m": lidar_service.latest_distance_m,
            "connected": lidar_service.latest_distance_m is not None,
        },
        "telemetry_cache": {
            "ready": telemetry_cache.is_ready,
            "age_sec": telemetry_cache.age_sec,
        },
    }
