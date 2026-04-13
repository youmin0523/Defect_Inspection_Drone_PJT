# =============================================
# app/models/defect.py
# 역할: 하자 탐지 로그 ORM 모델 정의
#       - 드론이 탐지한 모든 하자 정보를 저장하는 핵심 테이블
#       - 위치(LiDAR 3D 좌표), 이미지 크롭, 열화상 온도, 심각도 포함
#       - PostgreSQL JSONB 타입으로 원시 YOLO 탐지 결과 저장
# 테이블명: defect_logs
# =============================================

import uuid
from datetime import datetime

from sqlalchemy import (
    Column, String, Float, Text, BigInteger,
    DateTime, Enum as SAEnum, Index, func
)
from sqlalchemy.dialects.postgresql import UUID, JSONB

from app.db.base import Base


class DefectLog(Base):
    """
    하자 탐지 로그 테이블.
    드론 비행 중 AI가 탐지한 하자 1건 = 1 레코드.
    """
    __tablename__ = "defect_logs"

    # ── 기본 키 ──────────────────────────────
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)

    # ── 하자 분류 ─────────────────────────────
    # area: A(구조) / B(단열·방수) / C(마감재) / D(바닥) / E(창호)
    area = Column(String(1), nullable=False, comment="하자 영역 코드 (A-E)")
    # category_code: A-01, B-03 등 20종 코드
    category_code = Column(String(10), nullable=False, comment="하자 카테고리 코드")
    defect_type = Column(String(100), nullable=False, comment="하자 유형명 (한글)")

    # ── 심각도 ───────────────────────────────
    # HIGH: 구조·안전·방수 직결 / MED: 기능 저하 / LOW: 마감 미관
    severity = Column(
        SAEnum("HIGH", "MED", "LOW", name="severity_enum"),
        nullable=False,
        comment="심각도 등급"
    )

    # ── AI 탐지 결과 ──────────────────────────
    confidence = Column(Float, nullable=False, comment="AI 탐지 신뢰도 (0.0~1.0)")
    # 바운딩 박스 (프레임 내 정규화 좌표 0.0~1.0)
    bbox_x = Column(Float, comment="바운딩 박스 중심 X (정규화)")
    bbox_y = Column(Float, comment="바운딩 박스 중심 Y (정규화)")
    bbox_w = Column(Float, comment="바운딩 박스 너비 (정규화)")
    bbox_h = Column(Float, comment="바운딩 박스 높이 (정규화)")

    # ── 3D 공간 좌표 (TF-Luna LiDAR) ──────────
    # 드론 TF(Transform) → 월드 좌표계(ENU) 변환 후 저장
    lidar_x = Column(Float, comment="월드 좌표 X (m)")
    lidar_y = Column(Float, comment="월드 좌표 Y (m)")
    lidar_z = Column(Float, comment="월드 좌표 Z / 고도 (m)")

    # ── 이미지 데이터 ─────────────────────────
    # Base64 인코딩된 JPEG 크롭 이미지
    image_crop = Column(Text, comment="하자 영역 크롭 이미지 (Base64 JPEG)")

    # ── 열화상 데이터 ─────────────────────────
    thermal_max = Column(Float, comment="하자 ROI 최고 온도 (°C)")
    thermal_min = Column(Float, comment="하자 ROI 최저 온도 (°C)")
    thermal_avg = Column(Float, comment="하자 ROI 평균 온도 (°C)")

    # ── 메타데이터 ────────────────────────────
    timestamp = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="탐지 시각 (UTC)"
    )
    frame_id = Column(BigInteger, comment="탐지된 비디오 프레임 번호")

    # 원시 YOLO 탐지 결과 전체 저장 (디버깅·재분석용)
    raw_payload = Column(JSONB, comment="YOLO 원시 탐지 결과 JSON")

    # ── 인덱스 ───────────────────────────────
    # 필터링 쿼리 최적화: 심각도+시간 / 영역+시간 / 프레임
    __table_args__ = (
        Index("idx_defect_severity_ts", "severity", timestamp.desc()),
        Index("idx_defect_area_ts", "area", timestamp.desc()),
        Index("idx_defect_frame", "frame_id"),
    )

    def __repr__(self):
        return (
            f"<DefectLog id={self.id} "
            f"code={self.category_code} "
            f"severity={self.severity} "
            f"ts={self.timestamp}>"
        )
