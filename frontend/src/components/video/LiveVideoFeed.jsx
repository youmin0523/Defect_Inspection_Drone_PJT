/**
 * components/video/LiveVideoFeed.jsx
 * 역할: MJPEG 실시간 영상 스트림 뷰어
 *       - droneStore.cameraMode에 따라 src URL 동적 전환
 *         'rgb'    → VITE_STREAM_RGB_URL
 *         'thermal'→ VITE_STREAM_THERMAL_URL
 *         'blend'  → VITE_STREAM_BLEND_URL
 *       - 브라우저의 <img> 태그가 multipart/x-mixed-replace MJPEG를 네이티브 지원
 *       - 연결 오류 시 "No Signal" 플레이스홀더 표시
 */

import { useState } from 'react'
import useDroneStore from '../../store/droneStore.js'

const STREAM_URLS = {
  rgb:     import.meta.env.VITE_STREAM_RGB_URL     || '/api/v1/stream/rgb',
  thermal: import.meta.env.VITE_STREAM_THERMAL_URL || '/api/v1/stream/thermal',
  blend:   import.meta.env.VITE_STREAM_BLEND_URL   || '/api/v1/stream/blend',
}

const MODE_LABELS = {
  rgb:     'RGB',
  thermal: '열화상',
  blend:   '블렌드',
}

export default function LiveVideoFeed() {
  const cameraMode = useDroneStore((s) => s.cameraMode)
  const [hasError, setHasError] = useState(false)
  const [isLoaded, setIsLoaded] = useState(false)

  const streamUrl = STREAM_URLS[cameraMode] || STREAM_URLS.rgb

  return (
    <div className="relative w-full bg-black rounded overflow-hidden" style={{ aspectRatio: '16/9' }}>
      {/* MJPEG 스트림 */}
      {!hasError ? (
        <img
          key={streamUrl}  // 모드 변경 시 img 재생성하여 새 스트림 연결
          src={streamUrl}
          alt="드론 카메라 피드"
          className="w-full h-full object-contain"
          onLoad={() => setIsLoaded(true)}
          onError={() => setHasError(true)}
        />
      ) : (
        /* No Signal 플레이스홀더 */
        <div className="flex flex-col items-center justify-center w-full h-full text-slate-500">
          <span className="text-4xl mb-2">📷</span>
          <span className="text-sm">No Signal</span>
          <button
            className="mt-2 text-xs text-brand-500 hover:underline"
            onClick={() => setHasError(false)}
          >
            재연결
          </button>
        </div>
      )}

      {/* 로딩 오버레이 */}
      {!isLoaded && !hasError && (
        <div className="absolute inset-0 flex items-center justify-center bg-black/60">
          <div className="w-6 h-6 border-2 border-brand-500 border-t-transparent rounded-full animate-spin" />
        </div>
      )}

      {/* 카메라 모드 배지 */}
      <div className="absolute top-2 left-2 px-2 py-0.5 bg-black/60 rounded text-xs text-white font-mono">
        {MODE_LABELS[cameraMode]}
      </div>

      {/* 녹화 중 점멸 표시 */}
      <div className="absolute top-2 right-2 flex items-center gap-1">
        <span className="w-2 h-2 rounded-full bg-red-500 animate-pulse" />
        <span className="text-xs text-white/70">LIVE</span>
      </div>
    </div>
  )
}
