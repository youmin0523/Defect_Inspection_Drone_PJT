/**
 * components/layout/Sidebar.jsx
 * 역할: 좌측 사이드바 내비게이션
 *       - 대시보드 메뉴 아이콘 (아이콘 전용 컴팩트 사이드바)
 *       - 현재 활성 메뉴 하이라이트
 *       - 접기/펼치기 토글 (향후 확장용)
 */

import { NavLink } from 'react-router-dom'

const NAV_ITEMS = [
  { to: '/', icon: '📊', label: '대시보드' },
]

export default function Sidebar() {
  return (
    <aside className="flex flex-col w-14 bg-dashboard-surface border-r border-dashboard-border flex-shrink-0">
      {/* 로고 아이콘 */}
      <div className="flex items-center justify-center h-14 border-b border-dashboard-border">
        <span className="text-lg">🚁</span>
      </div>

      {/* 내비게이션 */}
      <nav className="flex flex-col items-center gap-1 pt-3">
        {NAV_ITEMS.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            title={item.label}
            className={({ isActive }) =>
              `flex items-center justify-center w-10 h-10 rounded-lg text-lg transition-colors ${
                isActive
                  ? 'bg-brand-600 text-white'
                  : 'text-slate-400 hover:bg-dashboard-border hover:text-white'
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
