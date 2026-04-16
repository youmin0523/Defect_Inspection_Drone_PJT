/**
 * pages/session/SessionModeling.jsx
 * 역할: 세션 Step 3 — Level 별 업로드/시뮬레이션 + 프로그레스
 *       - L1: CAD 드롭존(.dwg/.dxf/.ifc) → "모델링 시작" → 6~8초 프로그레스
 *       - L2: 이미지 드롭존(image/*) → 썸네일 미리보기 → "모델링 시작" → 6~8초
 *       - L3: "3D 시뮬레이션 시작" 버튼 → 10~12초 프로그레스 (파일 업로드 없음)
 *       - 모델링 완료 시 2초 후 자동으로 /dashboard 진입 (사용자가 완료 상태 확인할 시간 확보)
 */

import { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { ArrowLeft, Play, Loader2, Check } from 'lucide-react'
import FileDropzone from '../../components/session/FileDropzone.jsx'
import ModelingProgress from '../../components/session/ModelingProgress.jsx'
import useSessionStore from '../../store/sessionStore.js'

const LEVEL_CONFIG = {
  1: {
    title: 'CAD 도면 업로드 & 모델링',
    accept: '.dwg,.dxf,.ifc',
    hint: 'DWG · DXF · IFC 파일을 지원합니다',
    needsFile: true,
    startLabel: '모델링 시작',
  },
  2: {
    title: '평면도 이미지 업로드 & 모델링',
    accept: 'image/*',
    hint: 'PNG · JPG · WEBP 등 이미지 파일',
    needsFile: true,
    startLabel: '모델링 시작',
  },
  3: {
    title: '드론 자율비행 3D 시뮬레이션',
    accept: null,
    hint: null,
    needsFile: false,
    startLabel: '3D 시뮬레이션 시작',
  },
}

export default function SessionModeling() {
  const navigate = useNavigate()
  const {
    level,
    uploadedFileName,
    uploadedFileSize,
    uploadedImageDataUrl,
    modelStatus,
    setUploadedFile,
    startModeling,
    cancelModeling,
  } = useSessionStore()

  const cfg = LEVEL_CONFIG[level] ?? LEVEL_CONFIG[3]
  const isModeling = modelStatus === 'modeling'
  const isReady = modelStatus === 'ready'
  const canStart = cfg.needsFile ? !!uploadedFileName : true

  // 모델링 완료 후 잠시 대기 → 대시보드 이동
  useEffect(() => {
    if (!isReady) return
    const t = setTimeout(() => navigate('/dashboard'), 1800)
    return () => clearTimeout(t)
  }, [isReady, navigate])

  const fileMeta = uploadedFileName ? { name: uploadedFileName, size: uploadedFileSize } : null

  return (
    <div className="w-full max-w-2xl bg-slate-900/70 border border-slate-700/60 rounded-2xl shadow-2xl p-8 backdrop-blur-md">
      <h1 className="text-2xl font-bold text-white mb-1">{cfg.title}</h1>
      <p className="text-sm text-slate-400 mb-6 break-keep">
        {cfg.needsFile
          ? '파일을 업로드한 뒤 모델링을 시작하면, 3D 공간 모델이 생성됩니다.'
          : '드론이 현장을 자율비행하며 실시간으로 3D 공간 모델을 생성합니다.'}
      </p>

      {/* L1/L2: 드롭존 */}
      {cfg.needsFile && !isModeling && !isReady && (
        <div className="mb-6">
          <FileDropzone
            accept={cfg.accept}
            hint={cfg.hint}
            file={fileMeta}
            previewUrl={uploadedImageDataUrl}
            onFile={setUploadedFile}
            onClear={() => setUploadedFile(null)}
          />
        </div>
      )}

      {/* L3: 시뮬레이션 안내 박스 */}
      {!cfg.needsFile && !isModeling && !isReady && (
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
                {isReady ? '모델링 완료' : '모델링 진행 중'}
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

        {!isModeling && !isReady && (
          <button
            type="button"
            onClick={startModeling}
            disabled={!canStart}
            className="flex items-center gap-2 px-5 py-2.5 rounded-md bg-accent-500 text-slate-900 font-bold text-sm hover:bg-accent-400 transition shadow-lg disabled:bg-slate-700 disabled:text-slate-500 disabled:cursor-not-allowed"
          >
            <Play size={14} /> {cfg.startLabel}
          </button>
        )}

        {isModeling && (
          <button
            type="button"
            onClick={cancelModeling}
            className="flex items-center gap-2 px-5 py-2.5 rounded-md border border-red-500/50 text-red-300 text-sm hover:bg-red-500/10 transition"
          >
            취소
          </button>
        )}

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
