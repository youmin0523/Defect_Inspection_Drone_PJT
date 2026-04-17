# =============================================
# app/db/init_db.py
# 역할: 애플리케이션 시작 시 DB 테이블 자동 생성
#       - Base.metadata.create_all로 존재하지 않는 테이블을 생성
#       - 프로덕션에서는 Alembic 마이그레이션 사용 권장
#       - 개발/테스트 환경에서 빠른 초기화용
# 호출: main.py lifespan 핸들러에서 await init_db()
# =============================================

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import engine, Base
from app.db.session import async_session_factory

# ORM 모델을 Base에 등록하기 위해 모델 패키지 임포트
# (app/models/__init__.py 에서 모든 모델을 일괄 임포트해 메타데이터에 등록)
from app.models import (  # noqa: F401
    defect,
    user,
    business_profile,
    term,
    user_term_agreement,
)
from app.models.term import Term


# ── 약관 시드 데이터 ─────────────────────────
_TERM_SEEDS = [
    {"code": "service",   "title": "서비스 이용약관",       "is_required": True,  "version": "1.0"},
    {"code": "privacy",   "title": "개인정보 수집·이용 동의", "is_required": True,  "version": "1.0"},
    {"code": "marketing", "title": "마케팅 정보 수신 동의",  "is_required": False, "version": "1.0"},
]


async def _seed_terms(session: AsyncSession) -> None:
    """terms 테이블에 기본 약관이 없으면 삽입."""
    result = await session.execute(select(Term.code))
    existing_codes = {row[0] for row in result.all()}

    for seed in _TERM_SEEDS:
        if seed["code"] not in existing_codes:
            session.add(Term(**seed))

    await session.commit()


async def init_db() -> None:
    """
    비동기 방식으로 모든 테이블 생성 + 시드 데이터 삽입.
    테이블이 이미 존재하면 건너뜀 (checkfirst=True 기본 동작).
    """
    # 1) 테이블 생성
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # 2) 시드 데이터 (약관)
    async with async_session_factory() as session:
        await _seed_terms(session)
