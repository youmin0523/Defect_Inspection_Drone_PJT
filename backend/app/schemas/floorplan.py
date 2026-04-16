# =============================================
# app/schemas/floorplan.py
# 역할: 평면도 업로드/처리 Pydantic 스키마
# =============================================

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class FloorplanUploadResponse(BaseModel):
    """평면도 업로드 응답"""
    id: UUID
    filename: str
    content_type: str
    status: str  # uploaded / processing / completed / failed
    created_at: datetime

    class Config:
        from_attributes = True


class FloorplanProcessResponse(BaseModel):
    """OpenCV 처리 결과 응답"""
    id: UUID
    filename: str
    status: str
    wall_count: Optional[int] = Field(None, description="추출된 벽체 라인 수")
    walls: Optional[list] = Field(None, description="벽체 좌표 리스트 [{x1,y1,x2,y2}, ...]")
    gazebo_world: Optional[str] = Field(None, description="생성된 .world 파일 경로")


class FloorplanListResponse(BaseModel):
    """평면도 목록 응답"""
    items: list[FloorplanUploadResponse]
    total: int
