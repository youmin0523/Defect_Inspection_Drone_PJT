# =============================================
# app/api/chat.py
# 역할: 사내 메신저 REST API 엔드포인트
#       - GET    /chat/conversations                   → 대화방 목록
#       - POST   /chat/conversations                   → 새 대화방 생성
#       - GET    /chat/conversations/{id}/messages      → 메시지 목록
#       - POST   /chat/conversations/{id}/messages      → 메시지 전송 + WS broadcast
#       - PATCH  /chat/conversations/{id}/read          → 읽음 처리
#       - GET    /chat/unread-counts                    → 미읽음 카운트
# =============================================

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db, get_current_user, get_current_org_member, get_ws_manager
from app.models.conversation import Conversation
from app.models.message import Message
from app.models.conversation_member import ConversationMember
from app.models.user import User
from app.schemas.chat import (
    ConversationCreate,
    ConversationResponse,
    ConversationListResponse,
    MessageCreate,
    MessageResponse,
    MessageListResponse,
    MemberBrief,
    LastMessageBrief,
    UnreadCountResponse,
)
from app.core.ws_manager import ConnectionManager

router = APIRouter()


# ── 헬퍼: 대화방 응답 빌드 ──────────────────
async def _build_conv_response(db: AsyncSession, conv: Conversation) -> ConversationResponse:
    # 참여자 조회
    members_q = await db.execute(
        select(ConversationMember.user_id, User.name)
        .join(User, User.id == ConversationMember.user_id)
        .where(ConversationMember.conversation_id == conv.id)
    )
    participants = [
        MemberBrief(user_id=row[0], name=row[1], initials=row[1][:2].upper() if row[1] else "??")
        for row in members_q
    ]

    # 마지막 메시지
    last_msg_q = await db.execute(
        select(Message, User.name)
        .join(User, User.id == Message.sender_id)
        .where(Message.conversation_id == conv.id)
        .order_by(desc(Message.created_at))
        .limit(1)
    )
    last_row = last_msg_q.first()
    last_message = None
    if last_row:
        last_message = LastMessageBrief(
            text=last_row[0].text,
            sender_name=last_row[1],
            created_at=last_row[0].created_at,
        )

    return ConversationResponse(
        id=conv.id,
        type=conv.type,
        name=conv.name,
        participants=participants,
        created_at=conv.created_at,
        updated_at=conv.updated_at,
        last_message=last_message,
    )


@router.get("/conversations", response_model=ConversationListResponse)
async def list_conversations(
    org_tuple=Depends(get_current_org_member),
    db: AsyncSession = Depends(get_db),
):
    """현재 사용자의 대화방 목록 조회 (소속 조직 한정)"""
    user, member, org = org_tuple
    conv_ids_q = await db.execute(
        select(ConversationMember.conversation_id)
        .where(ConversationMember.user_id == user.id)
    )
    conv_ids = [row[0] for row in conv_ids_q]

    if not conv_ids:
        return ConversationListResponse(items=[], total=0)

    convs_q = await db.execute(
        select(Conversation)
        .where(Conversation.id.in_(conv_ids))
        .where(Conversation.organization_id == org.id)
        .order_by(desc(Conversation.updated_at))
    )
    convs = convs_q.scalars().all()

    items = []
    for conv in convs:
        items.append(await _build_conv_response(db, conv))

    return ConversationListResponse(items=items, total=len(items))


@router.post("/conversations", response_model=ConversationResponse, status_code=201)
async def create_conversation(
    payload: ConversationCreate,
    org_tuple=Depends(get_current_org_member),
    db: AsyncSession = Depends(get_db),
):
    """새 대화방 생성 (소속 조직에 자동 배정, 참여자 같은 조직 검증)"""
    user, member, org = org_tuple
    from app.models.organization import OrganizationMember
    # 참여자가 같은 조직인지 검증
    for pid in payload.participant_ids:
        if pid == user.id:
            continue
        exists = await db.scalar(
            select(OrganizationMember.id).where(
                OrganizationMember.organization_id == org.id,
                OrganizationMember.user_id == pid,
                OrganizationMember.status == "active",
            )
        )
        if not exists:
            raise HTTPException(status_code=400, detail=f"참여자 {pid}는 같은 조직에 소속되어 있지 않습니다.")

    conv = Conversation(
        type=payload.type,
        name=payload.name,
        created_by=user.id,
        organization_id=org.id,
    )
    db.add(conv)
    await db.flush()

    # 참여자 추가 (생성자 포함)
    all_ids = set(payload.participant_ids) | {user.id}
    for uid in all_ids:
        db.add(ConversationMember(conversation_id=conv.id, user_id=uid))
    await db.flush()

    return await _build_conv_response(db, conv)


