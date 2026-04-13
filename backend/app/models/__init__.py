# =============================================
# app/models/__init__.py
# 역할: models 패키지 초기화 파일
#       - 여기서 모델을 임포트하면 Base.metadata에 자동 등록됨
# =============================================

from app.models.defect import DefectLog  # noqa: F401

__all__ = ["DefectLog"]
