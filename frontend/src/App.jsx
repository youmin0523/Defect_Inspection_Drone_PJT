/**
 * App.jsx
 * 역할: 루트 라우팅 컴포넌트
 *       - `/`         → Landing
 *       - `/login`, `/signup`, `/find-account` → 공개 계정 페이지
 *       - `/session/*` → SessionLayout (setup / level / modeling) — 직원 진입 전 워크플로우
 *       - `/dashboard` → ProtectedSessionLayout 가드 + DashboardLayout (+ nested `/report`)
 *       - WebSocket 연결은 DashboardLayout 내부에서만 초기화하여 랜딩/세션 페이지에서는 비용 발생 없음
 */

import { BrowserRouter, Routes, Route, Outlet } from 'react-router-dom'
import Sidebar from './components/layout/Sidebar.jsx'
import Dashboard from './pages/Dashboard.jsx'
import Landing from './pages/Landing.jsx'
import Login from './pages/Login.jsx'
import Signup from './pages/Signup.jsx'
import FindAccount from './pages/FindAccount.jsx'
// //* [Modified Code] 직원 전용 진입 랜딩 (Interior Inspection Dashboard 목업)
import EmployeeLanding from './pages/EmployeeLanding.jsx'
import PreWork from './pages/employee/PreWork.jsx'
import ReportsList from './pages/employee/ReportsList.jsx'
import ReportDetail from './pages/employee/ReportDetail.jsx'
import SiteManagement from './pages/employee/SiteManagement.jsx'
import SiteDetail from './pages/employee/SiteDetail.jsx'
import Analytics from './pages/employee/Analytics.jsx'
import SessionLayout from './components/session/SessionLayout.jsx'
import ProtectedSessionLayout from './components/session/ProtectedSessionLayout.jsx'
import SessionSetup from './pages/session/SessionSetup.jsx'
import SessionLevel from './pages/session/SessionLevel.jsx'
import SessionModeling from './pages/session/SessionModeling.jsx'
import OAuthCallback from './pages/OAuthCallback.jsx'
import ReportModal from './components/report/ReportModal.jsx'
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
        {/* //* [Modified Code] nested route — /dashboard/report 진입 시 ReportModal 오버레이 렌더 */}
        <Outlet />
      </main>
    </div>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* 공개 라우트 */}
        <Route path="/" element={<Landing />} />
        <Route path="/login" element={<Login />} />
        <Route path="/signup" element={<Signup />} />
        <Route path="/find-account" element={<FindAccount />} />
        {/* OAuth 콜백 (Google / Kakao / Naver) */}
        <Route path="/auth/:provider/callback" element={<OAuthCallback />} />

        {/* //* [Modified Code] 직원 전용 랜딩 — "직원 전용" 버튼 클릭 시 진입하는 허브 */}
        <Route path="/employee" element={<EmployeeLanding />} />
        {/* //* [Modified Code] 사전 작업 — CAD/평면도 업로드 → Mock 3D 모델링 → preModelStore 저장 */}
        <Route path="/employee/pre-work" element={<PreWork />} />
        {/* //* [Modified Code] 리포트 아카이브 — 사무실 목록 + 재편집 상세 */}
        <Route path="/employee/reports" element={<ReportsList />} />
        <Route path="/employee/reports/:id" element={<ReportDetail />} />
        {/* //* [Modified Code] 현장 관리 — 목록 + 상세 */}
        <Route path="/employee/sites" element={<SiteManagement />} />
        <Route path="/employee/sites/:id" element={<SiteDetail />} />
        {/* //* [Modified Code] 분석·보고서 — 경향보고서 + 주간업무보고서 */}
        <Route path="/employee/analytics" element={<Analytics />} />

        {/* //* [Modified Code] 세션 워크플로우 (Setup → Level → Modeling) */}
        <Route path="/session" element={<SessionLayout />}>
          <Route path="setup"    element={<SessionSetup />} />
          <Route path="level"    element={<SessionLevel />} />
          <Route path="modeling" element={<SessionModeling />} />
        </Route>

        {/* //* [Modified Code] 대시보드 — 세션 완료 가드 + nested report 모달 */}
        <Route element={<ProtectedSessionLayout />}>
          <Route path="/dashboard" element={<DashboardLayout />}>
            <Route path="report" element={<ReportModal />} />
          </Route>
        </Route>
      </Routes>
    </BrowserRouter>
  )
}
