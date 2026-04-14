/**
 * App.jsx
 * 역할: 루트 레이아웃 컴포넌트
 *       - React Router 라우팅 설정
 *       - Header + Sidebar + 메인 콘텐츠 레이아웃
 *       - WebSocket 연결 초기화 (앱 마운트 시 단 한 번)
 *       - 대시보드 메인 페이지 렌더링
 */

import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Header from './components/layout/Header.jsx'
import Sidebar from './components/layout/Sidebar.jsx'
import Dashboard from './pages/Dashboard.jsx'
import useWebSocket from './hooks/useWebSocket.js'

function AppLayout() {
  // 앱 최상단에서 WebSocket 연결 초기화
  useWebSocket()

  return (
    <div className="flex h-screen overflow-hidden bg-dashboard-bg">
      {/* 좌측 사이드바 */}
      <Sidebar />

      {/* 우측 메인 영역 */}
      <div className="flex flex-col flex-1 overflow-hidden">
        <Header />
        <main className="flex-1 overflow-auto p-4">
          <Routes>
            <Route path="/" element={<Dashboard />} />
          </Routes>
        </main>
      </div>
    </div>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <AppLayout />
    </BrowserRouter>
  )
}
