/**
 * pages/session/SessionLevel.jsx
 * 역할: 세션 Step 2 — 이 현장에 맞는 3D 모델 소스 선택
 *
 *   //! [Original Code] v1: L1(CAD) / L2(평면도) / L3(자율비행) 3개 Level 카드로 현장에서 직접 선택
 *   //* [Modified Code] v2: 사용자 프로세스 재정의 반영 — CAD/평면도는 사무실 사전 작업(`/employee/pre-work`)
 *        에서 미리 Mock 모델링해두고, 여기서는 "이 현장 라벨에 매칭되는 사전 모델" 목록 + "드론 자율비행 스캔"(fallback) 선택.
 *
 *   분기:
 *     (A) preModelStore 에 현재 siteName 으로 매칭되는 사전 모델이 1개 이상 → 각각 로드 카드로 노출
 *     (B) 그 외에는 드론 자율비행 카드만 보임(= fallback). 사용자가 사전 작업을 건너뛰고 직행한 경우
 *
 *   선택 시:
 *     - 사전 모델 → sessionStore.selectPreModel(model) (level=1|2 + modelSource='premodel')
 *     - 드론 자율비행 → sessionStore.selectDroneScan() (level=3, modelSource='drone')
 */

import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { FileText, Image as ImageIcon, Navigation, ArrowLeft, ArrowRight, Upload } from 'lucide-react'
import useSessionStore from '../../store/sessionStore.js'
import usePreModelStore from '../../store/preModelStore.js'

