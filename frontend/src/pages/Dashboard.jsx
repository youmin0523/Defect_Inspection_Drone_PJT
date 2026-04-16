/**
 * pages/Dashboard.jsx
 * 역할: 풀스크린 HUD 관제 대시보드 (레퍼런스 "위성 관제실" 톤)
 *       - //! [Original Code] 12-col grid 카드 레이아웃 (영상/온도/3D맵/하자/보고서)
 *       - //* [Modified Code v1] 풀스크린 3D 맵 배경 + HUD 플로팅 오버레이
 *       - //* [Modified Code v2] 메인 배경을 LIVE 카메라 피드로 승격, 3D 맵은 우하단 미니맵으로 강등
 *         (사용자 피드백: "3D 맵은 도면/평면도/시뮬레이션 모델링용 — 우하단 미니맵이 맞다")
 *
 * 레이아웃 구조:
 *   ┌─────────────────────────────────────────────────────────────────┐
 *   │  [DashboardTopBar]                                               │
 *   ├─────────────────────────────────────────────────────────────────┤
 *   │ ┌───────────┐                                   ┌─────────────┐ │
 *   │ │ THERMAL   │   <LiveVideoFeed fill> 풀스크린    │ AI DEFECT   │ │
 *   │ │ TREND PIP │   (선택 드론 카메라 = RGB/열화상)   │ ANALYSIS    │ │
 *   │ └───────────┘   ─ 상단 중앙 HUD 뱃지(드론/모드/LIVE) ─│            │ │
 *   │                                                    │             │ │
 *   │ ┌────────────┐                    ┌──────────────┐ └─────────────┘ │
 *   │ │ DRONES     │                    │ 3D MINI MAP  │                 │
 *   │ │ (01 / 02)  │                    │ (BuildingScene)│               │
 *   │ └────────────┘                    └──────────────┘                 │
 *   └─────────────────────────────────────────────────────────────────┘
 *
 * 드론 ↔ 카메라 연동:
 *   DRONE 01 클릭 → cameraMode='rgb'     → 메인 배경이 RGB 스트림
 *   DRONE 02 클릭 → cameraMode='thermal' → 메인 배경이 열화상 스트림
 */

import { Activity, Video } from 'lucide-react'
import BuildingScene from '../components/map3d/BuildingScene.jsx'
import LiveVideoFeed from '../components/video/LiveVideoFeed.jsx'
import ThermalGraph from '../components/charts/ThermalGraph.jsx'
import DefectPanel from '../components/defects/DefectPanel.jsx'
import DashboardTopBar from '../components/dashboard/DashboardTopBar.jsx'
import DronesPanel from '../components/dashboard/DronesPanel.jsx'
import useDroneStore from '../store/droneStore.js'

const CAMERA_LABEL = {
  rgb: 'RGB · 일반 카메라',
  thermal: 'THERMAL · 열화상',
  blend: 'BLEND · 합성',
}

// HUD 구역 치수 — 중앙 LIVE 피드 박스가 피해야 할 좌/우/상/하 safe zone (px).
// 값은 각 패널(Thermal Trend·DronesPanel·AI Analysis·Minimap) 폭/높이 + gap 기준.
const SAFE = {
  top: 100,    // TopBar(56) + 여백(44)
  bottom: 150, // DronesPanel(≈134) + gap
  left: 316,   // Thermal Trend(280) + margin(4) + gap(32)
  right: 400,  // AI Analysis(360) + margin(4) + gap(36)
}

// 우하단 3D 미니맵 크기 — AI 패널의 하단 offset 산정에 사용.
const MINIMAP_W = 300
const MINIMAP_H = 200