@router.get("/conversations/{conversation_id}/messages", response_model=MessageListResponse)
async def get_messages(
    conversation_id: UUID,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """대화방 메시지 목록 조회"""
    # 참여자 확인
    member = await db.scalar(
        select(ConversationMember.id)
        .where(ConversationMember.conversation_id == conversation_id)
        .where(ConversationMember.user_id == current_user.id)
    )
    if member is None:
        raise HTTPException(status_code=403, detail="이 대화방에 참여하고 있지 않습니다.")

    total = await db.scalar(
        select(func.count(Message.id))
        .where(Message.conversation_id == conversation_id)
    )

    msgs_q = await db.execute(
        select(Message, User.name)
        .join(User, User.id == Message.sender_id)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at)
        .limit(limit)
        .offset(offset)
    )

    items = [
        MessageResponse(
            id=row[0].id,
            conversation_id=row[0].conversation_id,
            sender_id=row[0].sender_id,
            sender_name=row[1],
            sender_initials=row[1][:2].upper() if row[1] else "??",
            text=row[0].text,
            created_at=row[0].created_at,
        )
        for row in msgs_q
    ]

    return MessageListResponse(items=items, total=total, has_more=(offset + limit) < total)


@router.post("/conversations/{conversation_id}/messages", response_model=MessageResponse, status_code=201)
async def send_message(
    conversation_id: UUID,
    payload: MessageCreate,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    ws_manager: ConnectionManager = Depends(get_ws_manager),
):
    """메시지 전송 + WebSocket 브로드캐스트"""
    # 참여자 확인
    member = await db.scalar(
        select(ConversationMember.id)
        .where(ConversationMember.conversation_id == conversation_id)
        .where(ConversationMember.user_id == current_user.id)
    )
    if member is None:
        raise HTTPException(status_code=403, detail="이 대화방에 참여하고 있지 않습니다.")

    msg = Message(
        conversation_id=conversation_id,
        sender_id=current_user.id,
        text=payload.text,
    )
    db.add(msg)

    # 대화방 updated_at 갱신
    conv = await db.get(Conversation, conversation_id)
    if conv:
        conv.updated_at = func.now()

    await db.flush()

    response = MessageResponse(
        id=msg.id,
        conversation_id=msg.conversation_id,
        sender_id=msg.sender_id,
        sender_name=current_user.name,
        sender_initials=current_user.name[:2].upper() if current_user.name else "??",
        text=msg.text,
        created_at=msg.created_at,
    )

    # WebSocket 브로드캐스트
    await ws_manager.broadcast(f"chat:{conversation_id}", {
        "type": "chat.new_message",
        "data": response.model_dump(mode="json"),
    })

    return response


@router.patch("/conversations/{conversation_id}/read")
async def mark_read(
    conversation_id: UUID,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """대화방 읽음 처리 (last_read_at 갱신)"""
    result = await db.execute(
        select(ConversationMember)
        .where(ConversationMember.conversation_id == conversation_id)
        .where(ConversationMember.user_id == current_user.id)
    )
    member = result.scalar_one_or_none()
    if member is None:
        raise HTTPException(status_code=403, detail="이 대화방에 참여하고 있지 않습니다.")

    member.last_read_at = func.now()
    await db.flush()
    return {"ok": True}


@router.get("/unread-counts", response_model=UnreadCountResponse)
async def get_unread_counts(
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """전체 미읽음 카운트 조회"""
    members_q = await db.execute(
        select(ConversationMember)
        .where(ConversationMember.user_id == current_user.id)
    )
    members = members_q.scalars().all()

    per_conversation = {}
    total = 0

    for m in members:
        base = select(func.count(Message.id)).where(
            Message.conversation_id == m.conversation_id,
            Message.sender_id != current_user.id,
        )
        if m.last_read_at:
            base = base.where(Message.created_at > m.last_read_at)

        count = await db.scalar(base) or 0
        if count > 0:
            per_conversation[str(m.conversation_id)] = count
            total += count

    return UnreadCountResponse(total=total, per_conversation=per_conversation)
