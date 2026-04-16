# =============================================
# app/api/router.py
# 역할: 모든 서브 라우터를 하나의 api_router로 통합
#       - main.py에서 app.include_router(api_router, prefix="/api/v1")로 마운트
#       - 각 도메인별 라우터에 태그와 prefix 부여
# =============================================

from fastapi import APIRouter

from app.api import auth, defects, stream, websocket, report

api_router = APIRouter()

# 인증 / 회원가입
api_router.include_router(
    auth.router,
    prefix="/auth",
    tags=["Auth"],
)

# 하자 탐지 로그 CRUD
api_router.include_router(
    defects.router,
    prefix="/defects",
    tags=["Defects"],
)

# 카메라 스트리밍 (RGB / 열화상 / 블렌드)
api_router.include_router(
    stream.router,
    prefix="/stream",
    tags=["Stream"],
)

# WebSocket 실시간 이벤트
api_router.include_router(
    websocket.router,
    prefix="",
    tags=["WebSocket"],
)

# LLM 하자 점검 보고서 생성
api_router.include_router(
    report.router,
    prefix="/report",
    tags=["Report"],
)
