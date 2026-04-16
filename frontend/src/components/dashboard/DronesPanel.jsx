/**
 * components/dashboard/DronesPanel.jsx
 * 역할: 풀스크린 HUD 좌하단 "Drones" 패널 — 레퍼런스 톤 (컴팩트 드론 카드 2개)
 *       - DRONE 01 (RGB 카메라) / DRONE 02 (열화상 카메라)
 *       - 클릭 시 droneStore.setSelectedDrone() 호출 → 카메라 모드 자동 매핑
 *       - 선택된 드론은 accent(emerald) 강조, 비선택은 slate 톤
 *       - DRONE 01 에만 실시간 텔레메트리 배터리% 바인딩 (단일 드론 전제)
 */

import useDroneStore from '../../store/droneStore.js'

// 드론 카드 메타데이터 — 추후 멀티 드론 지원 시 서버에서 받아서 확장.
const DRONES = [
  { id: 'drone-01', label: 'DRONE 01', camera: 'RGB',     icon: '📷' },
  { id: 'drone-02', label: 'DRONE 02', camera: 'THERMAL', icon: '🌡️' },
]

export default function DronesPanel() {
  const selectedDroneId = useDroneStore((s) => s.selectedDroneId)
  const setSelectedDrone = useDroneStore((s) => s.setSelectedDrone)
  const telemetry = useDroneStore((s) => s.telemetry)
  const connectionStatus = useDroneStore((s) => s.connectionStatus)

  return (
    <div className="absolute bottom-4 left-4 z-20 w-[340px] rounded-xl bg-slate-900/80 border border-slate-700/60 backdrop-blur-md shadow-2xl pointer-events-auto">
      {/* 헤더 */}
      <div className="flex items-center justify-between px-4 py-2.5 border-b border-slate-700/60">
        <div className="flex items-center gap-2">
          <span className="text-[11px] font-bold uppercase tracking-[0.2em] text-slate-200">
            Drones
          </span>
          <span className="text-[10px] font-mono text-slate-500">{DRONES.length}</span>
        </div>
        <span className="text-[10px] font-mono text-slate-500">
          {connectionStatus === 'connected' ? 'LINK OK' : 'STANDBY'}
        </span>
      </div>

      {/* 드론 카드 목록 */}
      <div className="grid grid-cols-2 gap-2 p-2">
        {DRONES.map((d) => {
          const isSelected = selectedDroneId === d.id
          const isActiveDrone = d.id === 'drone-01' && connectionStatus === 'connected'
          // 현재는 DRONE 01 만 실 텔레메트리 연결, DRONE 02 는 데모 값.
          const battery = d.id === 'drone-01' ? telemetry.battery : 83

          return (
            <button
              key={d.id}
              type="button"
              onClick={() => setSelectedDrone(d.id)}
              className={`flex flex-col gap-1.5 rounded-lg border px-3 py-2 text-left transition ${
                isSelected
                  ? 'bg-accent-500/10 border-accent-500/60 shadow-[0_0_12px_rgba(16,185,129,0.25)]'
                  : 'bg-slate-950/40 border-slate-700/60 hover:border-slate-500'
              }`}
              title={`${d.label} — 선택 시 ${d.camera} 카메라로 전환`}
            >
              <div className="flex items-center justify-between">
                <span className={`text-[11px] font-bold tracking-wider ${
                  isSelected ? 'text-accent-300' : 'text-slate-200'
                }`}>
                  {d.icon} {d.label}
                </span>
                <span
                  className={`text-[9px] font-bold uppercase tracking-wider px-1.5 py-0.5 rounded ${
                    isSelected
                      ? 'bg-accent-500/20 text-accent-300 border border-accent-500/40'
                      : isActiveDrone
                        ? 'bg-slate-700/60 text-slate-300 border border-slate-600'
                        : 'bg-slate-800/60 text-slate-500 border border-slate-700'
                  }`}
                >
                  {isSelected ? 'ACTIVE' : 'IDLE'}
                </span>
              </div>

              <div className="flex items-center justify-between text-[10px]">
                <span className="font-mono text-slate-400">{d.camera} CAM</span>
                <span className="font-mono text-slate-300">{battery}%</span>
              </div>

              {/* 배터리 바 */}
              <div className="w-full bg-slate-800 h-1 rounded-full overflow-hidden">
                <div
                  className={`h-full transition-all ${
                    isSelected ? 'bg-accent-500' : 'bg-slate-500'
                  }`}
                  style={{ width: `${battery}%` }}
                />
              </div>
            </button>
          )
        })}
      </div>
    </div>
  )
}
