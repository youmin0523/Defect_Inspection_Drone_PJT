# =============================================
# app/schemas/defect.py
# 역할: 하자 탐지 로그 Pydantic 입출력 스키마 정의
#       - DefectLogCreate: POST 요청 시 클라이언트 입력 검증
#       - DefectLogResponse: GET 응답 시 직렬화 형식
#       - DefectLogFilter: 목록 조회 시 필터 파라미터
# 사용: API 라우터에서 request body 및 response_model로 사용
# =============================================

from datetime import datetime
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel, Field


class BoundingBox(BaseModel):
    """바운딩 박스 좌표 (0.0 ~ 1.0 정규화)"""
    x: float = Field(ge=0.0, le=1.0)
    y: float = Field(ge=0.0, le=1.0)
    w: float = Field(ge=0.0, le=1.0)
    h: float = Field(ge=0.0, le=1.0)


class LidarPosition(BaseModel):
    """LiDAR 기반 3D 월드 좌표 (미터 단위)"""
    x: Optional[float] = None
    y: Optional[float] = None
    z: Optional[float] = None


class ThermalData(BaseModel):
    """열화상 온도 데이터 (섭씨)"""
    max: Optional[float] = None
    min: Optional[float] = None
    avg: Optional[float] = None


# ── 생성 요청 스키마 ─────────────────────────
class DefectLogCreate(BaseModel):
    """
    하자 탐지 결과 저장 요청.
    AI 파이프라인에서 탐지 후 백엔드 DB에 저장할 때 사용.
    """
    area: str = Field(..., pattern="^[A-E]$", description="하자 영역 코드 (A-E)")
    category_code: str = Field(..., description="하자 카테고리 코드 (예: A-01)")
    defect_type: str = Field(..., description="하자 유형명 (한글)")
    severity: str = Field(..., pattern="^(HIGH|MED|LOW)$", description="심각도 등급")
    confidence: float = Field(..., ge=0.0, le=1.0, description="AI 탐지 신뢰도")
    bbox: Optional[BoundingBox] = None
    lidar_position: Optional[LidarPosition] = None
    thermal_data: Optional[ThermalData] = None
    image_crop: Optional[str] = None  # Base64 JPEG
    frame_id: Optional[int] = None
    raw_payload: Optional[dict] = None


# ── 응답 스키마 ──────────────────────────────
class DefectLogResponse(BaseModel):
    """
    하자 탐지 로그 응답.
    목록 조회 및 단건 조회 시 반환 형식.
    """
    id: UUID
    area: str
    category_code: str
    defect_type: str
    severity: str
    confidence: float
    bbox_x: Optional[float]
    bbox_y: Optional[float]
    bbox_w: Optional[float]
    bbox_h: Optional[float]
    lidar_x: Optional[float]
    lidar_y: Optional[float]
    lidar_z: Optional[float]
    image_crop: Optional[str]
    thermal_max: Optional[float]
    thermal_min: Optional[float]
    thermal_avg: Optional[float]
    timestamp: datetime
    frame_id: Optional[int]

    class Config:
        from_attributes = True  # SQLAlchemy ORM 객체 직접 변환


# ── 목록 조회 필터 ────────────────────────────
class DefectLogFilter(BaseModel):
    """하자 목록 조회 시 필터 파라미터"""
    area: Optional[str] = None          # A-E
    severity: Optional[str] = None      # HIGH / MED / LOW
    category_code: Optional[str] = None  # A-01 등
    limit: int = Field(default=50, ge=1, le=500)
    offset: int = Field(default=0, ge=0)


# ── 요약 통계 응답 ────────────────────────────
class DefectSummary(BaseModel):
    """대시보드용 하자 요약 통계"""
    total: int
    by_severity: dict  # {"HIGH": 3, "MED": 7, "LOW": 12}
    by_area: dict      # {"A": 5, "B": 3, ...}
    latest: Optional[DefectLogResponse] = None


class DefectLogListResponse(BaseModel):
    """하자 목록 페이지네이션 응답"""
    items: List[DefectLogResponse]
    total: int
    limit: int
    offset: int
