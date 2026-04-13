# =============================================
# app/dependencies.py
# 역할: FastAPI 공유 의존성(Depends) 팩토리 모음
#       - DB 세션, 서비스 싱글톤을 라우터에 주입하는 함수 제공
#       - 모든 라우터에서 동일한 인스턴스를 재사용하도록 보장
# 사용: router 함수 파라미터에 Depends(get_db) 등으로 주입
# =============================================

from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import async_session_factory
from app.core.ws_manager import ws_manager
from app.services.camera import rgb_camera_service, thermal_camera_service
from app.services.yolo_inference import yolo_service


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


def get_ws_manager():
    """WebSocket 연결 매니저 싱글톤 반환"""
    return ws_manager


def get_rgb_camera():
    """RGB 카메라 서비스 싱글톤 반환"""
    return rgb_camera_service


def get_thermal_camera():
    """열화상 카메라 서비스 싱글톤 반환"""
    return thermal_camera_service


def get_yolo_service():
    """YOLOv8 추론 서비스 싱글톤 반환"""
    return yolo_service
