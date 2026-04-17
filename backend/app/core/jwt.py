# =============================================
# app/core/jwt.py
# 역할: JWT 액세스 토큰 생성 및 검증
#       - python-jose 기반 HS256 서명
#       - settings.JWT_SECRET으로 서명/검증
# 사용: from app.core.jwt import create_access_token, decode_access_token
# =============================================

from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt

from app.config import settings

ALGORITHM = "HS256"


def create_access_token(user_id: str, expires_minutes: int = None) -> str:
    """
    사용자 UUID를 sub 클레임에 담은 JWT 액세스 토큰 발급.
    """
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=expires_minutes or settings.JWT_EXPIRE_MINUTES
    )
    payload = {"sub": str(user_id), "exp": expire}
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=ALGORITHM)


def decode_access_token(token: str) -> str | None:
    """
    JWT 토큰을 검증하고 sub(user_id) 반환.
    만료·변조 시 None 반환.
    """
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[ALGORITHM])
        return payload.get("sub")
    except JWTError:
        return None
