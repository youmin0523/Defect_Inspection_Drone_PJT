# =============================================
# app/schemas/organization.py
# 역할: 조직(회사) 관련 Pydantic 스키마
#       - OrganizationCreate: 조직 생성 요청
#       - OrganizationResponse: 조직 정보 응답
#       - OrgMemberResponse: 조직 멤버 정보 응답 (채팅 팀원 목록용)
#       - InviteMemberRequest: 멤버 초대 요청
# =============================================

from datetime import datetime
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel, Field


# ── 조직 ──────────────────────────────────────
class OrganizationCreate(BaseModel):
    """조직 생성 요청"""
    name: str = Field(..., max_length=200, description="회사/조직명")
    biz_number: Optional[str] = Field(None, max_length=10, description="사업자등록번호 (10자리)")


class OrganizationResponse(BaseModel):
    """조직 정보 응답"""
    id: UUID
    name: str
    biz_number: Optional[str]
    member_count: int = 0
    created_at: datetime

    class Config:
        from_attributes = True


# ── 조직 멤버 ────────────────────────────────
class OrgMemberResponse(BaseModel):
    """
    조직 멤버 정보 응답 — 메신저 팀원 목록에서 사용.
    User 정보 + 조직 내 부서/직위/권한 결합.
    """
    user_id: UUID
    name: str
    email: str
    initials: str
    role: str             # owner / admin / member
    department: Optional[str]
    position: Optional[str]
    status: str           # active / invited / deactivated

    class Config:
        from_attributes = True


class OrgMemberListResponse(BaseModel):
    """조직 멤버 목록 응답"""
    organization: OrganizationResponse
    members: List[OrgMemberResponse]
    total: int


# ── 멤버 초대 ────────────────────────────────
class InviteMemberRequest(BaseModel):
    """멤버 초대 요청"""
    email: str = Field(..., description="초대할 사용자 이메일")
    role: str = Field("member", pattern="^(admin|member)$")
    department: Optional[str] = None
    position: Optional[str] = None


# ── 멤버 정보 수정 ───────────────────────────
class UpdateMemberRequest(BaseModel):
    """멤버 부서/직위/권한 수정"""
    role: Optional[str] = Field(None, pattern="^(admin|member)$")
    department: Optional[str] = None
    position: Optional[str] = None
    status: Optional[str] = Field(None, pattern="^(active|deactivated)$")
