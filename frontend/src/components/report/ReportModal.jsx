/**
 * components/report/ReportModal.jsx
 * 역할: `/dashboard/report` nested route 용 리포트 오버레이 모달
 *       - MissionControl END → Dashboard 가 navigate('/dashboard/report') → DashboardLayout <Outlet /> 에 렌더
 *       - DashboardLayout 부모가 유지되므로 WebSocket 끊김 없음
 *       - 세션 정보 요약(현장명/운용자/날짜/Level) + 하자 카운트 + ReportPanel(LLM 스트리밍) 재사용
 *       - "새 점검 시작" 클릭 → sessionStore.reset() + droneStore.reset() + /session/setup replace
 */

import { useNavigate } from 'react-router-dom'
import { X, FileText, CheckCircle2, RotateCcw } from 'lucide-react'
import ReportPanel from './ReportPanel.jsx'
import useSessionStore from '../../store/sessionStore.js'
import useDroneStore from '../../store/droneStore.js'
import useDefectStore from '../../store/defectStore.js'

const LEVEL_NAME = {
  1: 'CAD 도면',
  2: '평면도 이미지',
  3: '드론 자율비행',
}

export default function ReportModal() {
  const navigate = useNavigate()
  const { siteName, operatorName, inspectionDate, level, startedAt } = useSessionStore()
  const sessionReset = useSessionStore((s) => s.reset)
  const droneReset = useDroneStore((s) => s.reset)
  const defects = useDefectStore((s) => s.defects)

  const severityCounts = defects.reduce(
    (acc, d) => {
      acc[d.severity] = (acc[d.severity] || 0) + 1
      return acc
    },
    { HIGH: 0, MED: 0, LOW: 0 }
  )

  const handleClose = () => navigate('/dashboard')
  const handleNewInspection = () => {
    sessionReset()
    droneReset()
    navigate('/session/setup', { replace: true })
  }

  return (
    <div
      role="dialog"
      aria-modal="true"
      className="absolute inset-0 z-50 flex items-center justify-center p-6 bg-slate-950/70 backdrop-blur-sm"
      onClick={(e) => {
        if (e.target === e.currentTarget) handleClose()
      }}
    >
      <div className="relative w-full max-w-3xl max-h-[90vh] overflow-hidden rounded-2xl bg-slate-900 border border-accent-500/30 shadow-2xl flex flex-col">
        {/* 헤더 */}
        <header className="flex items-start justify-between px-6 py-4 border-b border-slate-700 flex-shrink-0">
          <div className="flex items-start gap-3">
            <div className="w-10 h-10 rounded-full bg-accent-500/20 border border-accent-500/60 flex items-center justify-center">
              <CheckCircle2 size={20} className="text-accent-300" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-white">비행 종료 · 점검 리포트</h2>
              <p className="text-xs text-slate-400">
                세션 데이터를 기반으로 AI 가 보고서를 작성합니다.
              </p>
            </div>
          </div>
          <button
            type="button"
            onClick={handleClose}
            title="대시보드로 돌아가기"
            className="p-1.5 rounded text-slate-400 hover:bg-slate-800 hover:text-white transition"
          >
            <X size={18} />
          </button>
        </header>

        {/* 세션 요약 */}
        <section className="px-6 py-4 border-b border-slate-800 flex-shrink-0">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <SummaryCell label="현장" value={siteName || '—'} />
            <SummaryCell label="운용자" value={operatorName || '—'} />
            <SummaryCell label="일자" value={inspectionDate || '—'} />
            <SummaryCell label="Level" value={level ? `L${level} · ${LEVEL_NAME[level]}` : '—'} />
          </div>

          <div className="grid grid-cols-4 gap-3 mt-3">
            <SummaryCell label="총 하자" value={`${defects.length}건`} accent />
            <SummaryCell label="HIGH" value={severityCounts.HIGH} color="text-red-400" />
            <SummaryCell label="MED"  value={severityCounts.MED}  color="text-orange-400" />
            <SummaryCell label="LOW"  value={severityCounts.LOW}  color="text-yellow-400" />
          </div>
        </section>

        {/* ReportPanel 재사용 */}
        <section className="px-6 py-4 flex-1 overflow-y-auto">
          <div className="flex items-center gap-2 mb-2">
            <FileText size={14} className="text-accent-400" />
            <span className="text-xs font-bold uppercase tracking-wider text-white">
              AI Generated Report
            </span>
          </div>
          <ReportPanel />
        </section>

        {/* 하단 액션 */}
        <footer className="flex items-center justify-between px-6 py-3 border-t border-slate-800 flex-shrink-0">
          <button
            type="button"
            onClick={handleClose}
            className="text-xs text-slate-400 hover:text-white transition"
          >
            대시보드로 돌아가기
          </button>
          <button
            type="button"
            onClick={handleNewInspection}
            className="flex items-center gap-2 px-4 py-2 rounded-md bg-accent-500 text-slate-900 font-bold text-xs hover:bg-accent-400 transition shadow-lg"
          >
            <RotateCcw size={13} /> 새 점검 시작
          </button>
        </footer>
      </div>
    </div>
  )
}

function SummaryCell({ label, value, accent, color }) {
  return (
    <div className={`rounded-lg px-3 py-2 border ${accent ? 'bg-accent-500/10 border-accent-500/40' : 'bg-slate-950/40 border-slate-800'}`}>
      <div className="text-[10px] font-mono text-slate-500 uppercase tracking-wider mb-0.5">{label}</div>
      <div className={`text-sm font-semibold truncate ${color || (accent ? 'text-accent-300' : 'text-white')}`}>
        {value}
      </div>
    </div>
  )
}
