# =============================================
# app/api/admin_gpu.py
# 역할: 관리자용 GCP GPU VM 원격 제어 엔드포인트
#       - GET  /admin/gpu/status — 인스턴스 상태 (RUNNING / TERMINATED 등)
#       - POST /admin/gpu/start  — 인스턴스 시작 (시간당 과금)
#       - POST /admin/gpu/stop   — 인스턴스 정지 (GPU 과금 중단)
#
# 인증: 슈퍼어드민 전용 (require_superadmin)
# 호출 흐름: 프론트(브라우저) → Fly.io 백엔드(이 라우터) → GCP Compute REST API
#   ↳ 로컬 bat 파일 의존 제거. 어떤 브라우저에서도 admin 권한이면 켜고 끌 수 있음.
# =============================================

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.dependencies import require_superadmin
from app.services.gcp_compute import GcpComputeError, gcp_compute

router = APIRouter()


class GpuStatusResponse(BaseModel):
    name: str | None = None
    status: str | None = None  # RUNNING / TERMINATED / STOPPING / PROVISIONING / STAGING
    zone: str | None = None
    machine_type: str | None = None
    last_start_at: str | None = None
    last_stop_at: str | None = None


class GpuOperationResponse(BaseModel):
    operation: str | None = None
    status: str | None = None  # PENDING / RUNNING / DONE


def _raise_5xx(e: GcpComputeError) -> None:
    raise HTTPException(
        status_code=status.HTTP_502_BAD_GATEWAY,
        detail=f"GCP Compute 호출 실패: {e}",
    )


@router.get("/status", response_model=GpuStatusResponse)
async def get_gpu_status(_=Depends(require_superadmin)):
    """GPU VM 현재 상태 조회 (슈퍼어드민 전용)."""
    try:
        return await gcp_compute.get_status()
    except GcpComputeError as e:
        _raise_5xx(e)


@router.post("/start", response_model=GpuOperationResponse)
async def start_gpu(_=Depends(require_superadmin)):
    """GPU VM 시작 — 시간당 ~$0.71 과금 시작 (L4 GPU)."""
    try:
        return await gcp_compute.start()
    except GcpComputeError as e:
        _raise_5xx(e)


@router.post("/stop", response_model=GpuOperationResponse)
async def stop_gpu(_=Depends(require_superadmin)):
    """GPU VM 정지 — GPU 시간당 과금 중단 (디스크/IP 만 ~$13/월 유지)."""
    try:
        return await gcp_compute.stop()
    except GcpComputeError as e:
        _raise_5xx(e)
