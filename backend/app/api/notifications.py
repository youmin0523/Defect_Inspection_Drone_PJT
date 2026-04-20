# =============================================
# app/api/notifications.py
# 역할: 알림 REST API 엔드포인트
#       - GET    /notifications              → 목록 조회 (필터, 페이지네이션)
#       - GET    /notifications/unread-count  → 미읽음 수
#       - PATCH  /notifications/{id}/read     → 단건 읽음 처리
#       - PATCH  /notifications/read-all      → 전체 읽음 처리
#       - DELETE /notifications/{id}          → 삭제
# =============================================

from uuid import UUID
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db, get_current_user
from app.models.notification import Notification
from app.schemas.notification import (
    NotificationResponse,
    NotificationListResponse,
    NotificationUnreadCount,
)

router = APIRouter()


@router.get("", response_model=NotificationListResponse)
async def list_notifications(
    category: Optional[str] = Query(None, description="카테고리 필터"),
    is_read: Optional[bool] = Query(None, description="읽음 상태 필터"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    현재 사용자의 알림 목록 조회.
    카테고리·읽음 상태 필터 + 페이지네이션 지원.
    """
    base = select(Notification).where(Notification.user_id == current_user.id)
    count_q = select(func.count(Notification.id)).where(Notification.user_id == current_user.id)

    if category is not None:
        base = base.where(Notification.category == category)
        count_q = count_q.where(Notification.category == category)
    if is_read is not None:
        base = base.where(Notification.is_read == is_read)
        count_q = count_q.where(Notification.is_read == is_read)

    total = await db.scalar(count_q)

    result = await db.execute(
        base.order_by(Notification.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    items = [NotificationResponse.model_validate(r) for r in result.scalars().all()]

    return NotificationListResponse(items=items, total=total, limit=limit, offset=offset)


@router.get("/unread-count", response_model=NotificationUnreadCount)
async def get_unread_count(
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """현재 사용자의 미읽음 알림 수 반환"""
    count = await db.scalar(
        select(func.count(Notification.id))
        .where(Notification.user_id == current_user.id)
        .where(Notification.is_read == False)  # noqa: E712
    )
    return NotificationUnreadCount(count=count or 0)


@router.patch("/{notification_id}/read", response_model=NotificationResponse)
async def mark_as_read(
    notification_id: UUID,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """단건 알림 읽음 처리"""
    result = await db.execute(
        select(Notification)
        .where(Notification.id == notification_id)
        .where(Notification.user_id == current_user.id)
    )
    notif = result.scalar_one_or_none()
    if notif is None:
        raise HTTPException(status_code=404, detail="알림을 찾을 수 없습니다.")

    notif.is_read = True
    await db.flush()
    return NotificationResponse.model_validate(notif)


@router.patch("/read-all")
async def mark_all_as_read(
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """현재 사용자의 미읽음 알림 전체 읽음 처리"""
    result = await db.execute(
        update(Notification)
        .where(Notification.user_id == current_user.id)
        .where(Notification.is_read == False)  # noqa: E712
        .values(is_read=True)
    )
    return {"updated": result.rowcount}


@router.delete("/{notification_id}", status_code=204)
async def delete_notification(
    notification_id: UUID,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """단건 알림 삭제"""
    result = await db.execute(
        select(Notification)
        .where(Notification.id == notification_id)
        .where(Notification.user_id == current_user.id)
    )
    notif = result.scalar_one_or_none()
    if notif is None:
        raise HTTPException(status_code=404, detail="알림을 찾을 수 없습니다.")

    await db.delete(notif)
    await db.flush()
