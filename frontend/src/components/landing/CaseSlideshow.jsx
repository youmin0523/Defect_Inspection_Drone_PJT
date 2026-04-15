/**
 * CaseSlideshow.jsx
 * 역할: 도입 사례 카드 상단의 크로스페이드 슬라이드쇼
 *       - 이미지 배열을 받아 일정 간격으로 자동 전환
 *       - 하단 미니 점 인디케이터 제공
 *       - 이미지가 없으면 placeholder 텍스트 렌더
 */

import { useEffect, useState } from 'react'

export default function CaseSlideshow({ images, placeholder, interval = 4000, startDelay = 0 }) {
  const [index, setIndex] = useState(0)

  useEffect(() => {
    if (!images || images.length <= 1) return
    let intervalId
    // 카드별 시작 시점을 어긋나게 하여 여러 카드가 동시에 페이드되지 않도록 함
    const timeoutId = setTimeout(() => {
      setIndex((prev) => (prev + 1) % images.length)
      intervalId = setInterval(() => {
        setIndex((prev) => (prev + 1) % images.length)
      }, interval)
    }, startDelay + interval)
    return () => {
      clearTimeout(timeoutId)
      if (intervalId) clearInterval(intervalId)
    }
  }, [images, interval, startDelay])

  if (!images || images.length === 0) {
    return (
      <div className="h-48 bg-slate-200 flex items-center justify-center text-gray-500 group-hover:bg-slate-300 transition">
        {placeholder}
      </div>
    )
  }

  return (
    <div className="relative h-48 overflow-hidden bg-slate-900">
      {images.map((src, i) => (
        <img
          key={src}
          src={src}
          alt=""
          className={`absolute inset-0 w-full h-full object-cover transition-opacity duration-1000 ease-in-out ${
            i === index ? 'opacity-100' : 'opacity-0'
          }`}
        />
      ))}

      {images.length > 1 && (
        <div className="absolute bottom-2 left-1/2 -translate-x-1/2 flex gap-1.5 z-10">
          {images.map((_, i) => (
            <span
              key={i}
              className={`h-1.5 rounded-full transition-all duration-500 ${
                i === index ? 'w-4 bg-white' : 'w-1.5 bg-white/50'
              }`}
            />
          ))}
        </div>
      )}
    </div>
  )
}
