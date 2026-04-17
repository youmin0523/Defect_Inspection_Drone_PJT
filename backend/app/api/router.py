# =============================================
# app/api/router.py
# 역할: 모든 서브 라우터를 하나의 api_router로 통합
#       - main.py에서 app.include_router(api_router, prefix="/api/v1")로 마운트
#       - 각 도메인별 라우터에 태그와 prefix 부여
# =============================================

from fastapi import APIRouter

from app.api import auth, oauth, defects, stream, websocket, report, telemetry, slam, floorplan, ai_webhook

api_router = APIRouter()

# 인증 / 회원가입
api_router.include_router(
    auth.router,
    prefix="/auth",
    tags=["Auth"],
)

# OAuth 소셜 로그인 (Google / Kakao / Naver)
api_router.include_router(
    oauth.router,
    prefix="/oauth",
    tags=["OAuth"],
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

# LLM 하자 점검 보고서 생성/저장/조회/다운로드
api_router.include_router(
    report.router,
    prefix="/report",
    tags=["Report"],
)

# 드론 텔레메트리 (좌표/센서/배터리)
api_router.include_router(
    telemetry.router,
    prefix="/telemetry",
    tags=["Telemetry"],
)

# SLAM 맵 데이터
api_router.include_router(
    slam.router,
    prefix="/slam",
    tags=["SLAM"],
)

# 평면도 업로드 & 처리
api_router.include_router(
    floorplan.router,
    prefix="/floorplan",
    tags=["Floorplan"],
)

# AI 서버 연동 웹훅 (탐지 이벤트 수신)
api_router.include_router(
    ai_webhook.router,
    prefix="/ai",
    tags=["AI Webhook"],
)
