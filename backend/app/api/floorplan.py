# =============================================
# app/api/floorplan.py
# 역할: 평면도 이미지 업로드 & 처리 API
#       - POST /floorplan/upload      → JPG/PDF/DXF 업로드
#       - POST /floorplan/{id}/process → OpenCV 벽체 추출 트리거
#       - GET  /floorplan             → 업로드 목록 조회
#       - GET  /floorplan/{id}        → 상세 조회 (처리 결과 포함)
#       - DELETE /floorplan/{id}      → 삭제
# =============================================

import os
import uuid as uuid_mod
from uuid import UUID

import aiofiles
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db
from app.models.floorplan import Floorplan
from app.schemas.floorplan import (
    FloorplanUploadResponse,
    FloorplanProcessResponse,
    FloorplanAnalyzeResponse,
    FloorplanListResponse,
)
from app.services.floorplan_processor import extract_walls_from_bytes

router = APIRouter()

# 업로드 저장 디렉토리
UPLOAD_DIR = "./uploads/floorplans"

ALLOWED_CONTENT_TYPES = {
    "image/jpeg",
    "image/png",
    "application/pdf",
    "application/dxf",
    "application/octet-stream",  # .dxf fallback
}


@router.get("", response_model=FloorplanListResponse)
async def list_floorplans(db: AsyncSession = Depends(get_db)):
    """업로드된 평면도 목록 조회"""
    total = await db.scalar(select(func.count()).select_from(Floorplan))
    result = await db.execute(
        select(Floorplan).order_by(desc(Floorplan.created_at))
    )
    items = result.scalars().all()

    return FloorplanListResponse(
        items=[FloorplanUploadResponse.model_validate(item) for item in items],
        total=total or 0,
    )


@router.get("/{floorplan_id}", response_model=FloorplanUploadResponse)
async def get_floorplan(floorplan_id: UUID, db: AsyncSession = Depends(get_db)):
    """평면도 상세 조회"""
    result = await db.execute(
        select(Floorplan).where(Floorplan.id == floorplan_id)
    )
    fp = result.scalar_one_or_none()
    if not fp:
        raise HTTPException(status_code=404, detail="평면도를 찾을 수 없습니다.")
    return FloorplanUploadResponse.model_validate(fp)


@router.post("/upload", response_model=FloorplanUploadResponse, status_code=201)
async def upload_floorplan(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    """
    평면도 이미지(JPG/PNG/PDF/DXF) 업로드.
    파일을 서버에 저장하고 DB에 메타데이터 기록.
    이후 /process 엔드포인트로 OpenCV 처리 트리거.
    """
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"지원하지 않는 파일 형식입니다: {file.content_type}"
        )

    # 업로드 디렉토리 생성
    os.makedirs(UPLOAD_DIR, exist_ok=True)

    # 고유 파일명 생성
    ext = os.path.splitext(file.filename or "unknown")[1]
    saved_filename = f"{uuid_mod.uuid4()}{ext}"
    file_path = os.path.join(UPLOAD_DIR, saved_filename)

    # 파일 저장
    async with aiofiles.open(file_path, "wb") as f:
        content = await file.read()
        await f.write(content)

    # DB 기록
    floorplan = Floorplan(
        filename=file.filename or "unknown",
        content_type=file.content_type,
        file_path=file_path,
        status="uploaded",
    )
    db.add(floorplan)
    await db.flush()

    return FloorplanUploadResponse.model_validate(floorplan)


@router.post("/{floorplan_id}/process", response_model=FloorplanProcessResponse)
async def process_floorplan(
    floorplan_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    업로드된 평면도에서 벽체 라인 추출 트리거.
    OpenCV로 처리 후 Gazebo .world 파일 좌표 데이터 반환.
    TODO: 실제 OpenCV 파이프라인 연결 필요
    """
    result = await db.execute(
        select(Floorplan).where(Floorplan.id == floorplan_id)
    )
    fp = result.scalar_one_or_none()
    if not fp:
        raise HTTPException(status_code=404, detail="평면도를 찾을 수 없습니다.")

    if fp.status == "processing":
        raise HTTPException(status_code=409, detail="이미 처리 중입니다.")

    # 상태 업데이트
    fp.status = "processing"
    await db.flush()

    # TODO: 여기에 실제 OpenCV 벽체 추출 로직 연결
    # - JPG/PNG: cv2.Canny → HoughLinesP → 벽체 좌표 추출
    # - PDF: pdf2image → 이미지 변환 후 동일 파이프라인
    # - DXF: ezdxf 파싱 → LINE 엔티티 좌표 추출
    #
    # 처리 완료 시:
    #   fp.status = "completed"
    #   fp.wall_count = len(walls)
    #   fp.walls_data = walls
    #   fp.gazebo_world_path = "/path/to/generated.world"

    return FloorplanProcessResponse(
        id=fp.id,
        filename=fp.filename,
        status=fp.status,
        wall_count=fp.wall_count,
        walls=fp.walls_data,
        gazebo_world=fp.gazebo_world_path,
    )


@router.post("/analyze", response_model=FloorplanAnalyzeResponse)
async def analyze_floorplan(file: UploadFile = File(...)):
    """
    평면도 이미지에서 벽체 라인 추출 (Stateless — DB 불필요).
    JPG/PNG/WEBP 이미지를 받아 OpenCV로 처리 후 정규화 벽체 좌표 JSON 반환.
    프론트엔드 /employee/pre-work 에서 호출.
    """
    if file.content_type not in {"image/jpeg", "image/png", "image/webp"}:
        raise HTTPException(
            status_code=400,
            detail=f"이미지 파일만 지원합니다 (JPG/PNG/WEBP): {file.content_type}",
        )

    content = await file.read()

    try:
        result = extract_walls_from_bytes(content)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"이미지 처리 실패: {str(e)}")

    return FloorplanAnalyzeResponse(**result)


@router.delete("/{floorplan_id}", status_code=204)
async def delete_floorplan(
    floorplan_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """평면도 및 관련 파일 삭제"""
    result = await db.execute(
        select(Floorplan).where(Floorplan.id == floorplan_id)
    )
    fp = result.scalar_one_or_none()
    if not fp:
        raise HTTPException(status_code=404, detail="평면도를 찾을 수 없습니다.")

    # 파일 삭제
    if fp.file_path and os.path.exists(fp.file_path):
        os.remove(fp.file_path)

    await db.delete(fp)
