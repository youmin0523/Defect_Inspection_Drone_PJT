/**
 * pages/employee/PreWork.jsx
 * 역할: 사무실 사전 작업 — `/employee/pre-work`
 *       - 현장 라벨 입력 → Level 선택(L1 CAD / L2 평면도) → 파일 업로드 → Mock 3D 모델링
 *       - 완료 시 preModelStore 라이브러리에 저장, 후속 세션(/session/level) 에서 로드 가능
 *       - 직원 랜딩(`/employee`) 의 "도면 업로드 · 사전 작업" 카드가 여기로 진입
 *
 *   UX 경계선 (memory: project_ux_boundary_employee_vs_session):
 *     이 페이지는 "사무실" 맥락이다 — 실시간 드론 HUD 나 현장 요소를 섞지 말 것.
 *     `/employee` 랜딩과 같은 톤(흰 배경 + blue/yellow accent + 카드 레이아웃) 유지.
 */

import { useEffect, useRef, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import {
  ArrowLeft,
  Building,
  FileText,
  Image as ImageIcon,
  Upload,
  Play,
  CheckCircle2,
  Loader2,
  Trash2,
} from 'lucide-react'
import FileDropzone from '../../components/session/FileDropzone.jsx'
import { runMockModeling } from '../../utils/mockModeling.js'
import usePreModelStore from '../../store/preModelStore.js'

const LEVEL_CHOICES = [
  {
    level: 1,
    icon: FileText,
    title: 'CAD 도면',
    desc: 'DWG / DXF / IFC 형식의 설계 도면을 업로드합니다.',
    accept: '.dwg,.dxf,.ifc',
    hint: 'DWG · DXF · IFC 파일 지원',
  },
  {
    level: 2,
    icon: ImageIcon,
    title: '평면도 이미지',
    desc: 'PNG / JPG / WEBP 형식의 평면도 스캔 이미지를 업로드합니다.',
    accept: 'image/*',
    hint: 'PNG · JPG · WEBP 이미지',
  },
]

export default function PreWork() {
  const navigate = useNavigate()
  const preModels = usePreModelStore((s) => s.preModels)
  const addPreModel = usePreModelStore((s) => s.addPreModel)
  const removePreModel = usePreModelStore((s) => s.removePreModel)

  const [siteLabel, setSiteLabel] = useState('')
  const [level, setLevel] = useState(1)
  const [fileMeta, setFileMeta] = useState(null) // { name, size, imageDataUrl }
  const [status, setStatus] = useState('pending') // pending | modeling | ready
  const [progress, setProgress] = useState(0)
  const [stage, setStage] = useState('')
  const [error, setError] = useState(null)

  const cancelRef = useRef(null)

  useEffect(() => () => {
    cancelRef.current?.()
    cancelRef.current = null
  }, [])

  const cfg = LEVEL_CHOICES.find((c) => c.level === level) ?? LEVEL_CHOICES[0]
  const canStart = siteLabel.trim().length >= 2 && fileMeta && status === 'pending'

  const handleFile = async (file) => {
    if (!file) {
      setFileMeta(null)
      return
    }
    const isImage = file.type?.startsWith('image/')
    let imageDataUrl = null
    if (isImage) {
      imageDataUrl = await readAsDataUrl(file)
    }
    setFileMeta({
      name: file.name,
      size: file.size,
      imageDataUrl,
    })
    setError(null)
  }

  const handleChangeLevel = (lv) => {
    if (status === 'modeling') return
    setLevel(lv)
    setFileMeta(null)
    setError(null)
  }

  const handleStart = () => {
    if (!canStart) return
    setStatus('modeling')
    setProgress(0)
    setStage('초기화...')
    setError(null)

    cancelRef.current = runMockModeling({
      level,
      onTick: ({ progress, stage }) => {
        setProgress(progress)
        setStage(stage)
      },
      onComplete: () => {
        cancelRef.current = null
        // preModelStore 에 저장
        addPreModel({
          siteName: siteLabel.trim(),
          level,
          fileName: fileMeta.name,
          fileSize: fileMeta.size,
          imageDataUrl: fileMeta.imageDataUrl,
        })
        setStatus('ready')
      },
    })
  }

  const handleCancel = () => {
    cancelRef.current?.()
    cancelRef.current = null
    setStatus('pending')
    setProgress(0)
    setStage('')
  }

  const handleNewEntry = () => {
    // 동일 페이지에서 다른 현장/파일로 추가 모델 생성
    setSiteLabel('')
    setFileMeta(null)
    setStatus('pending')
    setProgress(0)
    setStage('')
    setError(null)
    setLevel(1)
  }

  return (
    <div className="min-h-screen bg-gray-50 text-slate-800 font-sans antialiased">
      {/* 헤더 */}
      <header className="sticky top-0 z-40 bg-white border-b border-gray-200 shadow-sm">
        <div className="max-w-5xl mx-auto px-6 md:px-8 py-3 flex items-center justify-between gap-4">
          <div className="flex items-center gap-4 md:gap-6">
            <Link
              to="/employee"
              className="inline-flex items-center gap-1.5 text-sm font-semibold text-gray-500 hover:text-blue-600 transition"
              title="직원 허브로"
            >
              <ArrowLeft size={16} /> 직원 허브
            </Link>
            <div className="h-5 w-px bg-gray-200 hidden md:block" aria-hidden />
            <div className="flex items-center gap-2">
              <Building className="text-blue-600" size={20} />
              <span className="font-extrabold tracking-tight text-slate-800 uppercase text-sm md:text-base">
                도면 업로드 · 사전 작업
              </span>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-5xl mx-auto px-6 md:px-8 py-10 space-y-8">
        {/* 섹션 헤더 */}
        <section>
          <p className="text-xs font-bold text-blue-600 uppercase tracking-[0.15em]">PRE-WORK</p>
          <h1 className="text-2xl md:text-3xl font-bold text-slate-800 mt-1">
            현장 나가기 전, 도면 기반 3D 모델을 먼저 준비해두세요
          </h1>
          <p className="text-sm text-gray-600 mt-2 break-keep max-w-3xl">
            여기서 만들어둔 모델은 현장에서 <span className="font-semibold text-blue-700">/세션 시작 → Level 선택</span> 화면에 자동 노출되어 즉시 불러올 수 있습니다.
            도면이 없는 현장은 현장에서 드론 자율비행으로 스캔합니다.
          </p>
        </section>

        {/* 모델 생성 카드 */}
        <section className="bg-white rounded-xl shadow-md border-t-4 border-yellow-500 p-6 md:p-8">
          {/* 1) 현장 라벨 */}
          <label className="block mb-6">
            <span className="flex items-center gap-1.5 text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1.5">
              <Building size={13} /> 현장 라벨
            </span>
            <input
              type="text"
              value={siteLabel}
              onChange={(e) => setSiteLabel(e.target.value)}
              placeholder="예: 송파 헬리오시티 102동 1501호"
              disabled={status !== 'pending'}
              className="w-full bg-white border border-gray-300 rounded-md px-3 py-2.5 text-sm text-slate-800 placeholder:text-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-100"
            />
            <p className="text-[11px] text-gray-500 mt-1.5">
              현장 세션에서 동일한 라벨을 입력하면 이 모델이 "Load" 옵션으로 자동 매칭됩니다.
            </p>
          </label>

          {/* 2) Level 선택 */}
          <div className="mb-6">
            <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">
              모델 소스
            </p>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {LEVEL_CHOICES.map((c) => {
                const Icon = c.icon
                const selected = level === c.level
                return (
                  <button
                    key={c.level}
                    type="button"
                    onClick={() => handleChangeLevel(c.level)}
                    disabled={status !== 'pending'}
                    className={`flex items-start gap-3 text-left border rounded-lg px-4 py-3 transition disabled:opacity-60 ${
                      selected
                        ? 'border-blue-500 bg-blue-50 shadow-sm'
                        : 'border-gray-200 bg-white hover:border-gray-300'
                    }`}
                  >
                    <div className={`w-10 h-10 rounded-lg flex items-center justify-center shrink-0 ${
                      selected ? 'bg-blue-600 text-white' : 'bg-gray-100 text-gray-600'
                    }`}>
                      <Icon size={18} />
                    </div>
                    <div className="min-w-0">
                      <div className="flex items-center gap-2">
                        <span className="text-sm font-bold text-slate-800">{c.title}</span>
                        <span className="text-[10px] font-mono text-gray-500">Level {c.level}</span>
                      </div>
                      <p className="text-xs text-gray-600 mt-0.5 break-keep">{c.desc}</p>
                    </div>
                  </button>
                )
              })}
            </div>
          </div>

          {/* 3) 파일 업로드 */}
          {status === 'pending' && (
            <div className="mb-6">
              <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">
                파일 업로드
              </p>
              <FileDropzone
                accept={cfg.accept}
                hint={cfg.hint}
                file={fileMeta ? { name: fileMeta.name, size: fileMeta.size } : null}
                previewUrl={fileMeta?.imageDataUrl}
                onFile={handleFile}
                onClear={() => setFileMeta(null)}
              />
            </div>
          )}

          {/* 4) 진행 중 / 완료 UI */}
          {(status === 'modeling' || status === 'ready') && (
            <div className="mb-6 rounded-xl border border-gray-200 bg-gray-50 p-5">
              <div className="flex items-center gap-3 mb-4">
                {status === 'ready' ? (
                  <div className="w-10 h-10 rounded-full bg-green-100 flex items-center justify-center">
                    <CheckCircle2 size={20} className="text-green-700" />
                  </div>
                ) : (
                  <div className="w-10 h-10 rounded-full bg-blue-100 flex items-center justify-center">
                    <Loader2 size={20} className="text-blue-700 animate-spin" />
                  </div>
                )}
                <div>
                  <div className="text-sm font-bold text-slate-800">
                    {status === 'ready' ? '모델링 완료 — 라이브러리에 저장됨' : '모델링 진행 중'}
                  </div>
                  <div className="text-[11px] text-gray-500 font-mono">
                    {status === 'ready'
                      ? '세션 Level 선택 화면에서 이 현장 라벨을 입력하면 자동 노출됩니다'
                      : '브라우저 탭을 유지해주세요'}
                  </div>
                </div>
              </div>

              <div className="flex items-center justify-between text-xs font-mono mb-2">
                <span className="text-gray-600">{stage || '준비 중...'}</span>
                <span className="text-blue-700 tabular-nums font-bold">{progress}%</span>
              </div>
              <div className="w-full h-2 bg-gray-200 rounded-full overflow-hidden">
                <div
                  className="h-full bg-blue-600 transition-[width] duration-200 ease-out"
                  style={{ width: `${progress}%` }}
                />
              </div>
            </div>
          )}

          {error && (
            <div className="mb-4 text-xs text-red-700 bg-red-50 border border-red-200 rounded-md px-3 py-2">
              {error}
            </div>
          )}

          {/* 5) 액션 버튼 */}
          <div className="flex items-center justify-between">
            <button
              type="button"
              onClick={() => navigate('/employee')}
              className="text-sm text-gray-500 hover:text-slate-800 transition"
            >
              취소하고 허브로
            </button>

            {status === 'pending' && (
              <button
                type="button"
                onClick={handleStart}
                disabled={!canStart}
                className="flex items-center gap-2 px-5 py-2.5 rounded-md bg-blue-600 text-white font-bold text-sm hover:bg-blue-700 transition shadow disabled:bg-gray-300 disabled:text-gray-500 disabled:cursor-not-allowed"
              >
                <Play size={14} /> 모델링 시작
              </button>
            )}

            {status === 'modeling' && (
              <button
                type="button"
                onClick={handleCancel}
                className="flex items-center gap-2 px-5 py-2.5 rounded-md border border-red-300 text-red-700 text-sm hover:bg-red-50 transition"
              >
                취소
              </button>
            )}

            {status === 'ready' && (
              <button
                type="button"
                onClick={handleNewEntry}
                className="flex items-center gap-2 px-5 py-2.5 rounded-md bg-blue-600 text-white font-bold text-sm hover:bg-blue-700 transition shadow"
              >
                <Upload size={14} /> 다른 도면 추가
              </button>
            )}
          </div>
        </section>

        {/* 기존 라이브러리 */}
        <section className="bg-white rounded-xl shadow-md p-6 md:p-8">
          <div className="flex items-center justify-between mb-4">
            <div>
              <p className="text-xs font-bold text-blue-600 uppercase tracking-[0.15em]">LIBRARY</p>
              <h2 className="text-xl font-bold text-slate-800 mt-1">사전 작업 완료 모델 ({preModels.length})</h2>
            </div>
          </div>

          {preModels.length === 0 ? (
            <p className="text-sm text-gray-500 text-center py-6">
              아직 사전 작업된 모델이 없습니다. 상단에서 첫 모델을 생성해보세요.
            </p>
          ) : (
            <ul className="divide-y divide-gray-100">
              {preModels.slice().reverse().map((m) => (
                <li key={m.id} className="py-3 flex items-center gap-3">
                  <div className={`w-10 h-10 rounded-lg flex items-center justify-center shrink-0 ${
                    m.level === 1 ? 'bg-blue-50 text-blue-700' : 'bg-yellow-50 text-yellow-700'
                  }`}>
                    {m.level === 1 ? <FileText size={18} /> : <ImageIcon size={18} />}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-semibold text-slate-800 truncate break-keep">{m.siteName}</p>
                    <p className="text-xs text-gray-500 mt-0.5 font-mono truncate">
                      L{m.level} · {m.fileName} · {new Date(m.createdAt).toLocaleString('ko-KR')}
                    </p>
                  </div>
                  <button
                    type="button"
                    onClick={() => removePreModel(m.id)}
                    title="삭제"
                    className="p-2 rounded hover:bg-red-50 text-gray-400 hover:text-red-600 transition"
                  >
                    <Trash2 size={14} />
                  </button>
                </li>
              ))}
            </ul>
          )}
        </section>
      </main>
    </div>
  )
}

function readAsDataUrl(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => resolve(reader.result)
    reader.onerror = reject
    reader.readAsDataURL(file)
  })
}
