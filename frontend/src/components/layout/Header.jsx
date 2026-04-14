/**
 * components/layout/Header.jsx
 * 역할: 상단 헤더 컴포넌트
 *       - AeroInspect 로고 및 서비스명
 *       - WebSocket 연결 상태 배지 (connected/disconnected/error)
 *       - 드론 텔레메트리 요약 (고도, 배터리, 비행모드)
 *       - 현재 탐지 건수 요약 표시
 */

import useDroneStore from '../../store/droneStore.js'
import useDefectStore from '../../store/defectStore.js'

const STATUS_CONFIG = {
  connected:    { label: '연결됨',    dotClass: 'bg-green-400 animate-pulse' },
  connecting:   { label: '연결 중...', dotClass: 'bg-yellow-400 animate-pulse' },
  disconnected: { label: '연결 끊김',  dotClass: 'bg-gray-400' },
  error:        { label: '오류',      dotClass: 'bg-red-400 animate-pulse' },
}

export default function Header() {
  const connectionStatus = useDroneStore((s) => s.connectionStatus)
  const telemetry = useDroneStore((s) => s.telemetry)
  
  // defects 배열의 레퍼런스만 구독
  const defects = useDefectStore((s) => s.defects)
  
  // 렌더링 시점에 심각도 카운트 계산
  const severityCounts = defects.reduce(
    (acc, d) => {
      acc[d.severity] = (acc[d.severity] || 0) + 1
      return acc
    },
    { HIGH: 0, MED: 0, LOW: 0 }
  )

  const status = STATUS_CONFIG[connectionStatus] ?? STATUS_CONFIG.disconnected

  return (
    <header className="flex items-center justify-between h-14 px-4 border-b border-dashboard-border bg-dashboard-surface flex-shrink-0">
      {/* 로고 */}
      <div className="flex items-center gap-2">
        <span className="text-xl">🚁</span>
        <span className="font-bold text-white tracking-wide">AeroInspect</span>
        <span className="text-xs text-slate-500 ml-1">v1.3</span>
      </div>

      {/* 드론 텔레메트리 */}
      <div className="flex items-center gap-4 text-xs text-slate-400">
        <TelemetryItem label="고도" value={`${telemetry.z.toFixed(1)}m`} />
        <TelemetryItem label="속도" value={`${telemetry.speed.toFixed(1)}m/s`} />
        <TelemetryItem label="모드" value={telemetry.mode} />
        <TelemetryItem
          label="배터리"
          value={`${telemetry.battery}%`}
          valueClass={telemetry.battery < 20 ? 'text-red-400' : 'text-green-400'}
        />
      </div>

      {/* 탐지 요약 + 연결 상태 */}
      <div className="flex items-center gap-3">
        {/* 심각도 카운터 */}
        <div className="flex items-center gap-2 text-xs">
          <span className="badge-high">{severityCounts.HIGH} HIGH</span>
          <span className="badge-med">{severityCounts.MED} MED</span>
          <span className="badge-low">{severityCounts.LOW} LOW</span>
        </div>

        {/* WS 연결 상태 */}
        <div className="flex items-center gap-1.5 text-xs text-slate-400">
          <span className={`w-2 h-2 rounded-full ${status.dotClass}`} />
          <span>{status.label}</span>
        </div>
      </div>
    </header>
  )
}

function TelemetryItem({ label, value, valueClass = 'text-slate-200' }) {
  return (
    <div className="flex flex-col items-center">
      <span className="text-slate-500 text-[10px] uppercase">{label}</span>
      <span className={`font-mono text-xs ${valueClass}`}>{value}</span>
    </div>
  )
}
