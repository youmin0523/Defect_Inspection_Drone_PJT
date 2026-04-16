# =============================================
# app/models/__init__.py
# 역할: models 패키지 초기화 파일
#       - 여기서 모델을 임포트하면 Base.metadata에 자동 등록됨
#       - 임포트 순서: 참조 당하는 쪽 → 참조 하는 쪽
#       - 새 모델 추가 시 해당 영역 주석 아래에 추가
# =============================================

# ── 사용자 / 인증 ────────────────────────────
from app.models.user import User  # noqa: F401
from app.models.business_profile import BusinessProfile  # noqa: F401
from app.models.term import Term  # noqa: F401
from app.models.user_term_agreement import UserTermAgreement  # noqa: F401

# ── 하자 탐지 ────────────────────────────────
from app.models.defect import DefectLog  # noqa: F401

# ── 드론 / 센서 ──────────────────────────────
from app.models.telemetry import TelemetryLog  # noqa: F401
from app.models.slam_map import SlamMap  # noqa: F401

# ── 평면도 / 환경 생성 ───────────────────────
from app.models.floorplan import Floorplan  # noqa: F401

# ── 보고서 ───────────────────────────────────
from app.models.report import Report  # noqa: F401

__all__ = [
    # 사용자 / 인증
    "User",
    "BusinessProfile",
    "Term",
    "UserTermAgreement",
    # 하자 탐지
    "DefectLog",
    # 드론 / 센서
    "TelemetryLog",
    "SlamMap",
    # 평면도
    "Floorplan",
    # 보고서
    "Report",
]
