/**
 * components/session/SessionLayout.jsx
 * 역할: 세션 셋업 플로우 공통 레이아웃
 *       - 상단 진척도 바 (1. 현장 정보 / 2. Level 선택 / 3. 모델링)
 *       - 중앙 `<Outlet />` 으로 각 단계 페이지 렌더
 *       - 좌측 사이드바/상단 Header 없이 풀스크린 다크 배경
 *       - 라우팅 가드(setup 없이 level/modeling 진입 방지)는 내부 `<Navigate />` 로 처리
 */

import { NavLink, Navigate, Outlet, useLocation } from 'react-router-dom'
import { Check } from 'lucide-react'
import logoWhite from '../../assets/logo/logo_white.png'
import useSessionStore from '../../store/sessionStore.js'

const STEPS = [
  { key: 'setup',    path: '/session/setup',    label: '현장 정보',  n: 1 },
  { key: 'level',    path: '/session/level',    label: 'Level 선택', n: 2 },
  { key: 'modeling', path: '/session/modeling', label: '3D 모델링',  n: 3 },
]

export default function SessionLayout() {
  const location = useLocation()
  const { siteName, operatorName, level } = useSessionStore()

  // 간이 가드: level 페이지는 setup 완료 필요, modeling 페이지는 level 선택 필요
  if (location.pathname === '/session/level' && (!siteName || !operatorName)) {
    return <Navigate to="/session/setup" replace />
  }
  if (location.pathname === '/session/modeling' && !level) {
    return <Navigate to="/session/level" replace />
  }

  const currentIndex = STEPS.findIndex((s) => s.path === location.pathname)

  return (
    <div className="min-h-screen bg-dashboard-bg text-white flex flex-col">
      {/* 상단 바: 로고 + 진척도 */}
      <header className="flex items-center justify-between px-6 py-4 border-b border-slate-800">
        <NavLink to="/" className="flex items-center gap-2" title="홈으로">
          <img src={logoWhite} alt="DRONE INSPECT" className="w-10 h-10 object-contain" />
          <span className="font-extrabold tracking-tight uppercase text-white">
            DRONE INSPECT
          </span>
        </NavLink>

        {/* 진척도 바 */}
        <ol className="flex items-center gap-2">
          {STEPS.map((step, idx) => {
            const isDone = idx < currentIndex
            const isCurrent = idx === currentIndex
            return (
              <li key={step.key} className="flex items-center gap-2">
                <div
                  className={`flex items-center gap-2 px-3 py-1.5 rounded-full border text-xs font-semibold transition ${
                    isCurrent
                      ? 'bg-accent-500/15 border-accent-500/60 text-accent-200'
                      : isDone
                        ? 'bg-slate-800 border-slate-700 text-slate-300'
                        : 'bg-slate-900 border-slate-800 text-slate-500'
                  }`}
                >
                  <span className={`w-5 h-5 rounded-full flex items-center justify-center text-[10px] font-bold ${
                    isCurrent
                      ? 'bg-accent-500 text-slate-900'
                      : isDone
                        ? 'bg-slate-600 text-slate-200'
                        : 'bg-slate-800 text-slate-500'
                  }`}>
                    {isDone ? <Check size={12} /> : step.n}
                  </span>
                  <span>{step.label}</span>
                </div>
                {idx < STEPS.length - 1 && (
                  <span className={`w-6 h-px ${idx < currentIndex ? 'bg-accent-500/60' : 'bg-slate-700'}`} />
                )}
              </li>
            )
          })}
        </ol>

        <div className="w-[200px]" aria-hidden>{/* 진척도 중앙 정렬용 여백 */}</div>
      </header>

      {/* 단계 별 컨텐츠 */}
      <main className="flex-1 flex items-center justify-center px-6 py-10">
        <Outlet />
      </main>
    </div>
  )
}
