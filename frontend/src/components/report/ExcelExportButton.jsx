/**
 * components/report/ExcelExportButton.jsx
 * 역할: 현재 리포트를 `.xlsx` 로 내보내기 (SheetJS)
 *       - 공종별로 시트를 그룹핑하지 않고 단일 시트 + 공종 컬럼으로 필터 가능
 *       - 이미지는 base64 크롭을 Excel 에 삽입 (SheetJS pro 기능 필요) — 무료판에서는
 *         이미지 URL 만 주석 필드에 기록하고 본문에선 '이미지 있음' 표기만.
 *         (추후 백엔드 연결 시 openpyxl 로 네이티브 이미지 삽입 가능)
 *       - 열: 번호 / 공종 / 장소 / area / 하자 유형 / 심각도 / 검증 / 수동추가 / 조치 메모 / 시각 / 이미지유무
 */

import { FileSpreadsheet } from 'lucide-react'
import * as XLSX from 'xlsx'

function buildRows(report) {
  return (report.defects ?? []).map((d, idx) => ({
    번호: idx + 1,
    공종: d.trade ?? '',
    장소: d.location ?? d.location_label ?? '', // v1 호환 (location_label 백업)
    영역코드: d.area ?? '',
    '하자 유형': d.defect_type ?? d.category_code ?? '',
    카테고리코드: d.category_code ?? '',
    심각도: d.severity ?? '',
    검증: d.verified ? 'Y' : '',
    수동추가: d.is_manual ? 'Y' : '',
    '조치 메모': d.action_note ?? '',
    시각: d.timestamp ? new Date(d.timestamp).toLocaleString('ko-KR') : '',
    이미지: d.image_crop ? '있음' : '',
  }))
}

export default function ExcelExportButton({ report, label = 'Excel 내보내기', variant = 'primary' }) {
  const handleExport = () => {
    const rows = buildRows(report)

    const wb = XLSX.utils.book_new()

    // Sheet 1: 요약
    const summaryRows = [
      ['현장',    report.site_name ?? ''],
      ['운용자',  report.operator_name ?? ''],
      ['일자',    report.inspection_date ?? ''],
      ['Level',   report.level ?? ''],
      ['모델 소스', report.model_source ?? ''],
      ['총 하자 수', report.defects?.length ?? 0],
      ['HIGH', (report.defects ?? []).filter((d) => d.severity === 'HIGH').length],
      ['MED',  (report.defects ?? []).filter((d) => d.severity === 'MED').length],
      ['LOW',  (report.defects ?? []).filter((d) => d.severity === 'LOW').length],
      ['발행 일시', new Date().toLocaleString('ko-KR')],
    ]
    const wsSummary = XLSX.utils.aoa_to_sheet([['항목', '값'], ...summaryRows])
    wsSummary['!cols'] = [{ wch: 14 }, { wch: 40 }]
    XLSX.utils.book_append_sheet(wb, wsSummary, '요약')

    // Sheet 2: 하자 목록
    const wsDefects = XLSX.utils.json_to_sheet(rows)
    // 컬럼 너비 힌트
    wsDefects['!cols'] = [
      { wch: 5 },  { wch: 10 }, { wch: 14 }, { wch: 6 },
      { wch: 30 }, { wch: 10 }, { wch: 8 },  { wch: 6 },
      { wch: 8 },  { wch: 30 }, { wch: 20 }, { wch: 8 },
    ]
    XLSX.utils.book_append_sheet(wb, wsDefects, '하자목록')

    // 파일명: YYYYMMDD_현장명_하자리포트.xlsx
    const date = report.inspection_date ?? new Date().toISOString().slice(0, 10)
    const site = (report.site_name ?? 'report').replace(/[\\/:*?"<>|]/g, '_')
    const filename = `${date.replace(/-/g, '')}_${site}_하자리포트.xlsx`

    XLSX.writeFile(wb, filename)
  }

  const baseClass =
    variant === 'primary'
      ? 'bg-green-600 text-white hover:bg-green-700'
      : 'bg-white text-green-700 border border-green-600 hover:bg-green-50'

  return (
    <button
      type="button"
      onClick={handleExport}
      className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded text-xs font-bold shadow-sm transition ${baseClass}`}
      title="현재 리포트를 Excel 파일로 다운로드"
    >
      <FileSpreadsheet size={13} /> {label}
    </button>
  )
}
