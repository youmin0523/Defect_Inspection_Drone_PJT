/**
 * pages/Dashboard.jsx
 * 역할: 메인 대시보드 페이지
 *       - 실시간 영상 피드 (LiveVideoFeed + CameraToggle)
 *       - 열화상 온도 그래프 (ThermalGraph)
 *       - 하자 탐지 목록 패널 (DefectPanel)
 *       - 3D 건물 맵 (BuildingScene)
 *       - LLM 보고서 패널 (ReportPanel)
 */

import LiveVideoFeed from '../components/video/LiveVideoFeed.jsx'
import CameraToggle from '../components/video/CameraToggle.jsx'
import ThermalGraph from '../components/charts/ThermalGraph.jsx'
import DefectPanel from '../components/defects/DefectPanel.jsx'
import BuildingScene from '../components/map3d/BuildingScene.jsx'
import ReportPanel from '../components/report/ReportPanel.jsx'

export default function Dashboard() {
  return (
    <div className="grid grid-cols-12 gap-4 h-full">
      {/* ── 좌측: 영상 피드 + 온도 그래프 ── */}
      <div className="col-span-7 flex flex-col gap-4">
        {/* 영상 피드 */}
        <div className="card flex-shrink-0">
          <div className="flex items-center justify-between mb-3">
            <h2 className="text-sm font-semibold text-slate-300 uppercase tracking-wider">
              실시간 영상
            </h2>
            <CameraToggle />
          </div>
          <LiveVideoFeed />
        </div>

        {/* 열화상 온도 그래프 */}
        <div className="card flex-shrink-0">
          <h2 className="text-sm font-semibold text-slate-300 uppercase tracking-wider mb-3">
            실시간 온도 추이
          </h2>
          <ThermalGraph />
        </div>

        {/* 3D 빌딩 맵 */}
        <div className="card flex-1 min-h-[280px]">
          <h2 className="text-sm font-semibold text-slate-300 uppercase tracking-wider mb-3">
            하자 위치 맵 (3D)
          </h2>
          <BuildingScene />
        </div>
      </div>

      {/* ── 우측: 하자 목록 + 보고서 ── */}
      <div className="col-span-5 flex flex-col gap-4 overflow-hidden">
        {/* 하자 탐지 목록 */}
        <div className="card flex-1 overflow-hidden flex flex-col">
          <DefectPanel />
        </div>

        {/* LLM 보고서 */}
        <div className="card flex-shrink-0">
          <ReportPanel />
        </div>
      </div>
    </div>
  )
}
