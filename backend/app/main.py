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

from app.config import settings
from app.db.init_db import init_db
from app.api.router import api_router
from app.services.camera import rgb_camera_service, thermal_camera_service
from app.services.yolo_inference import yolo_service


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    애플리케이션 시작/종료 시 실행되는 lifespan 핸들러.
    순서: DB 초기화 → 카메라 오픈 → YOLO 모델 로드
    """
    # ── 시작 ─────────────────────────────────
    print("[AeroInspect] 서버 시작 중...")

    # DB 테이블 생성 (처음 실행 시)
    await init_db()
    print("[AeroInspect] DB 초기화 완료")

    # RGB 카메라 (USB Capture Card) 열기
    await rgb_camera_service.open()
    print(f"[AeroInspect] RGB 카메라 (index={settings.RGB_CAMERA_INDEX}) 열림")

    # 열화상 카메라 (IRC-256CA) 열기
    await thermal_camera_service.open()
    print(f"[AeroInspect] 열화상 카메라 (index={settings.THERMAL_CAMERA_INDEX}) 열림")

    # YOLOv8 모델 로드 (가중치 파일 존재 시)
    yolo_service.load_model()
    print("[AeroInspect] YOLOv8 모델 로드 완료")

    print("[AeroInspect] 서버 준비 완료 ✓")

    yield  # 앱 실행 중

    # ── 종료 ─────────────────────────────────
    print("[AeroInspect] 서버 종료 중...")
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

# ── CORS 설정 ─────────────────────────────────
# React 개발서버(5173) 및 프로덕션 도메인 허용
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── 라우터 마운트 ─────────────────────────────
app.include_router(api_router, prefix="/api/v1")


@app.get("/", tags=["Health"])
async def root():
    """서버 상태 확인용 헬스체크 엔드포인트"""
    return {"status": "ok", "service": "AeroInspect API", "version": "1.3.0"}


@app.get("/health", tags=["Health"])
async def health_check():
    """카메라 및 서비스 상태 확인"""
    return {
        "status": "ok",
        "rgb_camera": rgb_camera_service.is_open,
        "thermal_camera": thermal_camera_service.is_open,
        "yolo_loaded": yolo_service.is_loaded,
    }
