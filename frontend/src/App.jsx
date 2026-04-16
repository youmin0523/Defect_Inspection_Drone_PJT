/**
 * App.jsx
 * 역할: 루트 라우팅 컴포넌트
 *       - `/`         → Landing (마케팅 메인 페이지)
 *       - `/dashboard` → Dashboard (관제 대시보드 — Sidebar + Header + 메인)
 *       - WebSocket 연결은 DashboardLayout 내부에서만 초기화하여 랜딩에서는 비용 발생 없음
 */

import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Sidebar from './components/layout/Sidebar.jsx'
import Dashboard from './pages/Dashboard.jsx'
import Landing from './pages/Landing.jsx'
import Login from './pages/Login.jsx'
import Signup from './pages/Signup.jsx'
import FindAccount from './pages/FindAccount.jsx'
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

// //* [Modified Code] 풀스크린 HUD 레이아웃 — 레퍼런스 "위성 관제실" 톤 적용 라운드.
// Header 제거(검색·WS 상태·알림·프로필은 Dashboard 내부 상단 HUD 바로 흡수), main 의 p-4 제거하여
// BuildingScene 이 뷰포트 전체를 캔버스로 쓰도록 변경. Sidebar(w-14)는 내비게이션 용도로 유지.
function DashboardLayout() {
  // 대시보드 진입 시에만 WebSocket 연결 초기화
  useWebSocket()

  return (
    <div className="flex h-screen overflow-hidden bg-dashboard-bg">
      {/* 좌측 사이드바 (얇은 아이콘 내비) */}
      <Sidebar />

      {/* 우측 메인: 전체를 Dashboard 컨트롤 — HUD + 풀스크린 맵 */}
      <main className="flex-1 relative overflow-hidden">
        <Dashboard />
      </main>
    </div>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* //* [Modified Code] 루트는 랜딩 페이지로 변경 */}
        <Route path="/" element={<Landing />} />
        {/* 로그인 / 회원가입 / 계정 찾기 */}
        <Route path="/login" element={<Login />} />
        <Route path="/signup" element={<Signup />} />
        <Route path="/find-account" element={<FindAccount />} />
        {/* //* [Modified Code] 기존 대시보드는 /dashboard 경로로 이동 */}
        <Route path="/dashboard" element={<DashboardLayout />} />
      </Routes>
    </BrowserRouter>
  )
}
