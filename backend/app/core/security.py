# =============================================
# app/core/security.py
# 역할: 비밀번호 해싱 및 검증 유틸리티
#       - bcrypt 기반 단방향 해시 (passlib CryptContext 사용)
#       - 향후 argon2 등 알고리즘 교체 시 CryptContext 정책만 수정
# 사용: from app.core.security import hash_password, verify_password
# =============================================

from passlib.context import CryptContext

# ── 해싱 정책 ─────────────────────────────────
# schemes=["bcrypt"]: 기본 bcrypt (적당한 work factor)
# deprecated="auto": 추후 새 알고리즘 도입 시 기존 해시를 자동으로 "deprecated" 로 표기
#                    → 로그인 성공 시 재해싱 트리거 가능 (needs_update())
_pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
)


def hash_password(plain_password: str) -> str:
    """
    평문 비밀번호를 bcrypt 해시 문자열로 변환.
    결과 길이: 60자 (2a$nn$saltsalthash...)
    """
    return _pwd_context.hash(plain_password)


def verify_password(plain_password: str, password_hash: str) -> bool:
    """
    사용자 입력 평문과 저장된 해시를 비교.
    상수 시간 비교로 타이밍 공격 방지 (passlib 내부 처리).
    """
    return _pwd_context.verify(plain_password, password_hash)


def needs_rehash(password_hash: str) -> bool:
    """
    저장된 해시가 현재 정책 대비 구버전(algo 변경 또는 rounds 증가)이면 True.
    로그인 성공 시 호출해 True 면 새 해시로 갱신하는 패턴으로 사용.
    """
    return _pwd_context.needs_update(password_hash)
