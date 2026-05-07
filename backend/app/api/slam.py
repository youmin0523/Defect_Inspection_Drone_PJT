# =============================================
# app/api/slam.py
# 역할: SLAM 맵 데이터 API
#       - POST   /slam          → 새 맵 세션 생성
#       - GET    /slam          → 맵 목록 조회 (메타데이터만)
#       - GET    /slam/{id}     → 맵 상세 조회 (이미지 포함)
#       - PATCH  /slam/{id}     → 맵 업데이트 (실시간 매핑 중 갱신)
#       - DELETE /slam/{id}     → 맵 삭제
# =============================================

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user, get_db, get_ws_manager
from app.models.slam_map import SlamMap
from app.models.slam_pointcloud import SlamPointcloud
from app.schemas.slam_map import (
    SlamMapCreate,
    SlamMapUpdate,
    SlamMapResponse,
    SlamMapMetaResponse,
    SlamMapListResponse,
)
from app.core.ws_manager import ConnectionManager

router = APIRouter()


@router.get("", response_model=SlamMapListResponse)
async def list_slam_maps(
    db: AsyncSession = Depends(get_db),
    _user=Depends(get_current_user),  # TODO: 조직별 SLAM 분리 시 get_current_org_member로 교체
):
    """SLAM 맵 목록 조회 (이미지 제외, 메타데이터만)"""
    query = select(SlamMap).order_by(desc(SlamMap.created_at))

    total = await db.scalar(select(func.count()).select_from(SlamMap))
    result = await db.execute(query)
    items = result.scalars().all()

    return SlamMapListResponse(
        items=[SlamMapMetaResponse.model_validate(item) for item in items],
        total=total or 0,
    )


@router.get("/{map_id}", response_model=SlamMapResponse)
async def get_slam_map(
    map_id: UUID,
    db: AsyncSession = Depends(get_db),
    _user=Depends(get_current_user),
):
    """SLAM 맵 상세 조회 (이미지 포함)"""
    result = await db.execute(select(SlamMap).where(SlamMap.id == map_id))
    slam_map = result.scalar_one_or_none()
    if not slam_map:
        raise HTTPException(status_code=404, detail="SLAM 맵을 찾을 수 없습니다.")
    return SlamMapResponse.model_validate(slam_map)


@router.post("", response_model=SlamMapResponse, status_code=201)
async def create_slam_map(
    payload: SlamMapCreate,
    db: AsyncSession = Depends(get_db),
    manager: ConnectionManager = Depends(get_ws_manager),
    _user=Depends(get_current_user),
):
    """새 SLAM 맵 세션 생성"""
    slam_map = SlamMap(
        name=payload.name,
        resolution=payload.resolution,
        width=payload.width,
        height=payload.height,
        origin_x=payload.origin_x,
        origin_y=payload.origin_y,
        origin_yaw=payload.origin_yaw,
        map_image=payload.map_image,
        metadata_=payload.metadata_,
        status=payload.status,
    )

    db.add(slam_map)
    await db.flush()

    response = SlamMapResponse.model_validate(slam_map)

    # WS로 새 맵 생성 알림
    await manager.broadcast("telemetry", {
        "type": "slam.created",
        "data": {"id": str(slam_map.id), "name": slam_map.name},
    })

    return response


@router.patch("/{map_id}", response_model=SlamMapResponse)
async def update_slam_map(
    map_id: UUID,
    payload: SlamMapUpdate,
    db: AsyncSession = Depends(get_db),
    manager: ConnectionManager = Depends(get_ws_manager),
    _user=Depends(get_current_user),
):
    """
    SLAM 맵 업데이트 (실시간 매핑 중 지도 이미지 갱신).
    SLAM 노드에서 주기적으로 호출하여 웹 미니맵에 반영.
    """
    result = await db.execute(select(SlamMap).where(SlamMap.id == map_id))
    slam_map = result.scalar_one_or_none()
    if not slam_map:
        raise HTTPException(status_code=404, detail="SLAM 맵을 찾을 수 없습니다.")

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(slam_map, field, value)

    await db.flush()

    response = SlamMapResponse.model_validate(slam_map)

    # WS로 맵 업데이트 Push (프론트 미니맵 갱신용)
    await manager.broadcast("telemetry", {
        "type": "slam.updated",
        "data": {
            "id": str(slam_map.id),
            "status": slam_map.status,
            "width": slam_map.width,
            "height": slam_map.height,
        },
    })

    return response


@router.delete("/{map_id}", status_code=204)
async def delete_slam_map(
    map_id: UUID,
    db: AsyncSession = Depends(get_db),
    _user=Depends(get_current_user),
):
    """SLAM 맵 삭제"""
    result = await db.execute(select(SlamMap).where(SlamMap.id == map_id))
    slam_map = result.scalar_one_or_none()
    if not slam_map:
        raise HTTPException(status_code=404, detail="SLAM 맵을 찾을 수 없습니다.")
    await db.delete(slam_map)


# ── 자율비행 점군(키프레임) ──────────────────
class PointcloudPatch(BaseModel):
    """slam_runner 가 키프레임마다 호출. mission_id 단위 점군 누적."""
    mission_id: UUID
    frame_idx: int = Field(ge=0)
    file_path: str = Field(min_length=1, max_length=512)
    point_count: int = Field(ge=0)
    pose_x: Optional[float] = None
    pose_y: Optional[float] = None
    pose_z: Optional[float] = None
    pose_qw: Optional[float] = None
    pose_qx: Optional[float] = None
    pose_qy: Optional[float] = None
    pose_qz: Optional[float] = None
    slam_confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    extra: Optional[dict] = None


@router.patch("/pointcloud", status_code=201)
async def add_slam_pointcloud(
    payload: PointcloudPatch,
    db: AsyncSession = Depends(get_db),
    manager: ConnectionManager = Depends(get_ws_manager),
    _user=Depends(get_current_user),
):
    """
    Visual-Inertial SLAM 키프레임 1건 등록.
    실제 점군 데이터(PLY/PCD blob)는 file_path 가 가리키는 파일시스템에 저장.
    본 엔드포인트는 메타+pose 만 영속화 + WS broadcast(pointcloud.delta).
    """
    row = SlamPointcloud(
        mission_id=payload.mission_id,
        frame_idx=payload.frame_idx,
        file_path=payload.file_path,
        point_count=payload.point_count,
        pose_x=payload.pose_x, pose_y=payload.pose_y, pose_z=payload.pose_z,
        pose_qw=payload.pose_qw, pose_qx=payload.pose_qx,
        pose_qy=payload.pose_qy, pose_qz=payload.pose_qz,
        slam_confidence=payload.slam_confidence,
        extra=payload.extra,
    )
    db.add(row)
    try:
        await db.flush()
    except Exception:
        await db.rollback()
        raise HTTPException(
            status_code=409,
            detail="duplicate_frame_idx_or_invalid_mission",
        )

    await manager.broadcast("pointcloud.delta", {
        "mission_id": str(payload.mission_id),
        "frame_idx": payload.frame_idx,
        "point_count": payload.point_count,
        "pose": [payload.pose_x, payload.pose_y, payload.pose_z],
        "slam_confidence": payload.slam_confidence,
    })
    return {"id": str(row.id)}
