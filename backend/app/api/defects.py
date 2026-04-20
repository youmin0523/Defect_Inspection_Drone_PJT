# =============================================
# app/api/defects.py
# 역할: 하자 탐지 로그 REST CRUD API 엔드포인트
#       - GET  /defects        → 목록 조회 (필터링, 페이지네이션)
#       - GET  /defects/{id}   → 단건 조회
#       - POST /defects        → 신규 하자 저장 + WS 브로드캐스트
#       - GET  /defects/summary → 대시보드용 요약 통계
#       - DELETE /defects/{id} → 하자 삭제
# =============================================

from uuid import UUID
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db, get_ws_manager
from app.models.defect import DefectLog
from app.schemas.defect import (
    DefectLogCreate,
    DefectLogResponse,
    DefectLogListResponse,
    DefectSummary,
)
from app.core.ws_manager import ConnectionManager

router = APIRouter()


@router.get("/summary", response_model=DefectSummary)
async def get_defect_summary(db: AsyncSession = Depends(get_db)):
    """
    대시보드용 하자 요약 통계 반환.
    전체 건수, 심각도별 건수, 영역별 건수, 최신 탐지 결과.
    """
    total = await db.scalar(select(func.count(DefectLog.id)))

    # 심각도별 카운트
    severity_rows = await db.execute(
        select(DefectLog.severity, func.count(DefectLog.id))
        .group_by(DefectLog.severity)
    )
    by_severity = {row[0]: row[1] for row in severity_rows}

    # 영역별 카운트
    area_rows = await db.execute(
        select(DefectLog.area, func.count(DefectLog.id))
        .group_by(DefectLog.area)
    )
    by_area = {row[0]: row[1] for row in area_rows}

    # 최신 탐지 결과
    latest_result = await db.execute(
        select(DefectLog).order_by(desc(DefectLog.timestamp)).limit(1)
    )
    latest = latest_result.scalar_one_or_none()

    return DefectSummary(
        total=total or 0,
        by_severity=by_severity,
        by_area=by_area,
        latest=DefectLogResponse.model_validate(latest) if latest else None,
    )


@router.get("/recent", response_model=DefectLogListResponse)
async def list_recent_defects(
    severity: Optional[str] = Query(None, description="심각도 필터 (HIGH/MED/LOW)"),
    limit: int = Query(50, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
):
    """
    최신순 하자 로그 N건 조회.
    실시간 대시보드용 — severity 단일 필터만 지원하는 경량 엔드포인트.
    """
    query = select(DefectLog).order_by(desc(DefectLog.timestamp))
    if severity:
        query = query.where(DefectLog.severity == severity.upper())
    query = query.limit(limit)
    result = await db.execute(query)
    items = result.scalars().all()
    return DefectLogListResponse(
        items=[DefectLogResponse.model_validate(item) for item in items],
        total=len(items),
        limit=limit,
        offset=0,
    )


@router.get("", response_model=DefectLogListResponse)
async def list_defects(
    area: Optional[str] = Query(None, description="영역 코드 (A-E)"),
    severity: Optional[str] = Query(None, description="심각도 (HIGH/MED/LOW)"),
    category_code: Optional[str] = Query(None, description="카테고리 코드 (예: A-01)"),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """하자 탐지 로그 목록 조회 (필터링 + 페이지네이션)"""
    query = select(DefectLog)

    if area:
        query = query.where(DefectLog.area == area.upper())
    if severity:
        query = query.where(DefectLog.severity == severity.upper())
    if category_code:
        query = query.where(DefectLog.category_code == category_code)

    # 최신 순 정렬
    query = query.order_by(desc(DefectLog.timestamp))

    # 전체 건수
    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query)

    # 페이지네이션
    result = await db.execute(query.offset(offset).limit(limit))
    items = result.scalars().all()

    return DefectLogListResponse(
        items=[DefectLogResponse.model_validate(item) for item in items],
        total=total or 0,
        limit=limit,
        offset=offset,
    )


@router.get("/{defect_id}", response_model=DefectLogResponse)
async def get_defect(defect_id: UUID, db: AsyncSession = Depends(get_db)):
    """하자 탐지 로그 단건 조회"""
    result = await db.execute(
        select(DefectLog).where(DefectLog.id == defect_id)
    )
    defect = result.scalar_one_or_none()
    if not defect:
        raise HTTPException(status_code=404, detail="하자 탐지 기록을 찾을 수 없습니다.")
    return DefectLogResponse.model_validate(defect)


@router.post("", response_model=DefectLogResponse, status_code=201)
async def create_defect(
    payload: DefectLogCreate,
    db: AsyncSession = Depends(get_db),
    manager: ConnectionManager = Depends(get_ws_manager),
):
    """
    새 하자 탐지 결과 저장 후 WebSocket으로 실시간 브로드캐스트.
    AI 파이프라인(defect_processor.py)에서 탐지 시 호출.
    """
    defect = DefectLog(
        area=payload.area.upper() if payload.area else None,
        category_code=payload.category_code,
        defect_type=payload.defect_type,
        severity=payload.severity.upper(),
        confidence=payload.confidence,
        defect_source=payload.defect_source,
        defect_class=payload.defect_class,
        defect_class_display_en=payload.defect_class_display_en,
        defect_class_display_ko=payload.defect_class_display_ko,
        bbox_x=payload.bbox.x if payload.bbox else None,
        bbox_y=payload.bbox.y if payload.bbox else None,
        bbox_w=payload.bbox.w if payload.bbox else None,
        bbox_h=payload.bbox.h if payload.bbox else None,
        lidar_x=payload.lidar_position.x if payload.lidar_position else None,
        lidar_y=payload.lidar_position.y if payload.lidar_position else None,
        lidar_z=payload.lidar_position.z if payload.lidar_position else None,
        image_crop=payload.image_crop,
        thermal_max=payload.thermal_data.max if payload.thermal_data else None,
        thermal_min=payload.thermal_data.min if payload.thermal_data else None,
        thermal_avg=payload.thermal_data.avg if payload.thermal_data else None,
        frame_id=payload.frame_id,
        raw_payload=payload.raw_payload,
    )

    db.add(defect)
    await db.flush()  # ID 생성을 위해 flush (commit은 get_db에서)

    response = DefectLogResponse.model_validate(defect)

    # WS "defects" 채널에 실시간 브로드캐스트
    await manager.broadcast("defects", {
        "type": "defect.new",
        "data": response.model_dump(mode="json"),
    })

    return response


@router.delete("/{defect_id}", status_code=204)
async def delete_defect(defect_id: UUID, db: AsyncSession = Depends(get_db)):
    """하자 탐지 기록 삭제"""
    result = await db.execute(
        select(DefectLog).where(DefectLog.id == defect_id)
    )
    defect = result.scalar_one_or_none()
    if not defect:
        raise HTTPException(status_code=404, detail="하자 탐지 기록을 찾을 수 없습니다.")
    await db.delete(defect)
