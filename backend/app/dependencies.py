# =============================================
# app/dependencies.py
# 역할: FastAPI 공유 의존성(Depends) 팩토리 모음
#       - DB 세션, 서비스 싱글톤을 라우터에 주입하는 함수 제공
#       - 모든 라우터에서 동일한 인스턴스를 재사용하도록 보장
# 사용: router 함수 파라미터에 Depends(get_db) 등으로 주입
# =============================================

from typing import AsyncGenerator
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import async_session_factory
from app.core.jwt import decode_access_token
from app.core.ws_manager import ws_manager
from app.services.camera import rgb_camera_service, thermal_camera_service
from app.services.recording import recording_service
from app.services.yolo_inference import yolo_service

_bearer_scheme = HTTPBearer(auto_error=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    비동기 DB 세션 의존성.
    요청마다 새 세션을 생성하고, 응답 후 자동으로 닫는다.
    """
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def get_current_user(
    cred: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
    db: AsyncSession = Depends(get_db),
):
    """
    Bearer 토큰에서 현재 사용자를 추출하는 인증 의존성.
    보호가 필요한 라우터에 Depends(get_current_user)로 주입.
    """
    if cred is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="인증 토큰이 필요합니다.")

    user_id = decode_access_token(cred.credentials)
    if user_id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="유효하지 않거나 만료된 토큰입니다.")

    from app.models.user import User  # 순환 임포트 방지
    result = await db.execute(select(User).where(User.id == UUID(user_id)))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="사용자를 찾을 수 없습니다.")
    return user


def get_ws_manager():
    """WebSocket 연결 매니저 싱글톤 반환"""
    return ws_manager


def get_rgb_camera():
    """RGB 카메라 서비스 싱글톤 반환"""
    return rgb_camera_service


def get_thermal_camera():
    """열화상 카메라 서비스 싱글톤 반환"""
    return thermal_camera_service


def get_recording_service():
    """녹화 서비스 싱글톤 반환"""
    return recording_service


def get_yolo_service():
    """YOLOv8 추론 서비스 싱글톤 반환"""
    return yolo_service
