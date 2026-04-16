/**
 * components/dashboard/DronesPanel.jsx
 * 역할: 풀스크린 HUD 좌하단 "Drones" 패널 — 드론 카드 2개
 *       - DRONE 01 (RGB 카메라) / DRONE 02 (열화상 카메라)
 *       - 클릭 시 droneStore.setSelectedDrone() → 카메라 모드 자동 매핑
 *       - //* [Modified Code v3] (2026-04-16) 폴리시:
 *         - lucide 아이콘으로 이모지 교체 (Camera / Thermometer)
 *         - 신호 세기 바 4-segment (데모용 fake strength)
 *         - 선택된 드론에 펄스 링 glow
 *         - 배터리 바를 색상 분기(low 붉은색) + 모노 타이포로 가독성 개선
 */

import { Camera, Thermometer, Radio } from 'lucide-react'
import useDroneStore from '../../store/droneStore.js'

const DRONES = [
  { id: 'drone-01', label: 'DRONE 01', camera: 'RGB',     icon: Camera,      signalDemo: 4 },
  { id: 'drone-02', label: 'DRONE 02', camera: 'THERMAL', icon: Thermometer, signalDemo: 3 },
]

// 4-segment 신호 세기 바 (1~4)
function SignalBars({ strength = 4, active }) {
  return (
    <span className="inline-flex items-end gap-[2px] h-3">
      {[1, 2, 3, 4].map((lv) => (
        <span
          key={lv}
          className={`w-[3px] rounded-[1px] transition-colors ${
            lv <= strength
              ? active ? 'bg-accent-400' : 'bg-slate-400'
              : 'bg-slate-700'
          }`}
          style={{ height: `${lv * 25}%` }}
        />
      ))}
    </span>
  )
}

export default function DronesPanel() {
  const selectedDroneId = useDroneStore((s) => s.selectedDroneId)
  const setSelectedDrone = useDroneStore((s) => s.setSelectedDrone)
  const telemetry = useDroneStore((s) => s.telemetry)
  const connectionStatus = useDroneStore((s) => s.connectionStatus)

  return (
    <div className="absolute bottom-4 left-4 z-20 w-[360px] rounded-xl bg-slate-900/85 border border-slate-700/60 backdrop-blur-md shadow-2xl pointer-events-auto ring-1 ring-slate-500/5">
      {/* 헤더 */}
      <div className="flex items-center justify-between px-4 py-2.5 border-b border-slate-700/60">
        <div className="flex items-center gap-2">
          <Radio size={12} className="text-accent-400" />
          <span className="text-[11px] font-bold uppercase tracking-[0.25em] text-slate-100">
            Drones
          </span>
          <span className="text-[10px] font-mono text-slate-500 bg-slate-800/60 border border-slate-700 rounded px-1 py-0.5">
            {DRONES.length}
          </span>
        </div>
        <span className={`flex items-center gap-1 text-[10px] font-mono tracking-wider ${
          connectionStatus === 'connected' ? 'text-accent-300' : 'text-slate-500'
        }`}>
          <span className={`w-1.5 h-1.5 rounded-full ${
            connectionStatus === 'connected' ? 'bg-accent-400 animate-pulse' : 'bg-slate-600'
          }`} />
          {connectionStatus === 'connected' ? 'LINK · OK' : 'STANDBY'}
        </span>
      </div>

      {/* 드론 카드 목록 */}
      <div className="grid grid-cols-2 gap-2 p-2">
        {DRONES.map((d) => {
          const isSelected = selectedDroneId === d.id
          const battery = d.id === 'drone-01' ? telemetry.battery : 83
          const batteryLow = battery < 20
          const Icon = d.icon

          return (
            <button
              key={d.id}
              type="button"
              onClick={() => setSelectedDrone(d.id)}
              className={`relative flex flex-col gap-2 rounded-lg border px-3 py-2.5 text-left transition overflow-hidden ${
                isSelected
                  ? 'bg-accent-500/10 border-accent-500/60 shadow-[0_0_14px_rgba(16,185,129,0.3)]'
                  : 'bg-slate-950/50 border-slate-700/60 hover:border-slate-500'
              }`}
              title={`${d.label} — 선택 시 ${d.camera} 카메라로 전환`}
            >
              {/* 선택된 카드에 상단 발광 라인 */}
              {isSelected && (
                <span className="absolute top-0 left-0 right-0 h-[2px] bg-gradient-to-r from-transparent via-accent-400 to-transparent" />
              )}

              {/* 타이틀 행: 아이콘 + 라벨 + ACTIVE 뱃지 */}
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-1.5">
                  <Icon size={12} className={isSelected ? 'text-accent-300' : 'text-slate-400'} />
                  <span className={`text-[11px] font-bold tracking-wider ${
                    isSelected ? 'text-accent-300' : 'text-slate-200'
                  }`}>
                    {d.label}
                  </span>
                </div>
                <span
                  className={`text-[9px] font-bold uppercase tracking-wider px-1.5 py-0.5 rounded ${
                    isSelected
                      ? 'bg-accent-500/20 text-accent-300 border border-accent-500/40'
                      : 'bg-slate-800/60 text-slate-500 border border-slate-700'
                  }`}
                >
                  {isSelected ? 'ACTIVE' : 'IDLE'}
                </span>
              </div>

              {/* 메타 행: 카메라 타입 + 신호 */}
              <div className="flex items-center justify-between text-[10px]">
                <span className="font-mono text-slate-400 tracking-wider">
                  {d.camera} · CAM
                </span>
                <SignalBars strength={d.signalDemo} active={isSelected} />
              </div>

              {/* 배터리 섹션 */}
              <div className="flex flex-col gap-1">
                <div className="flex items-center justify-between text-[10px] font-mono">
                  <span className="text-slate-500 uppercase tracking-wider">Battery</span>
                  <span className={`font-bold tabular-nums ${
                    batteryLow ? 'text-red-400' : isSelected ? 'text-accent-300' : 'text-slate-300'
                  }`}>
                    {battery}%
                  </span>
                </div>
                <div className="w-full bg-slate-800 h-1 rounded-full overflow-hidden">
                  <div
                    className={`h-full transition-all ${
                      batteryLow
                        ? 'bg-red-500'
                        : isSelected
                          ? 'bg-accent-500 shadow-[0_0_6px_rgba(16,185,129,0.6)]'
                          : 'bg-slate-500'
                    }`}
                    style={{ width: `${battery}%` }}
                  />
                </div>
              </div>
            </button>
          )
        })}
      </div>
    </div>
  )
}
