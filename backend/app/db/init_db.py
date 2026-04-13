# =============================================
# app/db/init_db.py
# 역할: 애플리케이션 시작 시 DB 테이블 자동 생성
#       - Base.metadata.create_all로 존재하지 않는 테이블을 생성
#       - 프로덕션에서는 Alembic 마이그레이션 사용 권장
#       - 개발/테스트 환경에서 빠른 초기화용
# 호출: main.py lifespan 핸들러에서 await init_db()
# =============================================

from app.db.base import engine, Base

# ORM 모델을 Base에 등록하기 위해 모델 모듈 임포트
from app.models import defect  # noqa: F401 (임포트만으로 Base에 등록됨)


async def init_db() -> None:
    """
    비동기 방식으로 모든 테이블 생성.
    테이블이 이미 존재하면 건너뜀 (checkfirst=True 기본 동작).
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
