# =============================================
# app/models/__init__.py
# 역할: models 패키지 초기화 파일
#       - 여기서 모델을 임포트하면 Base.metadata에 자동 등록됨
#       - 임포트 순서: 참조 당하는 쪽 → 참조 하는 쪽
# =============================================

from app.models.defect import DefectLog  # noqa: F401
from app.models.user import User  # noqa: F401
from app.models.business_profile import BusinessProfile  # noqa: F401
from app.models.term import Term  # noqa: F401
from app.models.user_term_agreement import UserTermAgreement  # noqa: F401

__all__ = [
    "DefectLog",
    "User",
    "BusinessProfile",
    "Term",
    "UserTermAgreement",
]
