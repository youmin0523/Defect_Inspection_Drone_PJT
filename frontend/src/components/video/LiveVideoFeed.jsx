/**
 * components/video/LiveVideoFeed.jsx
 * 역할: MJPEG 실시간 영상 스트림 뷰어
 *       - droneStore.cameraMode에 따라 src URL 동적 전환
 *         'rgb'    → VITE_STREAM_RGB_URL
 *         'thermal'→ VITE_STREAM_THERMAL_URL
 *         'blend'  → VITE_STREAM_BLEND_URL
 *       - 브라우저의 <img> 태그가 multipart/x-mixed-replace MJPEG를 네이티브 지원
 *       - 연결 오류 시 "No Signal" 플레이스홀더 표시
 *       - //* [Modified Code] fill prop: 풀스크린 배경(object-cover, 16/9 강제 해제)으로 사용
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

export default function LiveVideoFeed({ fill = false }) {
  const cameraMode = useDroneStore((s) => s.cameraMode)
  const [hasError, setHasError] = useState(false)
  const [isLoaded, setIsLoaded] = useState(false)

  const streamUrl = STREAM_URLS[cameraMode] || STREAM_URLS.rgb

  // fill 모드: 부모(풀스크린 컨테이너) 를 꽉 채움. 일반 모드: 16/9 고정.
  const containerClass = fill
    ? 'relative w-full h-full bg-black overflow-hidden'
    : 'relative w-full bg-black rounded overflow-hidden'
  const containerStyle = fill ? undefined : { aspectRatio: '16/9' }
  const imgClass = fill
    ? 'w-full h-full object-cover'
    : 'w-full h-full object-contain'

  // fill 모드일 때 No-Signal 플레이스홀더는 "radar grid" 톤으로 — 풀스크린을 까맣게 두지 않기 위함.
  const noSignalBg = fill
    ? 'bg-[radial-gradient(ellipse_at_center,_rgba(15,23,42,0.9)_0%,_rgba(2,6,23,1)_100%)]'
    : ''

  return (
    <div className={containerClass} style={containerStyle}>
      {/* MJPEG 스트림 */}
      {!hasError ? (
        <img
          key={streamUrl}
          src={streamUrl}
          alt="드론 카메라 피드"
          className={imgClass}
          onLoad={() => setIsLoaded(true)}
          onError={() => setHasError(true)}
        />
      ) : (
        /* No Signal 플레이스홀더 */
        <div className={`flex flex-col items-center justify-center w-full h-full text-slate-500 ${noSignalBg}`}>
          {fill && (
            /* 풀스크린 모드: 은은한 레이더 그리드 오버레이 */
            <div className="absolute inset-0 opacity-[0.08] bg-[linear-gradient(0deg,transparent_24%,rgba(16,185,129,0.6)_25%,rgba(16,185,129,0.6)_26%,transparent_27%,transparent_74%,rgba(16,185,129,0.6)_75%,rgba(16,185,129,0.6)_76%,transparent_77%),linear-gradient(90deg,transparent_24%,rgba(16,185,129,0.6)_25%,rgba(16,185,129,0.6)_26%,transparent_27%,transparent_74%,rgba(16,185,129,0.6)_75%,rgba(16,185,129,0.6)_76%,transparent_77%)] bg-[size:56px_56px]" />
          )}
          <span className={fill ? 'text-6xl mb-3 opacity-40' : 'text-4xl mb-2'}>📷</span>
          <span className={fill ? 'text-sm font-mono tracking-widest uppercase text-slate-400' : 'text-sm'}>
            {fill ? 'Signal Standby' : 'No Signal'}
          </span>
          {fill && (
            <span className="text-[10px] font-mono text-slate-600 mt-1">
              {MODE_LABELS[cameraMode]} · {cameraMode.toUpperCase()} CAM
            </span>
          )}
          <button
            className="mt-3 text-xs text-brand-500 hover:underline"
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

      {/* fill 모드에서는 상단 뱃지/LIVE 표시는 Dashboard 의 자체 HUD 에서 처리 — 여기서는 숨김 */}
      {!fill && (
        <>
          <div className="absolute top-2 left-2 px-2 py-0.5 bg-black/60 rounded text-xs text-white font-mono">
            {MODE_LABELS[cameraMode]}
          </div>
          <div className="absolute top-2 right-2 flex items-center gap-1">
            <span className="w-2 h-2 rounded-full bg-red-500 animate-pulse" />
            <span className="text-xs text-white/70">LIVE</span>
          </div>
        </>
      )}
    </div>
  )
}
