/**
 * pages/session/SessionSetup.jsx
 * 역할: 세션 Step 1 — 현장명 / 운용자 / 날짜 입력 폼
 *       - 3개 필드 모두 필수, 제출 시 sessionStore.setSessionInfo() 호출 + /session/level 이동
 *       - 유효성: 현장명 2자 이상, 운용자 2자 이상, 날짜 YYYY-MM-DD
 */

import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Building2, User, Calendar, ArrowRight } from 'lucide-react'
import useSessionStore from '../../store/sessionStore.js'

export default function SessionSetup() {
  const navigate = useNavigate()
  const { siteName: initSite, operatorName: initOperator, inspectionDate: initDate, setSessionInfo } = useSessionStore()

  const [siteName, setSiteName] = useState(initSite ?? '')
  const [operatorName, setOperatorName] = useState(initOperator ?? '')
  const [inspectionDate, setInspectionDate] = useState(initDate ?? new Date().toISOString().slice(0, 10))
  const [error, setError] = useState(null)

  const handleSubmit = (e) => {
    e.preventDefault()
    if (siteName.trim().length < 2) return setError('현장명은 2자 이상 입력해주세요.')
    if (operatorName.trim().length < 2) return setError('운용자명은 2자 이상 입력해주세요.')
    if (!/^\d{4}-\d{2}-\d{2}$/.test(inspectionDate)) return setError('날짜 형식(YYYY-MM-DD)이 올바르지 않습니다.')

    setError(null)
    setSessionInfo({
      siteName: siteName.trim(),
      operatorName: operatorName.trim(),
      inspectionDate,
    })
    navigate('/session/level')
  }

  return (
    <form
      onSubmit={handleSubmit}
      className="w-full max-w-xl bg-slate-900/70 border border-slate-700/60 rounded-2xl shadow-2xl p-8 backdrop-blur-md"
    >
      <h1 className="text-2xl font-bold text-white mb-1">현장 정보</h1>
      <p className="text-sm text-slate-400 mb-6 break-keep">
        점검을 시작할 현장과 운용자 정보를 입력해주세요. 리포트에 자동 기록됩니다.
      </p>

      {/* 현장명 */}
      <label className="block mb-4">
        <span className="flex items-center gap-1.5 text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5">
          <Building2 size={13} /> 현장명
        </span>
        <input
          type="text"
          value={siteName}
          onChange={(e) => setSiteName(e.target.value)}
          placeholder="예: 송파 헬리오시티 102동 1503호"
          className="w-full bg-slate-950/60 border border-slate-700 rounded-md px-3 py-2.5 text-sm text-white placeholder:text-slate-600 focus:outline-none focus:ring-2 focus:ring-accent-500 focus:border-accent-500"
          autoFocus
          required
        />
      </label>

      {/* 운용자 */}
      <label className="block mb-4">
        <span className="flex items-center gap-1.5 text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5">
          <User size={13} /> 운용자
        </span>
        <input
          type="text"
          value={operatorName}
          onChange={(e) => setOperatorName(e.target.value)}
          placeholder="예: 김민수"
          className="w-full bg-slate-950/60 border border-slate-700 rounded-md px-3 py-2.5 text-sm text-white placeholder:text-slate-600 focus:outline-none focus:ring-2 focus:ring-accent-500 focus:border-accent-500"
          required
        />
      </label>

      {/* 날짜 */}
      <label className="block mb-6">
        <span className="flex items-center gap-1.5 text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5">
          <Calendar size={13} /> 점검 일자
        </span>
        <input
          type="date"
          value={inspectionDate}
          onChange={(e) => setInspectionDate(e.target.value)}
          className="w-full bg-slate-950/60 border border-slate-700 rounded-md px-3 py-2.5 text-sm text-white focus:outline-none focus:ring-2 focus:ring-accent-500 focus:border-accent-500"
          required
        />
      </label>

      {error && (
        <div className="mb-4 text-xs text-red-400 bg-red-500/10 border border-red-500/30 rounded-md px-3 py-2">
          {error}
        </div>
      )}

      <div className="flex items-center justify-end">
        <button
          type="submit"
          className="flex items-center gap-2 px-5 py-2.5 rounded-md bg-accent-500 text-slate-900 font-bold text-sm hover:bg-accent-400 transition shadow-lg"
        >
          다음
          <ArrowRight size={14} />
        </button>
      </div>
    </form>
  )
}