export default function SessionLevel() {
  const navigate = useNavigate()
  const siteName = useSessionStore((s) => s.siteName)
  const storedSource = useSessionStore((s) => s.modelSource)
  const storedPreModelId = useSessionStore((s) => s.loadedPreModelId)
  const selectPreModel = useSessionStore((s) => s.selectPreModel)
  const selectDroneScan = useSessionStore((s) => s.selectDroneScan)

  const allPreModels = usePreModelStore((s) => s.preModels)
  const matchingModels = allPreModels.filter((m) => m.siteName === siteName)

  // 기본 선택: 이전에 고른 게 있으면 복원, 없으면 매칭 모델이 있으면 첫 번째, 아니면 드론
  const initialChoice = (() => {
    if (storedSource === 'premodel' && storedPreModelId) {
      const exists = matchingModels.find((m) => m.id === storedPreModelId)
      if (exists) return { type: 'premodel', id: exists.id }
    }
    if (storedSource === 'drone') return { type: 'drone' }
    if (matchingModels.length > 0) return { type: 'premodel', id: matchingModels[0].id }
    return { type: 'drone' }
  })()
  const [choice, setChoice] = useState(initialChoice)

  const handleNext = () => {
    if (choice.type === 'premodel') {
      const model = matchingModels.find((m) => m.id === choice.id)
      if (!model) return
      selectPreModel(model)
    } else {
      selectDroneScan()
    }
    navigate('/session/modeling')
  }

  return (
    <div className="w-full max-w-5xl">
      <header className="text-center mb-8">
        <h1 className="text-2xl font-bold text-white mb-1">모델 소스 선택</h1>
        <p className="text-sm text-slate-400 break-keep">
          {siteName ? (
            <>
              현장 <span className="font-semibold text-white">"{siteName}"</span> 에 사용할 3D 모델을 선택하세요.
            </>
          ) : (
            '현장 정보가 없어 기본 경로만 사용 가능합니다.'
          )}
        </p>
      </header>

      {/* 사전 모델 섹션 */}
      <section className="mb-6">
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-xs font-bold uppercase tracking-[0.15em] text-slate-300">
            사전 작업된 모델 — 매칭 {matchingModels.length}건
          </h2>
          <Link
            to="/employee/pre-work"
            className="text-[11px] text-accent-300 hover:text-accent-200 transition inline-flex items-center gap-1"
            title="사무실 허브로 이동해 새 사전 모델 생성"
          >
            <Upload size={11} /> 사전 작업 바로가기
          </Link>
        </div>

        {matchingModels.length === 0 ? (
          <div className="rounded-xl border border-slate-800 bg-slate-900/40 px-5 py-6 text-center">
            <p className="text-sm text-slate-400">
              이 현장 라벨에 매칭되는 사전 모델이 없습니다.
            </p>
            <p className="text-xs text-slate-500 mt-1">
              사전 모델이 있다면 `/employee/pre-work` 에서 동일한 현장 라벨로 업로드하세요.
              <br />
              없다면 아래 <span className="text-accent-300 font-semibold">드론 자율비행 스캔</span> 으로 진행합니다.
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {matchingModels.map((m) => {
              const selected = choice.type === 'premodel' && choice.id === m.id
              const Icon = m.level === 1 ? FileText : ImageIcon
              return (
                <button
                  key={m.id}
                  type="button"
                  onClick={() => setChoice({ type: 'premodel', id: m.id })}
                  className={`group flex items-start gap-3 rounded-xl border px-4 py-3 text-left transition ${
                    selected
                      ? 'bg-accent-500/10 border-accent-500/60 shadow-[0_0_18px_rgba(16,185,129,0.2)]'
                      : 'bg-slate-900/70 border-slate-700/60 hover:border-slate-500'
                  }`}
                >
                  <div className={`w-11 h-11 rounded-xl flex items-center justify-center shrink-0 ${
                    selected ? 'bg-accent-500/20 text-accent-300' : 'bg-slate-800 text-slate-300'
                  }`}>
                    <Icon size={20} />
                  </div>
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center gap-2 mb-0.5">
                      <span className="text-sm font-bold text-white">
                        {m.level === 1 ? 'CAD 도면' : '평면도 이미지'}
                      </span>
                      <span className={`text-[10px] font-mono px-1.5 py-0.5 rounded ${
                        selected ? 'bg-accent-500/20 text-accent-300 border border-accent-500/40' : 'text-slate-500 border border-slate-700'
                      }`}>
                        L{m.level}
                      </span>
                    </div>
                    <p className="text-xs text-slate-400 truncate font-mono">{m.fileName}</p>
                    <p className="text-[10px] text-slate-500 font-mono mt-1">
                      생성 {new Date(m.createdAt).toLocaleString('ko-KR')}
                    </p>
                  </div>
                </button>
              )
            })}
          </div>
        )}
      </section>

      {/* 드론 자율비행 섹션 (항상 노출) */}
      <section className="mb-8">
        <h2 className="text-xs font-bold uppercase tracking-[0.15em] text-slate-300 mb-3">
          실시간 스캔 (Fallback)
        </h2>
        <button
          type="button"
          onClick={() => setChoice({ type: 'drone' })}
          className={`group w-full flex items-start gap-4 rounded-xl border px-5 py-4 text-left transition ${
            choice.type === 'drone'
              ? 'bg-accent-500/10 border-accent-500/60 shadow-[0_0_18px_rgba(16,185,129,0.2)]'
              : 'bg-slate-900/70 border-slate-700/60 hover:border-slate-500'
          }`}
        >
          <div className={`w-14 h-14 rounded-xl flex items-center justify-center shrink-0 ${
            choice.type === 'drone' ? 'bg-accent-500/20 text-accent-300' : 'bg-slate-800 text-slate-300'
          }`}>
            <Navigation size={22} />
          </div>
          <div className="min-w-0 flex-1">
            <div className="flex items-center gap-2">
              <span className="text-base font-bold text-white">드론 자율비행 스캔</span>
              <span className="text-[10px] font-mono text-slate-500 px-1.5 py-0.5 rounded border border-slate-700">
                L3
              </span>
            </div>
            <p className="text-sm text-slate-400 mt-1 break-keep">
              도면이 없는 현장에서 드론이 실내를 자율비행하며 SLAM 기반으로 3D 모델을 생성합니다.
              모델링 시간 약 10초 (Mock — 실제 구현 시 실시간 스캔).
            </p>
          </div>
        </button>
      </section>

      {/* 컨트롤 */}
      <div className="flex items-center justify-between">
        <button
          type="button"
          onClick={() => navigate('/session/setup')}
          className="flex items-center gap-2 px-4 py-2 rounded-md border border-slate-700 text-slate-300 text-sm hover:bg-slate-800 hover:text-white transition"
        >
          <ArrowLeft size={14} /> 이전
        </button>
        <button
          type="button"
          onClick={handleNext}
          className="flex items-center gap-2 px-5 py-2.5 rounded-md bg-accent-500 text-slate-900 font-bold text-sm hover:bg-accent-400 transition shadow-lg"
        >
          다음
          <ArrowRight size={14} />
        </button>
      </div>
    </div>
  )
}
