/**
 * App.jsx
 * 역할: 루트 라우팅 컴포넌트
 *       - `/`         → Landing (마케팅 메인 페이지)
 *       - `/dashboard` → Dashboard (관제 대시보드 — Sidebar + Header + 메인)
 *       - WebSocket 연결은 DashboardLayout 내부에서만 초기화하여 랜딩에서는 비용 발생 없음
 */

import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Header from './components/layout/Header.jsx'
import Sidebar from './components/layout/Sidebar.jsx'
import Dashboard from './pages/Dashboard.jsx'
import Landing from './pages/Landing.jsx'
import useWebSocket from './hooks/useWebSocket.js'

// //! [Original Code] 기존 AppLayout: 단일 라우트 `/` = Dashboard + WebSocket 최상단 초기화
// function AppLayout() {
//   useWebSocket()
//   return (
//     <div className="flex h-screen overflow-hidden bg-dashboard-bg">
//       <Sidebar />
//       <div className="flex flex-col flex-1 overflow-hidden">
//         <Header />
//         <main className="flex-1 overflow-auto p-4">
//           <Routes>
//             <Route path="/" element={<Dashboard />} />
//           </Routes>
//         </main>
//       </div>
//     </div>
//   )
// }

// //* [Modified Code] DashboardLayout으로 이름 변경 + /dashboard 전용 레이아웃으로 분리
// (랜딩 페이지에서는 Sidebar/Header/WebSocket이 필요 없으므로 격리)
function DashboardLayout() {
  // 대시보드 진입 시에만 WebSocket 연결 초기화
  useWebSocket()

  return (
    <div className="flex h-screen overflow-hidden bg-dashboard-bg">
      {/* 좌측 사이드바 */}
      <Sidebar />

      {/* 우측 메인 영역 */}
      <div className="flex flex-col flex-1 overflow-hidden">
        <Header />
        <main className="flex-1 overflow-auto p-4">
          <Dashboard />
        </main>
      </div>
    </div>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* //* [Modified Code] 루트는 랜딩 페이지로 변경 */}
        <Route path="/" element={<Landing />} />
        {/* //* [Modified Code] 기존 대시보드는 /dashboard 경로로 이동 */}
        <Route path="/dashboard" element={<DashboardLayout />} />
      </Routes>
    </BrowserRouter>
  )
}
