# =============================================
# app/api/report.py
# 역할: LLM 기반 하자 점검 보고서 생성 API
#       - POST /report/generate → 스트리밍 방식 보고서 생성 (Claude/Gemini)
#       - POST /report/preview  → 비스트리밍 방식 보고서 미리보기
#       - 프론트엔드는 fetch + response.body.getReader()로 청크 단위 수신
# =============================================

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db
from app.schemas.report import ReportRequest, ReportResponse
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
