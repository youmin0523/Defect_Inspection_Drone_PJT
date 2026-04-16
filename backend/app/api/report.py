# =============================================
# app/api/report.py
# 역할: LLM 기반 하자 점검 보고서 생성/저장/조회/다운로드 API
#       - POST /report/generate   → 스트리밍 방식 보고서 생성 (Claude/Gemini)
#       - POST /report/preview    → 비스트리밍 방식 보고서 미리보기
#       - POST /report/save       → 생성된 보고서 DB 저장
#       - GET  /report            → 저장된 보고서 목록 조회
#       - GET  /report/{id}       → 보고서 단건 조회
#       - GET  /report/{id}/download → 마크다운 파일 다운로드
#       - DELETE /report/{id}     → 보고서 삭제
# =============================================

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse, Response
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db
from app.models.report import Report
from app.schemas.report import (
    ReportRequest,
    ReportResponse,
    ReportSaveRequest,
    ReportSavedResponse,
    ReportListResponse,
)
from app.services.llm_report import LLMReportService

router = APIRouter()
report_service = LLMReportService()


@router.post("/generate")
async def generate_report_stream(
    request: ReportRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    LLM 기반 하자 점검 보고서 스트리밍 생성.
    텍스트 청크를 순차적으로 전송하여 프론트엔드에서 실시간 표시.

    프론트엔드 수신 방법:
        const response = await fetch('/api/v1/report/generate', {...})
        const reader = response.body.getReader()
        while (true) {
            const { done, value } = await reader.read()
            if (done) break
            // value를 텍스트로 디코딩하여 화면에 추가
        }
    """
    try:
        generator = report_service.generate_stream(request, db)
        return StreamingResponse(
            generator,
            media_type="text/plain; charset=utf-8",
            headers={"X-Content-Type-Options": "nosniff"},
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"보고서 생성 실패: {str(e)}")


@router.post("/preview", response_model=ReportResponse)
async def preview_report(
    request: ReportRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    LLM 기반 하자 점검 보고서 비스트리밍 생성.
    전체 내용을 한 번에 반환 (소규모 탐지 결과 또는 테스트용).
    """
    try:
        report = await report_service.generate_full(request, db)
        return report
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"보고서 생성 실패: {str(e)}")


# ── 보고서 저장/조회/다운로드 ──────────────────


@router.post("/save", response_model=ReportSavedResponse, status_code=201)
async def save_report(
    payload: ReportSaveRequest,
    db: AsyncSession = Depends(get_db),
):
    """생성된 보고서를 DB에 저장"""
    report = Report(
        title=payload.title,
        building_name=payload.building_name,
        inspector_name=payload.inspector_name,
        provider=payload.provider,
        content=payload.content,
        defect_count=payload.defect_count,
        high_count=payload.high_count,
        med_count=payload.med_count,
        low_count=payload.low_count,
    )
    db.add(report)
    await db.flush()
    return ReportSavedResponse.model_validate(report)


@router.get("", response_model=ReportListResponse)
async def list_reports(db: AsyncSession = Depends(get_db)):
    """저장된 보고서 목록 조회 (최신순)"""
    total = await db.scalar(select(func.count()).select_from(Report))
    result = await db.execute(
        select(Report).order_by(desc(Report.created_at))
    )
    items = result.scalars().all()
    return ReportListResponse(
        items=[ReportSavedResponse.model_validate(item) for item in items],
        total=total or 0,
    )


@router.get("/{report_id}", response_model=ReportSavedResponse)
async def get_report(report_id: UUID, db: AsyncSession = Depends(get_db)):
    """보고서 단건 조회"""
    result = await db.execute(select(Report).where(Report.id == report_id))
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="보고서를 찾을 수 없습니다.")
    return ReportSavedResponse.model_validate(report)


@router.get("/{report_id}/download")
async def download_report(report_id: UUID, db: AsyncSession = Depends(get_db)):
    """보고서 마크다운 파일 다운로드"""
    result = await db.execute(select(Report).where(Report.id == report_id))
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="보고서를 찾을 수 없습니다.")

    filename = f"{report.title or 'report'}_{report.created_at.strftime('%Y%m%d')}.md"
    return Response(
        content=report.content,
        media_type="text/markdown; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.delete("/{report_id}", status_code=204)
async def delete_report(report_id: UUID, db: AsyncSession = Depends(get_db)):
    """보고서 삭제"""
    result = await db.execute(select(Report).where(Report.id == report_id))
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="보고서를 찾을 수 없습니다.")
    await db.delete(report)
