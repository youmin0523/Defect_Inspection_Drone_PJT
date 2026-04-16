/**
 * pages/session/SessionLevel.jsx
 * 역할: 세션 Step 2 — Level 1(CAD) / Level 2(평면도) / Level 3(자율비행) 선택
 *       - 3개 카드 나란히, 사용자의 현재 선택은 sessionStore.level 에 반영
 *       - L3 에 "추천" 뱃지 (이번 라운드 주력)
 *       - "다음" 클릭 시 sessionStore.setLevel() 커밋 + /session/modeling 이동
 */

import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { FileText, Image as ImageIcon, Navigation, ArrowLeft, ArrowRight } from 'lucide-react'
import LevelCard from '../../components/session/LevelCard.jsx'
import useSessionStore from '../../store/sessionStore.js'

const LEVELS = [
  {
    level: 1,
    icon: FileText,
    title: 'CAD 도면 업로드',
    subtitle: '정밀도가 가장 높은 방식. DWG/DXF/IFC 도면을 3D 로 변환합니다.',
    bullets: [
      '.dwg / .dxf / .ifc 파일 지원',
      '레이어·치수·재질 정보 보존',
      '정밀도 ★★★',
    ],
  },
  {
    level: 2,
    icon: ImageIcon,
    title: '평면도 이미지 업로드',
    subtitle: '도면 스캔본이나 출력물 사진으로 3D 모델을 역설계합니다.',
    bullets: [
      'PNG / JPG / WEBP 이미지',
      '벽·문 자동 추출 + 벽체 extrude',
      '정밀도 ★★',
    ],
  },
  {
    level: 3,
    icon: Navigation,
    title: '드론 자율비행 스캔',
    subtitle: '도면이 없는 현장에서 드론이 실내를 스캔해 3D 모델을 생성합니다.',
    bullets: [
      'SLAM 기반 실시간 포인트 클라우드',
      '도면 소실·노후 건축물에 최적',
      '정밀도 ★★☆',
    ],
    recommended: true,
  },
]

export default function SessionLevel() {
  const navigate = useNavigate()
  const storedLevel = useSessionStore((s) => s.level)
  const setLevel = useSessionStore((s) => s.setLevel)

  const [selected, setSelected] = useState(storedLevel ?? 3)

  const handleNext = () => {
    setLevel(selected)
    navigate('/session/modeling')
  }

  return (
    <div className="w-full max-w-6xl">
      <header className="text-center mb-8">
        <h1 className="text-2xl font-bold text-white mb-1">Level 선택</h1>
        <p className="text-sm text-slate-400 break-keep">
          보유한 자료에 따라 모델링 방식을 선택하세요. 선택에 따라 다음 단계의 업로드 화면이 달라집니다.
        </p>
      </header>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
        {LEVELS.map((l) => (
          <LevelCard
            key={l.level}
            {...l}
            selected={selected === l.level}
            onSelect={setSelected}
          />
        ))}
      </div>

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
