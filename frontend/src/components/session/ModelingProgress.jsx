/**
 * components/session/ModelingProgress.jsx
 * 역할: 모델링 진행 상황 시각화 — 프로그레스 바 + 현재 스테이지 텍스트
 *       - sessionStore 의 modelProgress / modelStage 구독
 *       - 모델링 완료(status='ready') 시 onComplete 콜백 1회 발화
 */

import { useEffect } from 'react'
import useSessionStore from '../../store/sessionStore.js'

export default function ModelingProgress({ onComplete }) {
  const progress = useSessionStore((s) => s.modelProgress)
  const stage = useSessionStore((s) => s.modelStage)
  const status = useSessionStore((s) => s.modelStatus)

  useEffect(() => {
    if (status === 'ready') onComplete?.()
  }, [status, onComplete])

  return (
    <div className="w-full flex flex-col gap-3">
      {/* 스테이지 라벨 */}
      <div className="flex items-center justify-between text-xs font-mono">
        <span className="text-slate-300">{stage || '준비 중...'}</span>
        <span className="text-accent-300 tabular-nums">{progress}%</span>
      </div>

      {/* 프로그레스 바 */}
      <div className="w-full h-2 bg-slate-800 rounded-full overflow-hidden">
        <div
          className="h-full bg-accent-500 transition-[width] duration-200 ease-out shadow-[0_0_8px_rgba(16,185,129,0.6)]"
          style={{ width: `${progress}%` }}
        />
      </div>

      {/* 하단 상태 */}
      <div className="text-[10px] text-slate-500 font-mono uppercase tracking-wider">
        {status === 'ready' ? '● 완료 — 대시보드 이동 대기' : status === 'modeling' ? '● 진행 중' : '● 대기'}
      </div>
    </div>
  )
}
