/**
 * components/layout/Sidebar.jsx
 * 역할: 좌측 사이드바 내비게이션
 *       - 대시보드 메뉴 아이콘 (아이콘 전용 컴팩트 사이드바)
 *       - 현재 활성 메뉴 하이라이트
 *       - 접기/펼치기 토글 (향후 확장용)
 */

import { NavLink } from 'react-router-dom'

// //* [Modified Code] 라우팅 분리 후 `/`는 랜딩 페이지. 대시보드는 `/dashboard` 경로로 이동.
const NAV_ITEMS = [
  { to: '/dashboard', icon: '📊', label: '대시보드' },
]

export default function Sidebar() {
  return (
    <aside className="flex flex-col w-14 bg-dashboard-surface border-r border-slate-700 flex-shrink-0">
      {/* 로고 아이콘 (emerald accent 박스) */}
      <div className="flex items-center justify-center h-14 border-b border-slate-700">
        <div className="p-1.5 bg-accent-500 rounded-md shadow-md shadow-accent-900/30">
          <span className="text-white text-sm" aria-hidden>🚁</span>
        </div>
      </div>

      {/* 내비게이션 (active: emerald accent) */}
      <nav className="flex flex-col items-center gap-1 pt-3">
        {NAV_ITEMS.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            title={item.label}
            className={({ isActive }) =>
              `flex items-center justify-center w-10 h-10 rounded-lg text-lg transition-colors ${
                isActive
                  ? 'bg-accent-500/20 text-accent-400 border border-accent-500/40 shadow-[0_0_8px_rgba(16,185,129,0.3)]'
                  : 'text-slate-400 hover:bg-slate-700/60 hover:text-white'
              }`
            }
          >
            {item.icon}
          </NavLink>
        ))}
      </nav>
    </aside>
  )
}