export default function Dashboard() {
  const selectedDroneId = useDroneStore((s) => s.selectedDroneId)
  const cameraMode = useDroneStore((s) => s.cameraMode)

  return (
    <div className="relative h-full w-full overflow-hidden bg-dashboard-bg">
      {/* ── 상단 HUD 바 ─────────────────────────────────────── */}
      <DashboardTopBar />

      {/* ── 중앙: LIVE 카메라 피드 (16:9 유지, safe zone 안에 중앙 배치) ── */}
      {/* //* [Modified Code] 풀스크린 object-cover → 16:9 박스로 변경, 다른 HUD 패널과 겹치지 않도록
           safe zone(SAFE.*) 내에서 flex center + aspectRatio 로 자동 피팅 */}
      <div
        className="absolute z-0 flex items-center justify-center"
        style={{
          top: SAFE.top,
          bottom: SAFE.bottom,
          left: SAFE.left,
          right: SAFE.right,
        }}
      >
        <div
          className="relative bg-black rounded-xl overflow-hidden border border-slate-700/60 shadow-2xl"
          style={{
            aspectRatio: '16 / 9',
            width: '100%',
            maxHeight: '100%',
          }}
        >
          <LiveVideoFeed fill />

          {/* 피드 상단 좌측: 드론/카메라 컨텍스트 HUD 뱃지 */}
          <div className="absolute top-3 left-3 pointer-events-none">
            <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-slate-900/70 border border-slate-700/60 backdrop-blur-md shadow-lg">
              <span className="w-1.5 h-1.5 rounded-full bg-red-500 animate-pulse" />
              <Video size={12} className="text-accent-400" />
              <span className="text-[11px] font-mono tracking-wider text-slate-200">
                {selectedDroneId.replace('drone-0', 'DRONE ')} · {CAMERA_LABEL[cameraMode]}
              </span>
              <span className="text-[10px] font-mono text-slate-500">LIVE</span>
            </div>
          </div>
        </div>
      </div>

      {/* ── 좌상단: Thermal Trend PIP (Live Feed PIP 은 메인으로 승격되어 제거됨) ── */}
      <aside className="absolute top-20 left-4 z-20 w-[280px] pointer-events-auto">
        <section className="rounded-xl bg-slate-900/80 border border-slate-700/60 backdrop-blur-md shadow-2xl px-3 py-2.5">
          <div className="flex items-center justify-between mb-2">
            <span className="text-[11px] font-bold uppercase tracking-wider text-white">
              Thermal Trend
            </span>
            <span className="text-[9px] font-mono text-slate-500">last 60s</span>
          </div>
          <div className="h-[110px]">
            <ThermalGraph />
          </div>
        </section>
      </aside>

      {/* ── 좌하단: Drones 패널 (DRONE 01/02 선택) ───────────── */}
      <DronesPanel />

      {/* ── 우하단: 3D 미니맵 (도면/평면도/시뮬레이션 모델링 용) ── */}
      <aside
        className="absolute right-4 bottom-4 z-20 pointer-events-auto"
        style={{ width: MINIMAP_W, height: MINIMAP_H }}
      >
        <div className="flex flex-col h-full rounded-xl bg-slate-900/80 border border-slate-700/60 backdrop-blur-md shadow-2xl overflow-hidden">
          <div className="flex items-center justify-between px-3 py-1.5 border-b border-slate-700/60 flex-shrink-0">
            <span className="text-[11px] font-bold uppercase tracking-wider text-white">
              3D Mini Map
            </span>
            <span className="text-[9px] font-mono text-slate-500">floor plan · sim</span>
          </div>
          <div className="flex-1 relative">
            <BuildingScene />
          </div>
        </div>
      </aside>

      {/* ── 우측: AI Defect Analysis (미니맵과 겹치지 않도록 bottom offset) ── */}
      <aside
        className="absolute top-20 right-4 z-20 w-[360px] pointer-events-auto"
        style={{ bottom: MINIMAP_H + 24 /* minimap(200) + gap(16) + safety(8) */ }}
      >
        <div className="flex flex-col h-full rounded-xl bg-slate-900/80 border border-accent-500/30 backdrop-blur-md shadow-2xl overflow-hidden">
          <div className="px-4 py-3 border-b border-slate-700/60 flex-shrink-0">
            <div className="flex items-center gap-2">
              <Activity className="text-accent-400" size={16} />
              <span className="text-sm font-bold tracking-tight uppercase text-white">
                AI Defect Analysis
              </span>
            </div>
            <div className="flex items-center gap-1.5 mt-1">
              <span className="w-1.5 h-1.5 rounded-full bg-accent-400 animate-pulse" />
              <span className="text-[10px] font-mono text-accent-300 uppercase tracking-wider">
                Real-time detection
              </span>
            </div>
          </div>
          <div className="flex-1 overflow-hidden flex flex-col p-3">
            <DefectPanel />
          </div>
        </div>
      </aside>
    </div>
  )
}
