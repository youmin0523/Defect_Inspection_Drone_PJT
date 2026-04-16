/**
 * pages/session/SessionModeling.jsx
 * 역할: 세션 Step 3 — modelSource 에 따라 2가지 분기
 *
 *   //* [Modified Code v2] (2026-04-16) 흐름 재정의에 맞춰 단순화.
 *
 *   (A) modelSource='premodel' → "사전 모델 로드 중..." 짧은 로드 애니메이션 (2.5초) → ready
 *       - 이미 `/employee/pre-work` 에서 Mock 모델링이 끝났으므로 실제 처리할 일 없음.
 *       - preModelStore 에서 선택된 모델의 메타(파일명/이미지)를 sessionStore 가 이미 복사해둠.
 *
 *   (B) modelSource='drone' → 기존 11초 Mock 시뮬레이션 (runMockModeling level=3)
 *       - SLAM 기반 실시간 스캔 연출 (스테이지 텍스트 4단계)
 *
 *   완료 후 1.8초 대기 → /dashboard 자동 진입
 */

import { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { ArrowLeft, Play, Loader2, Check, Download } from 'lucide-react'
import ModelingProgress from '../../components/session/ModelingProgress.jsx'
import useSessionStore from '../../store/sessionStore.js'

export default function SessionModeling() {
  const navigate = useNavigate()
  const {
    level,
    modelSource,
    uploadedFileName,
    modelStatus,
    startModeling,
    cancelModeling,
  } = useSessionStore()

  const isModeling = modelStatus === 'modeling'
  const isReady = modelStatus === 'ready'

  // 사전 모델: 진입 즉시 "로드 중" 시뮬레이션 자동 시작 (2.5초 후 ready)
  useEffect(() => {
    if (modelSource !== 'premodel') return
    if (modelStatus !== 'pending') return
    // sessionStore.startModeling 은 runMockModeling(level=1/2) 를 7초 돌리므로 여기서는 쓰지 않음.
    // 대신 로컬 2.5초 타이머로 "로드" 연출 후 modelStatus='ready' 강제.
    const setState = useSessionStore.setState
    setState({ modelStatus: 'modeling', modelProgress: 0, modelStage: '메타데이터 검증' })
    const stages = [
      { at: 400,  stage: '모델 파일 검증', pct: 20 },
      { at: 900,  stage: '메시 로드', pct: 55 },
      { at: 1500, stage: '텍스처 매핑', pct: 85 },
      { at: 2100, stage: '완료 처리', pct: 100 },
    ]
    const timers = stages.map((s) =>
      setTimeout(() => setState({ modelProgress: s.pct, modelStage: s.stage }), s.at)
    )
    const done = setTimeout(
      () => setState({ modelStatus: 'ready', modelProgress: 100 }),
      2500
    )
    return () => {
      timers.forEach(clearTimeout)
      clearTimeout(done)
    }
  }, [modelSource, modelStatus])

  // 완료 후 대시보드 자동 이동
  useEffect(() => {
    if (!isReady) return
    const t = setTimeout(() => navigate('/dashboard'), 1800)
    return () => clearTimeout(t)
  }, [isReady, navigate])

  const isPreModel = modelSource === 'premodel'
  const isDrone = modelSource === 'drone'

  return (
    <div className="w-full max-w-2xl bg-slate-900/70 border border-slate-700/60 rounded-2xl shadow-2xl p-8 backdrop-blur-md">
      <h1 className="text-2xl font-bold text-white mb-1">
        {isPreModel ? '사전 모델 로드' : '드론 자율비행 3D 시뮬레이션'}
      </h1>
      <p className="text-sm text-slate-400 mb-6 break-keep">
        {isPreModel
          ? `사무실에서 미리 생성한 Level ${level} 모델을 불러옵니다.`
          : '드론이 현장을 자율비행하며 실시간으로 3D 공간 모델을 생성합니다.'}
      </p>

      {/* 드론 — 사용자 클릭 전 안내 박스 */}
      {isDrone && !isModeling && !isReady && (
        <div className="mb-6 rounded-xl border border-slate-700 bg-slate-950/40 p-5 text-center">
          <div className="w-14 h-14 mx-auto rounded-xl bg-accent-500/10 border border-accent-500/40 flex items-center justify-center mb-3">
            <Play size={22} className="text-accent-400" />
          </div>
          <p className="text-sm text-slate-300 mb-1 font-semibold">시뮬레이션 준비 완료</p>
          <p className="text-xs text-slate-500 break-keep">
            "3D 시뮬레이션 시작" 을 누르면 드론 가상 비행이 시작되며, 약 10초 후 3D 모델이 완성됩니다.
          </p>
        </div>
      )}

      {/* 사전 모델 — 어떤 모델을 로드하는지 정보 표시 */}
      {isPreModel && (
        <div className="mb-6 rounded-xl border border-accent-500/30 bg-accent-500/5 p-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-accent-500/15 border border-accent-500/40 flex items-center justify-center text-accent-300">
              <Download size={18} />
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-xs font-mono text-slate-500 uppercase tracking-wider mb-0.5">
                Loading Pre-built Model · Level {level}
              </p>
              <p className="text-sm text-white font-semibold truncate">{uploadedFileName || '사전 모델'}</p>
            </div>
          </div>
        </div>
      )}

      {/* 진행 중 / 완료 UI */}
      {(isModeling || isReady) && (
        <div className="mb-6 rounded-xl border border-slate-700 bg-slate-950/40 p-5">
          <div className="flex items-center gap-3 mb-4">
            {isReady ? (
              <div className="w-10 h-10 rounded-full bg-accent-500/20 border border-accent-500/60 flex items-center justify-center">
                <Check size={20} className="text-accent-300" />
              </div>
            ) : (
              <div className="w-10 h-10 rounded-full bg-slate-800 flex items-center justify-center">
                <Loader2 size={20} className="text-accent-400 animate-spin" />
              </div>
            )}
            <div>
              <div className="text-sm font-bold text-white">
                {isReady ? '준비 완료' : isPreModel ? '모델 로드 중' : '시뮬레이션 진행 중'}
              </div>
              <div className="text-[11px] text-slate-500 font-mono">
                {isReady ? '잠시 후 대시보드로 이동합니다...' : '브라우저 탭을 유지해주세요'}
              </div>
            </div>
          </div>
          <ModelingProgress />
        </div>
      )}

      {/* 컨트롤 바 */}
      <div className="flex items-center justify-between">
        <button
          type="button"
          onClick={() => {
            if (isModeling) cancelModeling()
            navigate('/session/level')
          }}
          disabled={isReady}
          className="flex items-center gap-2 px-4 py-2 rounded-md border border-slate-700 text-slate-300 text-sm hover:bg-slate-800 hover:text-white transition disabled:opacity-40 disabled:cursor-not-allowed"
        >
          <ArrowLeft size={14} /> 이전
        </button>

        {/* 드론 — 수동 시작 버튼 */}
        {isDrone && !isModeling && !isReady && (
          <button
            type="button"
            onClick={startModeling}
            className="flex items-center gap-2 px-5 py-2.5 rounded-md bg-accent-500 text-slate-900 font-bold text-sm hover:bg-accent-400 transition shadow-lg"
          >
            <Play size={14} /> 3D 시뮬레이션 시작
          </button>
        )}

        {/* 진행 중 */}
        {isModeling && (
          <button
            type="button"
            onClick={cancelModeling}
            disabled={isPreModel /* 사전 모델 로드는 짧아서 취소 미지원 */}
            className="flex items-center gap-2 px-5 py-2.5 rounded-md border border-red-500/50 text-red-300 text-sm hover:bg-red-500/10 transition disabled:opacity-40 disabled:cursor-not-allowed"
          >
            취소
          </button>
        )}

        {/* 완료 */}
        {isReady && (
          <button
            type="button"
            onClick={() => navigate('/dashboard')}
            className="flex items-center gap-2 px-5 py-2.5 rounded-md bg-accent-500 text-slate-900 font-bold text-sm hover:bg-accent-400 transition shadow-lg"
          >
            <Check size={14} /> 대시보드 진입
          </button>
        )}
      </div>
    </div>
  )
}
