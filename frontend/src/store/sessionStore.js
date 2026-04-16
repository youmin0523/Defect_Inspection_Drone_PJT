/**
 * store/sessionStore.js
 * 역할: 점검 세션 전역 관리 (현장/운용자/날짜/Level/모델링 진행) + localStorage persist
 *       - 직원 전용 진입 시 Setup → Level → Modeling → Dashboard 순서로 채워짐
 *       - persist: 새로고침에도 세션 유지 (File 객체는 직렬화 불가라 메타만, L2 이미지는 base64)
 *       - runMockModeling 유틸과 연동 — 실제 백엔드 연결 전 프로시저럴 시뮬레이션
 *
 * 제약:
 *   - uploadedImageDataUrl (L2 전용) 은 base64 라 localStorage 쿼터(≈5MB) 주의. 큰 파일은 자동 resize 하지 않으므로
 *     데모용 평면도 이미지는 1MB 미만 권장.
 *   - CAD 파일(L1) 은 dashboard 에서 실제 내용이 필요 없으므로 메타(name/size) 만 persist.
 */

import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import { runMockModeling } from '../utils/mockModeling.js'

// 클로저에 러너 cancel 함수 보관 (store state 밖 — persist 되면 안 되는 런타임 참조)
let cancelRunner = null

const todayISO = () => new Date().toISOString().slice(0, 10)

const useSessionStore = create(
  persist(
    (set, get) => ({
      // ── Setup 단계 ──────────────────────────
      siteName: '',
      operatorName: '',
      inspectionDate: todayISO(),

      // ── Level & Modeling 단계 ──────────────
      level: null, // 1 | 2 | 3 | null
      uploadedFileName: null,
      uploadedFileSize: null,
      uploadedImageDataUrl: null, // L2 전용: BuildingMesh 텍스처용 base64 (persist)
      modelStatus: 'pending', // 'pending' | 'modeling' | 'ready'
      modelProgress: 0,
      modelStage: '',

      // //* [Modified Code] 흐름 재설계 (2026-04-16): 모델 소스 구분
      //   'premodel'  = /employee/pre-work 에서 미리 만들어둔 모델을 로드
      //   'drone'     = L3 자율비행 실시간 스캔
      modelSource: null, // 'premodel' | 'drone' | null
      loadedPreModelId: null, // preModelStore.preModels 의 id 참조

      // ── 세션 메타 ──────────────────────────
      sessionId: null,
      startedAt: null,
      finishedAt: null,

      // ── Actions ───────────────────────────

      /** Setup 단계: 현장·운용자·날짜 커밋 */
      setSessionInfo: ({ siteName, operatorName, inspectionDate }) =>
        set({ siteName, operatorName, inspectionDate }),

      /** Level 변경 시 업로드/모델 상태 리셋 (이전 Level 흔적 제거) */
      setLevel: (level) =>
        set({
          level,
          uploadedFileName: null,
          uploadedFileSize: null,
          uploadedImageDataUrl: null,
          modelStatus: 'pending',
          modelProgress: 0,
          modelStage: '',
          modelSource: null,
          loadedPreModelId: null,
        }),

      /**
       * 사전 모델 선택 — /session/level 에서 pre-made model 클릭 시.
       * preModel: { id, level, fileName, imageDataUrl } — preModelStore 에서 꺼낸 엔트리
       * /session/modeling 은 modelSource='premodel' 감지 시 짧은 "로드 중" 애니메이션 후 ready 처리.
       */
      selectPreModel: (preModel) =>
        set({
          level: preModel.level,
          modelSource: 'premodel',
          loadedPreModelId: preModel.id,
          uploadedFileName: preModel.fileName,
          uploadedFileSize: preModel.fileSize ?? 0,
          uploadedImageDataUrl: preModel.imageDataUrl ?? null,
          modelStatus: 'pending',
          modelProgress: 0,
          modelStage: '',
        }),

      /** 드론 자율비행 선택 — L3 고정. */
      selectDroneScan: () =>
        set({
          level: 3,
          modelSource: 'drone',
          loadedPreModelId: null,
          uploadedFileName: null,
          uploadedFileSize: null,
          uploadedImageDataUrl: null,
          modelStatus: 'pending',
          modelProgress: 0,
          modelStage: '',
        }),

      /** L1/L2 업로드 처리 — File 객체 받아 메타만 저장. 이미지면 base64 도 저장 */
      setUploadedFile: async (file) => {
        if (!file) {
          set({
            uploadedFileName: null,
            uploadedFileSize: null,
            uploadedImageDataUrl: null,
          })
          return
        }
        const isImage = file.type?.startsWith('image/')
        let imageDataUrl = null
        if (isImage) {
          imageDataUrl = await readFileAsDataUrl(file)
        }
        set({
          uploadedFileName: file.name,
          uploadedFileSize: file.size,
          uploadedImageDataUrl: imageDataUrl,
        })
      },

      /** 모델링 시작 — mockModeling 러너 기동, onTick 으로 state 업데이트 */
      startModeling: () => {
        if (get().modelStatus === 'modeling') return
        const level = get().level
        if (!level) return
        set({
          modelStatus: 'modeling',
          modelProgress: 0,
          modelStage: '초기화...',
          startedAt: get().startedAt ?? Date.now(),
          sessionId: get().sessionId ?? crypto.randomUUID(),
        })
        cancelRunner?.()
        cancelRunner = runMockModeling({
          level,
          onTick: ({ progress, stage }) => set({ modelProgress: progress, modelStage: stage }),
          onComplete: () => {
            cancelRunner = null
            set({ modelStatus: 'ready', modelProgress: 100 })
          },
        })
      },

      /** 모델링 취소 (뒤로가기 등) */
      cancelModeling: () => {
        cancelRunner?.()
        cancelRunner = null
        set({ modelStatus: 'pending', modelProgress: 0, modelStage: '' })
      },

      /** 비행 종료 시 타임스탬프 기록 (리포트 용) */
      finish: () => set({ finishedAt: Date.now() }),

      /** 전체 초기화 — "새 점검 시작" 버튼에서 호출 */
      reset: () => {
        cancelRunner?.()
        cancelRunner = null
        set({
          siteName: '',
          operatorName: '',
          inspectionDate: todayISO(),
          level: null,
          uploadedFileName: null,
          uploadedFileSize: null,
          uploadedImageDataUrl: null,
          modelStatus: 'pending',
          modelProgress: 0,
          modelStage: '',
          modelSource: null,
          loadedPreModelId: null,
          sessionId: null,
          startedAt: null,
          finishedAt: null,
        })
      },
    }),
    {
      name: 'drone-inspect-session',
      // File 객체/러너 취소 클로저/런타임 전용 필드 제외
      partialize: (state) => ({
        siteName: state.siteName,
        operatorName: state.operatorName,
        inspectionDate: state.inspectionDate,
        level: state.level,
        uploadedFileName: state.uploadedFileName,
        uploadedFileSize: state.uploadedFileSize,
        uploadedImageDataUrl: state.uploadedImageDataUrl,
        modelStatus: state.modelStatus,
        modelSource: state.modelSource,
        loadedPreModelId: state.loadedPreModelId,
        sessionId: state.sessionId,
        startedAt: state.startedAt,
        finishedAt: state.finishedAt,
      }),
    }
  )
)

function readFileAsDataUrl(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => resolve(reader.result)
    reader.onerror = reject
    reader.readAsDataURL(file)
  })
}

export default useSessionStore
