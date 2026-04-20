# =============================================
# app/api/auth.py
# 역할: 회원가입, 로그인, 계정 중복확인 엔드포인트
#       - POST /auth/signup           → 신규 회원 생성 (개인/사업자 공용)
#       - POST /auth/login            → 일반 로그인 (아이디+비밀번호 → JWT)
#       - GET  /auth/me               → 현재 로그인 사용자 조회
#       - GET  /auth/check-email      → 이메일 중복 확인
#       - GET  /auth/check-username   → 아이디 중복 확인
# =============================================

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password, verify_password
from app.core.jwt import create_access_token
from app.dependencies import get_db, get_current_user
from app.models.user import User
from app.models.business_profile import BusinessProfile
from app.models.term import Term
from app.models.user_term_agreement import UserTermAgreement
from app.schemas.user import (
    AvailabilityResponse,
    BusinessInfoResponse,
    LoginRequest,
    TokenResponse,
    UserSignupRequest,
    UserResponse,
)

router = APIRouter()


# ── 내부 헬퍼 ────────────────────────────────
async def _email_exists(db: AsyncSession, email: str) -> bool:
    result = await db.execute(select(User.id).where(User.email == email))
    return result.scalar_one_or_none() is not None


async def _username_exists(db: AsyncSession, username: str) -> bool:
    result = await db.execute(select(User.id).where(User.username == username))
    return result.scalar_one_or_none() is not None


async def _biz_number_exists(db: AsyncSession, biz_number: str) -> bool:
    result = await db.execute(
        select(BusinessProfile.user_id).where(BusinessProfile.biz_number == biz_number)
    )
    return result.scalar_one_or_none() is not None


# ── 중복 확인 ────────────────────────────────
@router.get("/check-email", response_model=AvailabilityResponse)
async def check_email(
    email: str = Query(..., description="확인할 이메일 주소"),
    db: AsyncSession = Depends(get_db),
):
    """이메일 사용 가능 여부 확인 (회원가입 버튼 옆 '중복 확인')."""
    taken = await _email_exists(db, email)
    return AvailabilityResponse(
        available=not taken,
        message="이미 사용 중인 이메일입니다." if taken else "사용 가능한 이메일입니다.",
    )


@router.get("/check-username", response_model=AvailabilityResponse)
async def check_username(
    username: str = Query(..., description="확인할 아이디"),
    db: AsyncSession = Depends(get_db),
):
    """아이디 사용 가능 여부 확인."""
    taken = await _username_exists(db, username)
    return AvailabilityResponse(
        available=not taken,
        message="이미 사용 중인 아이디입니다." if taken else "사용 가능한 아이디입니다.",
    )


# ── 회원가입 ─────────────────────────────────
@router.post(
    "/signup",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
async def signup(
    payload: UserSignupRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    신규 회원 등록.
    개인/사업자 공용 — account_type='business' 시 BusinessProfile 1:1 동시 생성.
    선택한 약관에 대해 UserTermAgreement 레코드도 함께 생성.
    """
    # ── 1) account_type 별 필수값 교차 검증 ──
    if payload.account_type == "business" and payload.business is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="사업자 회원은 business 정보(biz_number, ceo_name)가 필요합니다.",
        )

    # ── 2) 유니크 필드 사전 검증 ─────────────
    # (DB UNIQUE 제약과 이중 체크: 친절한 메시지 + 경쟁 조건 보호)
    if await _email_exists(db, payload.email):
        raise HTTPException(status_code=409, detail="이미 사용 중인 이메일입니다.")
    if await _username_exists(db, payload.username):
        raise HTTPException(status_code=409, detail="이미 사용 중인 아이디입니다.")
    if payload.business and await _biz_number_exists(db, payload.business.biz_number):
        raise HTTPException(status_code=409, detail="이미 등록된 사업자등록번호입니다.")

    # ── 3) User 레코드 생성 ──────────────────
    user = User(
        account_type=payload.account_type,
        email=payload.email,
        username=payload.username,
        password_hash=hash_password(payload.password),
        name=payload.name,
        phone=payload.phone,
    )
    db.add(user)
    await db.flush()  # user.id 확보 (자식 테이블 FK 연결용)

    # ── 4) 사업자 프로파일 (해당 시) ──────────
    if payload.business:
        db.add(
            BusinessProfile(
                user_id=user.id,
                biz_number=payload.business.biz_number,
                ceo_name=payload.business.ceo_name,
                # verified_at은 별도 진위확인 엔드포인트에서 갱신
            )
        )

    # ── 5) 약관 동의 이력 기록 ───────────────
    # 프론트의 3개 고정 체크 → DB terms.code 로 매핑
    agreement_map = {
        "service": payload.terms.service,
        "privacy": payload.terms.privacy,
        "marketing": payload.terms.marketing,
    }
    agreed_codes = [code for code, checked in agreement_map.items() if checked]

    if agreed_codes:
        term_rows = await db.execute(
            select(Term).where(Term.code.in_(agreed_codes))
        )
        for term in term_rows.scalars().all():
            db.add(
                UserTermAgreement(
                    user_id=user.id,
                    term_id=term.id,
                    version=term.version,  # 동의 당시 버전 스냅샷
                )
            )

    # ── 6) 응답 생성 ────────────────────────
    # (get_db 의존성에서 commit 수행됨)
    await db.flush()

    business_resp = None
    if payload.business:
        business_resp = BusinessInfoResponse(
            biz_number=payload.business.biz_number,
            ceo_name=payload.business.ceo_name,
            verified_at=None,
        )

    return UserResponse(
        id=user.id,
        account_type=user.account_type,
        email=user.email,
        username=user.username,
        name=user.name,
        phone=user.phone,
        created_at=user.created_at,
        business=business_resp,
    )


# ── 로그인 ──────────────────────────────────
@router.post("/login", response_model=TokenResponse)
async def login(
    payload: LoginRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    일반 로그인: 아이디 + 비밀번호 → JWT 액세스 토큰 발급.
    """
    result = await db.execute(select(User).where(User.username == payload.username))
    user = result.scalar_one_or_none()

    if user is None or user.password_hash is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="아이디 또는 비밀번호가 올바르지 않습니다.")

    if not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="아이디 또는 비밀번호가 올바르지 않습니다.")

    token = create_access_token(user.id)

    return TokenResponse(
        access_token=token,
        user=UserResponse(
            id=user.id,
            account_type=user.account_type,
            email=user.email,
            username=user.username,
            name=user.name,
            phone=user.phone,
            created_at=user.created_at,
        ),
    )


# ── 현재 사용자 조회 ────────────────────────
@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """Bearer 토큰으로 현재 로그인 사용자 정보 반환."""
    return UserResponse(
        id=current_user.id,
        account_type=current_user.account_type,
        email=current_user.email,
        username=current_user.username,
        name=current_user.name,
        phone=current_user.phone,
        created_at=current_user.created_at,
    )
