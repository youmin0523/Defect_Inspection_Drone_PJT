# =============================================
# app/api/organization.py
# 역할: 조직(회사) 관리 REST API
#       - GET    /organizations/my          → 내 조직 정보
#       - GET    /organizations/members     → 같은 조직 멤버 목록 (채팅 팀원 목록)
#       - POST   /organizations             → 조직 생성 (B2B 자동 매칭 or 수동)
#       - POST   /organizations/members/invite → 멤버 초대
#       - PATCH  /organizations/members/{user_id} → 멤버 정보 수정
#       - DELETE /organizations/members/{user_id} → 멤버 제거
#
# 설계:
#   - biz_number 자동 매칭: 회원가입 시 B2B 사업자등록번호가 기존 Organization 과
#     일치하면 자동으로 OrganizationMember 생성 (auth.py 회원가입 로직에서 호출)
#   - 관리자 초대: admin/owner 가 이메일로 초대 → invited 상태로 멤버 생성
# =============================================

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db, get_current_user
from app.models.organization import Organization, OrganizationMember
from app.models.user import User
from app.schemas.organization import (
    OrganizationCreate,
    OrganizationResponse,
    OrgMemberResponse,
    OrgMemberListResponse,
    InviteMemberRequest,
    UpdateMemberRequest,
)

router = APIRouter()


# ── 헬퍼: 현재 사용자의 조직 조회 ─────────────
async def _get_user_org(db: AsyncSession, user_id: UUID):
    """현재 사용자가 소속된 Organization + OrganizationMember 반환"""
    result = await db.execute(
        select(OrganizationMember, Organization)
        .join(Organization, Organization.id == OrganizationMember.organization_id)
        .where(OrganizationMember.user_id == user_id)
        .where(OrganizationMember.status == "active")
    )
    row = result.first()
    if not row:
        return None, None
    return row[0], row[1]  # member, org


@router.get("/my", response_model=OrganizationResponse)
async def get_my_organization(
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """현재 사용자의 소속 조직 정보 조회"""
    member, org = await _get_user_org(db, current_user.id)
    if not org:
        raise HTTPException(status_code=404, detail="소속된 조직이 없습니다.")

    count = await db.scalar(
        select(func.count(OrganizationMember.id))
        .where(OrganizationMember.organization_id == org.id)
        .where(OrganizationMember.status == "active")
    )

    return OrganizationResponse(
        id=org.id, name=org.name, biz_number=org.biz_number,
        member_count=count, created_at=org.created_at,
    )


@router.get("/members", response_model=OrgMemberListResponse)
async def list_organization_members(
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    같은 조직의 멤버 목록 조회 — 메신저 '새 대화' 팀원 목록에서 사용.
    active + invited 상태 멤버 모두 반환.
    """
    member, org = await _get_user_org(db, current_user.id)
    if not org:
        raise HTTPException(status_code=404, detail="소속된 조직이 없습니다.")

    result = await db.execute(
        select(OrganizationMember, User)
        .join(User, User.id == OrganizationMember.user_id)
        .where(OrganizationMember.organization_id == org.id)
        .where(OrganizationMember.status.in_(["active", "invited"]))
        .order_by(OrganizationMember.role, User.name)
    )

    members = []
    for om, user in result:
        members.append(OrgMemberResponse(
            user_id=user.id,
            name=user.name,
            email=user.email,
            initials=user.name[:2].upper() if user.name else "??",
            role=om.role,
            department=om.department,
            position=om.position,
            status=om.status,
        ))

    active_count = sum(1 for m in members if m.status == "active")

    return OrgMemberListResponse(
        organization=OrganizationResponse(
            id=org.id, name=org.name, biz_number=org.biz_number,
            member_count=active_count, created_at=org.created_at,
        ),
        members=members,
        total=len(members),
    )


@router.post("", response_model=OrganizationResponse, status_code=201)
async def create_organization(
    payload: OrganizationCreate,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    조직 생성.
    biz_number 가 이미 존재하면 409 Conflict (기존 조직에 가입 유도).
    생성자는 자동으로 owner 권한 부여.
    """
    # 사업자등록번호 중복 체크
    if payload.biz_number:
        existing = await db.scalar(
            select(Organization.id).where(Organization.biz_number == payload.biz_number)
        )
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="해당 사업자등록번호로 등록된 조직이 이미 존재합니다.",
            )

    org = Organization(name=payload.name, biz_number=payload.biz_number)
    db.add(org)
    await db.flush()

    # 생성자를 owner 로 등록
    db.add(OrganizationMember(
        organization_id=org.id,
        user_id=current_user.id,
        role="owner",
        status="active",
    ))
    await db.flush()

    return OrganizationResponse(
        id=org.id, name=org.name, biz_number=org.biz_number,
        member_count=1, created_at=org.created_at,
    )


@router.post("/members/invite", response_model=OrgMemberResponse, status_code=201)
async def invite_member(
    payload: InviteMemberRequest,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    멤버 초대 (admin/owner 전용).
    이메일로 사용자를 찾아 invited 상태로 조직에 추가.
    """
    # 권한 확인
    my_member, org = await _get_user_org(db, current_user.id)
    if not org:
        raise HTTPException(status_code=404, detail="소속된 조직이 없습니다.")
    if my_member.role not in ("owner", "admin"):
        raise HTTPException(status_code=403, detail="멤버 초대 권한이 없습니다. (admin 이상)")

    # 초대할 사용자 찾기
    target_user = await db.scalar(select(User).where(User.email == payload.email))
    if not target_user:
        raise HTTPException(status_code=404, detail="해당 이메일의 사용자를 찾을 수 없습니다.")

    # 이미 소속 여부 확인
    existing = await db.scalar(
        select(OrganizationMember.id)
        .where(OrganizationMember.organization_id == org.id)
        .where(OrganizationMember.user_id == target_user.id)
    )
    if existing:
        raise HTTPException(status_code=409, detail="이미 조직에 소속된 사용자입니다.")

    new_member = OrganizationMember(
        organization_id=org.id,
        user_id=target_user.id,
        role=payload.role,
        department=payload.department,
        position=payload.position,
        status="invited",
    )
    db.add(new_member)
    await db.flush()

    return OrgMemberResponse(
        user_id=target_user.id,
        name=target_user.name,
        email=target_user.email,
        initials=target_user.name[:2].upper() if target_user.name else "??",
        role=new_member.role,
        department=new_member.department,
        position=new_member.position,
        status=new_member.status,
    )


@router.patch("/members/{user_id}", response_model=OrgMemberResponse)
async def update_member(
    user_id: UUID,
    payload: UpdateMemberRequest,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """멤버 부서/직위/권한/상태 수정 (admin/owner 전용)"""
    my_member, org = await _get_user_org(db, current_user.id)
    if not org:
        raise HTTPException(status_code=404, detail="소속된 조직이 없습니다.")
    if my_member.role not in ("owner", "admin"):
        raise HTTPException(status_code=403, detail="수정 권한이 없습니다.")

    result = await db.execute(
        select(OrganizationMember, User)
        .join(User, User.id == OrganizationMember.user_id)
        .where(OrganizationMember.organization_id == org.id)
        .where(OrganizationMember.user_id == user_id)
    )
    row = result.first()
    if not row:
        raise HTTPException(status_code=404, detail="해당 멤버를 찾을 수 없습니다.")

    target_member, target_user = row
    if payload.role is not None:
        target_member.role = payload.role
    if payload.department is not None:
        target_member.department = payload.department
    if payload.position is not None:
        target_member.position = payload.position
    if payload.status is not None:
        target_member.status = payload.status
    await db.flush()

    return OrgMemberResponse(
        user_id=target_user.id,
        name=target_user.name,
        email=target_user.email,
        initials=target_user.name[:2].upper() if target_user.name else "??",
        role=target_member.role,
        department=target_member.department,
        position=target_member.position,
        status=target_member.status,
    )


@router.delete("/members/{user_id}", status_code=204)
async def remove_member(
    user_id: UUID,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """멤버 제거 (admin/owner 전용, owner 자신은 제거 불가)"""
    my_member, org = await _get_user_org(db, current_user.id)
    if not org:
        raise HTTPException(status_code=404, detail="소속된 조직이 없습니다.")
    if my_member.role not in ("owner", "admin"):
        raise HTTPException(status_code=403, detail="멤버 제거 권한이 없습니다.")

    result = await db.execute(
        select(OrganizationMember)
        .where(OrganizationMember.organization_id == org.id)
        .where(OrganizationMember.user_id == user_id)
    )
    target = result.scalar_one_or_none()
    if not target:
        raise HTTPException(status_code=404, detail="해당 멤버를 찾을 수 없습니다.")
    if target.role == "owner":
        raise HTTPException(status_code=400, detail="조직 소유자는 제거할 수 없습니다.")

    await db.delete(target)
    await db.flush()
