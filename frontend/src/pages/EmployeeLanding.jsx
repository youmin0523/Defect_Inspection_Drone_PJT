/**
 * EmployeeLanding.jsx  (v2 — 사무실 허브형)
 * 역할: 직원 전용 관제 허브 — "현장 나가기 전/후 사무실에서 쓰는 작업 홈"
 *       - `/employee` 진입 시 최초로 보이는 페이지. `/session/setup` 은 **실제 현장** 에서 쓰는 플로우라 별도.
 *       - 도면 사전 작업 · 보고서 작성 · 현장 관리 · 팀 할당 · 알림 · KPI 요약을 한눈에.
 *       - 랜딩(`/`) 과 톤온톤: `bg-gray-50` 전체 배경 + 흰 카드 + slate-900 배너 + blue/yellow/green accent.
 *
 * //! [Original Code] v1 "Interior Inspection Dashboard" 풀 JSX 목업(실시간 드론 HUD + 평면도 핀 + 결함 분석 사이드패널)
 *   은 이 페이지의 목적(사무실 허브)과 맞지 않아 v2 로 전면 교체함.
 *   v1 원본 전체는 `Vibe_Coding_Log.md` 의 "⏱ 2026-04-16 17:20" 라운드 블록에 아카이브 보관.
 *   (현장 작업용 실시간 HUD 는 `/dashboard` 영역 소관이며, v1 목업의 실내 버전은 추후 `/dashboard/indoor` 신설 시 재활용 예정)
 *
 * 데이터 출처:
 *   - 실데이터(store): 현재 세션 siteName / operatorName / level (sessionStore), defects.length·severity (defectStore),
 *                     mission 시간(droneStore)
 *   - 목업 데이터(MOCK_*): 이번 달 누적치 / 오늘 일정 / 알림 / 팀원 / 최근 활동
 *     → DB 연결 시 MOCK_* 상수를 각 API 훅 호출로 교체 (키·타입 동일하게 유지)
 */

import { useEffect, useMemo } from 'react'
import { Link } from 'react-router-dom'
import {
  AlertTriangle,
  ArrowLeft,
  ArrowRight,
  Bell,
  Building,
  Calendar,
  CheckCircle,
  Clock,
  FileText,
  LogOut,
  MapPin,
  Play,
  TrendingUp,
  Upload,
  UserCheck,
  Users,
  Activity,
  MessageSquare,
} from 'lucide-react'
import useDefectStore from '../store/defectStore.js'
import useDroneStore from '../store/droneStore.js'
import useSessionStore from '../store/sessionStore.js'
import useNotificationStore from '../store/notificationStore.js'
import useChatStore from '../store/chatStore.js'
import NotificationDropdown from '../components/notification/NotificationDropdown.jsx'
import NOTIFICATION_CATEGORIES from '../constants/notificationCategories.js'

/* ──────────────────────────────────────────────────────────────
   상수: 목업 데이터 (DB 연결 시 API 훅으로 교체)
   ────────────────────────────────────────────────────────────── */

// 이번 달 누적 통계 (목업) — `/api/v1/employee/kpi/monthly` 같은 엔드포인트로 교체 예정
const MOCK_MONTHLY_KPI = {
  inspectionsCompleted: 42,
  reportsPublished: 38,
  averageFlightMinutes: 23,
}

// 오늘 일정 — `/api/v1/employee/schedule/today` 로 교체 예정
const MOCK_TODAY_SCHEDULE = [
  { id: 's1', time: '09:00', site: '송파 헬리오시티 102동 1501호', status: 'upcoming', operator: '유민수' },
  { id: 's2', time: '14:00', site: '잠실 리센츠 303동 503호',      status: 'upcoming', operator: '김다연' },
  { id: 's3', time: '16:30', site: '잠실 엘스 208동 2102호',       status: 'upcoming', operator: '박지훈' },
]

// 팀원 현황 및 담당 현장 — `/api/v1/teams/assignments` 로 교체 예정
const MOCK_TEAM_MEMBERS = [
  { id: 't1', name: '유민수', role: '과장',  team: '안전진단 1팀', assignedSite: '송파 헬리오시티 1501호', status: 'office',  initials: 'YS' },
  { id: 't2', name: '김다연', role: '대리',  team: '안전진단 1팀', assignedSite: '잠실 리센츠 503호',      status: 'field',   initials: 'KD' },
  { id: 't3', name: '박지훈', role: '선임',  team: '안전진단 2팀', assignedSite: '잠실 엘스 2102호',       status: 'field',   initials: 'PJ' },
  { id: 't4', name: '이서현', role: '사원',  team: '안전진단 2팀', assignedSite: '미배정',                 status: 'standby', initials: 'LS' },
]

// 최근 활동 — `/api/v1/employee/activities?limit=5` 로 교체 예정
const MOCK_RECENT_ACTIVITIES = [
  { id: 'a1', date: '2026-04-15', kind: 'report',    label: '헬리오시티 1402호 점검 보고서 발행',   actor: '유민수' },
  { id: 'a2', date: '2026-04-15', kind: 'inspection',label: '헬리오시티 1402호 현장 점검 완료',     actor: '유민수' },
  { id: 'a3', date: '2026-04-14', kind: 'upload',    label: '리센츠 503호 평면도 업로드',           actor: '김다연' },
  { id: 'a4', date: '2026-04-13', kind: 'schedule',  label: '엘스 2102호 점검 일정 등록',           actor: '박지훈' },
  { id: 'a5', date: '2026-04-12', kind: 'report',    label: '엘스 1805호 점검 보고서 발행',         actor: '이서현' },
]

// 요일 한국어 매핑
const KR_WEEKDAYS = ['일', '월', '화', '수', '목', '금', '토']

/* ──────────────────────────────────────────────────────────────
   메인 컴포넌트
   ────────────────────────────────────────────────────────────── */

export default function EmployeeLanding() {
  // 실데이터: 현재 세션
  const siteName = useSessionStore((s) => s.siteName)
  const operatorName = useSessionStore((s) => s.operatorName)
  const level = useSessionStore((s) => s.level)

  // 실데이터: 현재 세션 하자
  const defects = useDefectStore((s) => s.defects)
  const severityCounts = useMemo(
    () =>
      defects.reduce(
        (acc, d) => {
          acc[d.severity] = (acc[d.severity] || 0) + 1
          return acc
        },
        { HIGH: 0, MED: 0, LOW: 0 }
      ),
    [defects]
  )

  // 실데이터: 비행 상태
  const missionStatus = useDroneStore((s) => s.missionStatus)
  const missionStartedAt = useDroneStore((s) => s.missionStartedAt)
  const missionEndedAt = useDroneStore((s) => s.missionEndedAt)

  // 파생: 오늘 날짜 포맷 ("2026-04-16 수요일")
  const { dateStr, weekdayLabel } = useMemo(() => {
    const today = new Date()
    return {
      dateStr: today.toISOString().slice(0, 10),
      weekdayLabel: KR_WEEKDAYS[today.getDay()] + '요일',
    }
  }, [])

  // 파생: 현재 세션 비행 지속 시간(분)
  const currentFlightMinutes = useMemo(() => {
    if (!missionStartedAt) return null
    const end = missionEndedAt ?? Date.now()
    return Math.round((end - missionStartedAt) / 60000)
  }, [missionStartedAt, missionEndedAt])

  // 알림 데이터
  const notifications = useNotificationStore((s) => s.notifications)
  const unreadCount = useNotificationStore((s) => s.unreadCount)
  const fetchAll = useNotificationStore((s) => s.fetchAll)
  const fetchUnreadCount = useNotificationStore((s) => s.fetchUnreadCount)

  useEffect(() => { fetchAll(); fetchUnreadCount() }, [fetchAll, fetchUnreadCount])

  // 현재 세션 컨텍스트 요약 문구 ("진행 중 세션 없음" / "송파 헬리오시티 · Level 3 · 비행 중")
  const sessionContextLabel = useMemo(() => {
    if (!siteName) return '진행 중인 세션이 없습니다.'
    const parts = [siteName]
    if (level) parts.push(`Level ${level}`)
    const statusMap = { idle: '대기', flying: '비행 중', ended: '종료' }
    parts.push(statusMap[missionStatus] || '대기')
    return parts.join(' · ')
  }, [siteName, level, missionStatus])

  return (
    <div className="min-h-screen bg-gray-50 text-slate-800 font-sans antialiased">
      <EmployeeHeader operatorName={operatorName} />

      <WelcomeBanner
        operatorName={operatorName}
        dateStr={dateStr}
        weekdayLabel={weekdayLabel}
        todayCount={MOCK_TODAY_SCHEDULE.length}
        pendingReports={unreadCount}
        sessionContextLabel={sessionContextLabel}
      />

      <main className="max-w-7xl mx-auto px-6 md:px-8 py-10 md:py-12 space-y-10 md:space-y-12">
        <QuickActionsSection />

        <KPISection
          monthlyKpi={MOCK_MONTHLY_KPI}
          currentDefectCount={defects.length}
          currentHighSeverity={severityCounts.HIGH}
          currentFlightMinutes={currentFlightMinutes}
        />

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <TodayScheduleSection schedules={MOCK_TODAY_SCHEDULE} />
          <NotificationsSection notifications={notifications} />
        </div>

        <TeamAssignmentsSection members={MOCK_TEAM_MEMBERS} />

        <RecentActivitySection activities={MOCK_RECENT_ACTIVITIES} />
      </main>

    </div>
  )
}

/* ──────────────────────────────────────────────────────────────
   1. 상단 헤더 — 밝은 톤(랜딩 스크롤 후 헤더와 동일 감성)
   ────────────────────────────────────────────────────────────── */

function EmployeeHeader({ operatorName }) {
  const displayName = operatorName || '게스트'
  const initials = (operatorName?.slice(0, 2) || 'GU').toUpperCase()
  const { unreadCount, toggleDropdown } = useNotificationStore()
  const chatUnread = useChatStore((s) => s.unreadTotal)

  return (
    <header className="sticky top-0 z-40 bg-white border-b border-gray-200 shadow-sm">
      <div className="max-w-7xl mx-auto px-6 md:px-8 py-3 flex items-center justify-between gap-4">
        {/* 좌측: 메인으로 + 브랜드 */}
        <div className="flex items-center gap-4 md:gap-6">
          <Link
            to="/"
            className="inline-flex items-center gap-1.5 text-sm font-semibold text-gray-500 hover:text-blue-600 transition"
            title="메인 랜딩으로"
          >
            <ArrowLeft size={16} /> 메인으로
          </Link>
          <div className="h-5 w-px bg-gray-200 hidden md:block" aria-hidden />
          <div className="flex items-center gap-2">
            <Building className="text-blue-600" size={20} />
            <span className="font-extrabold tracking-tight text-slate-800 uppercase text-sm md:text-base">
              DRONE INSPECT <span className="text-blue-600 font-light">Employee</span>
            </span>
          </div>
        </div>

        {/* 우측: 메신저 · 알림 · 프로필 · 로그아웃 */}
        <div className="flex items-center gap-2 md:gap-3">
          {/* 메신저 바로가기 */}
          <Link
            to="/employee/chat"
            className="relative p-2 rounded-full hover:bg-gray-100 transition focus:outline-none focus:ring-2 focus:ring-blue-400"
            aria-label="메신저"
            title="메신저"
          >
            <MessageSquare size={18} className="text-gray-600" />
            {chatUnread > 0 && (
              <span className="absolute -top-0.5 -right-0.5 min-w-[18px] h-[18px] flex items-center justify-center bg-blue-600 text-white text-[10px] font-bold rounded-full px-1 border-2 border-white">
                {chatUnread > 9 ? '9+' : chatUnread}
              </span>
            )}
          </Link>

          {/* 알림 */}
          <div className="relative">
            <button
              type="button"
              className="relative p-2 rounded-full hover:bg-gray-100 transition focus:outline-none focus:ring-2 focus:ring-blue-400"
              aria-label="알림 보기"
              title="알림"
              onClick={toggleDropdown}
            >
              <Bell size={18} className="text-gray-600" />
              {unreadCount > 0 && (
                <span className="absolute -top-0.5 -right-0.5 min-w-[18px] h-[18px] flex items-center justify-center bg-red-500 text-white text-[10px] font-bold rounded-full px-1 border-2 border-white">
                  {unreadCount > 99 ? '99+' : unreadCount}
                </span>
              )}
            </button>
            <NotificationDropdown theme="light" />
          </div>
          <div className="hidden md:flex items-center gap-3 pl-3 border-l border-gray-200">
            <div className="text-right leading-tight">
              <p className="text-sm font-bold text-slate-800">{displayName}</p>
              <p className="text-[11px] text-gray-500">안전진단 1팀</p>
            </div>
            <div className="w-9 h-9 rounded-full bg-blue-600 text-white flex items-center justify-center text-xs font-bold shadow">
              {initials}
            </div>
          </div>
          <button
            type="button"
            className="p-2 rounded-full hover:bg-gray-100 transition focus:outline-none focus:ring-2 focus:ring-blue-400"
            aria-label="로그아웃"
            title="로그아웃 (세션 연동 전 임시 버튼)"
          >
            <LogOut size={18} className="text-gray-500" />
          </button>
        </div>
      </div>
    </header>
  )
}

/* ──────────────────────────────────────────────────────────────
   2. 환영 배너 — 다크 slate-900 (랜딩 ServiceIntroSection 동일 감성)
   ────────────────────────────────────────────────────────────── */

function WelcomeBanner({
  operatorName,
  dateStr,
  weekdayLabel,
  todayCount,
  pendingReports,
  sessionContextLabel,
}) {
  const name = operatorName || '게스트'
  return (
    <section className="relative bg-slate-900 text-white overflow-hidden">
      {/* 점무늬 데코 — 랜딩 Hero 와 동일한 노란 닷 패턴 */}
      <div
        aria-hidden="true"
        className="absolute inset-0 opacity-20 pointer-events-none"
        style={{
          backgroundImage: 'radial-gradient(#fbbf24 1px, transparent 1px)',
          backgroundSize: '30px 30px',
        }}
      />

      <div className="relative max-w-7xl mx-auto px-6 md:px-8 py-10 md:py-14">
        <div className="flex flex-col lg:flex-row lg:items-end lg:justify-between gap-6">
          <div>
            <p className="text-sm text-blue-300 font-mono tracking-widest uppercase mb-2">
              Employee · Office Hub
            </p>
            <h1 className="text-2xl md:text-4xl font-extrabold leading-tight break-keep">
              {name} 과장님, 좋은 하루입니다.
              <br className="hidden md:block" />
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-yellow-400">
                오늘도 안전한 점검을 응원합니다.
              </span>
            </h1>
            <p className="text-gray-300 mt-3 text-sm md:text-base">
              {dateStr} ({weekdayLabel}) · {sessionContextLabel}
            </p>
          </div>

          {/* 오늘 요약 스탯 (배너 내부) */}
          <div className="flex gap-3 md:gap-4">
            <SummaryPill label="오늘 일정" value={`${todayCount}건`} accent="blue" />
            <SummaryPill label="승인 대기 보고서" value={`${pendingReports}건`} accent="yellow" />
          </div>
        </div>
      </div>
    </section>
  )
}

function SummaryPill({ label, value, accent }) {
  const accentClass =
    accent === 'yellow'
      ? 'border-yellow-400/40 bg-yellow-400/10 text-yellow-200'
      : 'border-blue-400/40 bg-blue-400/10 text-blue-200'
  return (
    <div className={`rounded-lg border px-4 py-3 min-w-[120px] ${accentClass}`}>
      <p className="text-[10px] font-bold uppercase tracking-wider opacity-80">{label}</p>
      <p className="text-xl md:text-2xl font-extrabold mt-1">{value}</p>
    </div>
  )
}

/* ──────────────────────────────────────────────────────────────
   3. 퀵 액션 — 4장 카드 (현장 점검 시작은 /session/setup 으로)
   ────────────────────────────────────────────────────────────── */

const QUICK_ACTIONS = [
  {
    key: 'start-inspection',
    title: '현장 점검 시작',
    desc: '현장 정보 입력 → 모델링 → 실시간 관제까지 한 번에 진입합니다.',
    to: '/session/setup',
    icon: Play,
    accent: 'blue',
    primary: true,
  },
  {
    key: 'upload-drawing',
    title: '도면 업로드 · 사전 작업',
    desc: 'CAD/평면도 업로드 및 Mock 3D 모델링까지 한 번에. 현장 세션에서 바로 Load 가능한 사전 모델을 만들어둡니다.',
    to: '/employee/pre-work',
    icon: Upload,
    accent: 'yellow',
  },
  {
    key: 'write-report',
    title: '보고서 작성 · 조회',
    desc: '완료된 점검 세션의 리포트를 작성·발행하거나 이력을 확인합니다.',
    to: '/employee/reports',
    icon: FileText,
    accent: 'green',
  },
  {
    key: 'manage-sites',
    title: '현장 관리',
    desc: '진행 중/예정 현장을 등록·수정하고 담당자를 배정합니다.',
    to: '/employee/sites',
    icon: MapPin,
    accent: 'indigo',
  },
  {
    key: 'analytics',
    title: '분석 · 보고서',
    desc: '하자 경향보고서 및 주간업무보고서를 자동 생성합니다.',
    to: '/employee/analytics',
    icon: TrendingUp,
    accent: 'violet',
  },
  {
    key: 'chat',
    title: '메신저',
    desc: '팀원과 1:1 대화, 그룹 채팅, 팀 채널로 실시간 소통합니다.',
    to: '/employee/chat',
    icon: MessageSquare,
    accent: 'cyan',
  },
]

const ACTION_ACCENT = {
  blue:   { border: 'border-t-4 border-blue-600',   panel: 'bg-blue-50',   iconBg: 'bg-blue-600',   text: 'text-blue-700',   hoverBg: 'group-hover:bg-blue-100' },
  yellow: { border: 'border-t-4 border-yellow-500', panel: 'bg-yellow-50', iconBg: 'bg-yellow-500', text: 'text-yellow-700', hoverBg: 'group-hover:bg-yellow-100' },
  green:  { border: 'border-t-4 border-green-600',  panel: 'bg-green-50',  iconBg: 'bg-green-600',  text: 'text-green-700',  hoverBg: 'group-hover:bg-green-100' },
  indigo: { border: 'border-t-4 border-indigo-600', panel: 'bg-indigo-50', iconBg: 'bg-indigo-600', text: 'text-indigo-700', hoverBg: 'group-hover:bg-indigo-100' },
  violet: { border: 'border-t-4 border-violet-600', panel: 'bg-violet-50', iconBg: 'bg-violet-600', text: 'text-violet-700', hoverBg: 'group-hover:bg-violet-100' },
  cyan:   { border: 'border-t-4 border-cyan-600',   panel: 'bg-cyan-50',   iconBg: 'bg-cyan-600',   text: 'text-cyan-700',   hoverBg: 'group-hover:bg-cyan-100' },
}

function QuickActionsSection() {
  return (
    <section>
      <SectionHeader
        eyebrow="QUICK ACTIONS"
        title="자주 사용하는 작업"
        desc="클릭 한 번으로 사무실 업무와 현장 점검을 시작하세요."
      />
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5 mt-6">
        {QUICK_ACTIONS.map((action) => {
          const style = ACTION_ACCENT[action.accent]
          const Icon = action.icon
          const body = (
            <div className="p-6 flex-1 flex flex-col">
              <h3 className="text-lg font-bold text-slate-800 break-keep">{action.title}</h3>
              <p className="text-sm text-gray-600 mt-2 leading-relaxed break-keep flex-1">
                {action.desc}
              </p>
              <span className={`mt-4 inline-flex items-center gap-1 text-sm font-semibold ${style.text}`}>
                바로가기 <ArrowRight size={14} />
              </span>
            </div>
          )
          const CardRoot = action.disabled ? 'div' : Link
          const rootProps = action.disabled
            ? {
                title: '준비 중 — DB/관리자 권한 기능 연결 후 활성화 예정',
                'aria-disabled': 'true',
                className: `group relative flex flex-col bg-white rounded-xl shadow-md opacity-60 cursor-not-allowed h-full ${style.border}`,
              }
            : {
                to: action.to,
                className: `group relative flex flex-col bg-white rounded-xl shadow-md hover:shadow-xl hover:-translate-y-1 transition duration-300 h-full ${style.border}`,
              }
          return (
            <CardRoot key={action.key} {...rootProps}>
              {/* 상단 아이콘 패널 */}
              <div className={`h-24 flex items-center justify-center ${style.panel} ${style.hoverBg} transition`}>
                <div className={`w-12 h-12 rounded-xl ${style.iconBg} text-white flex items-center justify-center shadow-lg`}>
                  <Icon size={22} />
                </div>
              </div>
              {body}
              {action.primary && (
                <span className="absolute top-3 right-3 text-[10px] font-bold tracking-wider bg-blue-600 text-white px-2 py-0.5 rounded">
                  RECOMMENDED
                </span>
              )}
              {action.disabled && (
                <span className="absolute top-3 right-3 text-[10px] font-bold tracking-wider bg-gray-400 text-white px-2 py-0.5 rounded">
                  SOON
                </span>
              )}
            </CardRoot>
          )
        })}
      </div>
    </section>
  )
}

/* ──────────────────────────────────────────────────────────────
   4. KPI 요약 — 실/목업 혼용 (DB 연결 시 점진 교체)
   ────────────────────────────────────────────────────────────── */

function KPISection({ monthlyKpi, currentDefectCount, currentHighSeverity, currentFlightMinutes }) {
  const cards = [
    {
      key: 'inspections',
      icon: CheckCircle,
      label: '이번 달 점검 완료',
      value: monthlyKpi.inspectionsCompleted,
      unit: '건',
      sub: `발행 보고서 ${monthlyKpi.reportsPublished}건`,
      accent: 'green',
      source: 'mock',
    },
    {
      key: 'defects',
      icon: Activity,
      label: '현재 세션 하자 검출',
      value: currentDefectCount,
      unit: '건',
      sub: '실시간 WebSocket 수신분',
      accent: 'blue',
      source: 'live',
    },
    {
      key: 'critical',
      icon: AlertTriangle,
      label: '심각(HIGH) 하자',
      value: currentHighSeverity,
      unit: '건',
      sub: '즉시 조치 대상',
      accent: 'red',
      source: 'live',
    },
    {
      key: 'flight',
      icon: Clock,
      label: currentFlightMinutes == null ? '이번 달 평균 비행 시간' : '현재 세션 비행 시간',
      value: currentFlightMinutes ?? monthlyKpi.averageFlightMinutes,
      unit: '분',
      sub: currentFlightMinutes == null ? `이번 달 평균` : `미션 시작 이후 누적`,
      accent: 'yellow',
      source: currentFlightMinutes == null ? 'mock' : 'live',
    },
  ]

  return (
    <section>
      <SectionHeader
        eyebrow="KPI SUMMARY"
        title="핵심 성과 지표 (KPI)"
        desc="현재 세션 실데이터와 이번 달 누적 지표를 함께 보여줍니다. (LIVE · 목업 혼용)"
      />
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5 mt-6">
        {cards.map((card) => (
          <KPICard key={card.key} {...card} />
        ))}
      </div>
    </section>
  )
}

const KPI_ACCENT = {
  blue:   { iconBg: 'bg-blue-100',   iconText: 'text-blue-700',   ring: 'ring-blue-100' },
  green:  { iconBg: 'bg-green-100',  iconText: 'text-green-700',  ring: 'ring-green-100' },
  red:    { iconBg: 'bg-red-100',    iconText: 'text-red-700',    ring: 'ring-red-100' },
  yellow: { iconBg: 'bg-yellow-100', iconText: 'text-yellow-700', ring: 'ring-yellow-100' },
}

function KPICard({ icon: Icon, label, value, unit, sub, accent, source }) {
  const style = KPI_ACCENT[accent]
  const sourceBadge =
    source === 'live' ? (
      <span className="inline-flex items-center gap-1 text-[10px] font-bold text-green-700 bg-green-50 px-1.5 py-0.5 rounded">
        <span className="w-1.5 h-1.5 bg-green-500 rounded-full animate-pulse" /> LIVE
      </span>
    ) : (
      <span className="inline-flex items-center gap-1 text-[10px] font-bold text-gray-500 bg-gray-100 px-1.5 py-0.5 rounded">
        MOCK
      </span>
    )
  return (
    <div className={`bg-white rounded-xl shadow-md p-5 ring-1 ${style.ring} hover:shadow-lg transition`}>
      <div className="flex items-start justify-between mb-3">
        <div className={`w-10 h-10 rounded-lg ${style.iconBg} ${style.iconText} flex items-center justify-center`}>
          <Icon size={18} />
        </div>
        {sourceBadge}
      </div>
      <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider">{label}</p>
      <p className="text-3xl font-extrabold text-slate-800 mt-1">
        {value}
        <span className="text-base font-bold text-gray-400 ml-1">{unit}</span>
      </p>
      <p className="text-xs text-gray-500 mt-2">{sub}</p>
    </div>
  )
}

/* ──────────────────────────────────────────────────────────────
   5. 오늘 일정 — 2열 중 좌측
   ────────────────────────────────────────────────────────────── */

function TodayScheduleSection({ schedules }) {
  return (
    <section className="bg-white rounded-xl shadow-md overflow-hidden border-t-4 border-blue-600">
      <div className="px-6 py-4 border-b border-gray-100 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Calendar className="text-blue-600" size={18} />
          <h3 className="font-bold text-slate-800">오늘의 일정</h3>
        </div>
        <span className="text-xs font-semibold text-gray-500">총 {schedules.length}건</span>
      </div>
      <ul className="divide-y divide-gray-100">
        {schedules.map((s) => (
          <li key={s.id} className="px-6 py-4 flex items-center gap-4 hover:bg-gray-50 transition">
            <div className="flex flex-col items-center w-14 shrink-0">
              <span className="text-lg font-extrabold text-blue-700 font-mono">{s.time}</span>
              <span className="text-[10px] text-gray-400 uppercase">KST</span>
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-semibold text-slate-800 truncate break-keep">{s.site}</p>
              <p className="text-xs text-gray-500 mt-0.5">담당 {s.operator}</p>
            </div>
            <Link
              to="/session/setup"
              className="inline-flex items-center gap-1 text-xs font-bold text-blue-700 hover:text-blue-900 transition shrink-0"
              title="이 일정으로 현장 점검 시작"
            >
              점검 시작 <ArrowRight size={12} />
            </Link>
          </li>
        ))}
      </ul>
    </section>
  )
}

/* ──────────────────────────────────────────────────────────────
   6. 알림/공지 — 2열 중 우측 (notificationStore 연동)
   ────────────────────────────────────────────────────────────── */

function formatRelativeTime(timestamp) {
  const diff = Date.now() - timestamp
  const minutes = Math.floor(diff / 60000)
  if (minutes < 1) return '방금 전'
  if (minutes < 60) return `${minutes}분 전`
  const hours = Math.floor(minutes / 60)
  if (hours < 24) return `${hours}시간 전`
  const days = Math.floor(hours / 24)
  if (days < 7) return `${days}일 전`
  const weeks = Math.floor(days / 7)
  if (weeks < 5) return `${weeks}주 전`
  const months = Math.floor(days / 30)
  return `${months}개월 전`
}

function NotificationsSection({ notifications }) {
  return (
    <section className="bg-white rounded-xl shadow-md overflow-hidden border-t-4 border-yellow-500">
      <div className="px-6 py-4 border-b border-gray-100 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Bell className="text-yellow-500" size={18} />
          <h3 className="font-bold text-slate-800">알림 · 공지</h3>
        </div>
        <span className="text-xs font-semibold text-gray-500">최근 {notifications.length}건</span>
      </div>
      <ul className="divide-y divide-gray-100">
        {notifications.slice(0, 6).map((n) => {
          const cat = NOTIFICATION_CATEGORIES[n.category] || NOTIFICATION_CATEGORIES.system
          const Icon = cat.icon
          return (
            <li key={n.id} className={`px-6 py-4 flex items-start gap-4 border-l-4 ${cat.border} hover:bg-gray-50 transition`}>
              <div className={`w-9 h-9 rounded-lg ${cat.lightBg} ${cat.lightText} flex items-center justify-center shrink-0`}>
                <Icon size={16} />
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-0.5">
                  <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded ${cat.lightBg} ${cat.lightText}`}>
                    {cat.label}
                  </span>
                  {!n.is_read && (
                    <span className="w-2 h-2 rounded-full bg-blue-500 shrink-0" />
                  )}
                </div>
                <p className={`text-sm break-keep ${n.is_read ? 'text-slate-500' : 'font-semibold text-slate-800'}`}>{n.title}</p>
                <p className="text-xs text-gray-500 mt-1">{formatRelativeTime(n.created_at)}</p>
              </div>
            </li>
          )
        })}
      </ul>
    </section>
  )
}

/* ──────────────────────────────────────────────────────────────
   7. 팀원 현황 & 담당 현장 할당
   ────────────────────────────────────────────────────────────── */

const MEMBER_STATUS = {
  office:  { label: '사무실', dot: 'bg-blue-500',   text: 'text-blue-700',   bg: 'bg-blue-50' },
  field:   { label: '현장 중', dot: 'bg-green-500',  text: 'text-green-700',  bg: 'bg-green-50' },
  standby: { label: '대기',   dot: 'bg-gray-400',   text: 'text-gray-600',   bg: 'bg-gray-100' },
}

function TeamAssignmentsSection({ members }) {
  return (
    <section>
      <SectionHeader
        eyebrow="TEAM"
        title="팀원 현황 및 담당 현장 할당"
        desc="팀원별 실시간 상태와 현재 담당 중인 현장을 확인하세요."
        rightSlot={
          <span className="inline-flex items-center gap-1.5 text-xs text-gray-500">
            <Users size={14} /> 총 {members.length}명
          </span>
        }
      />
      <div className="bg-white rounded-xl shadow-md overflow-hidden mt-6">
        <div className="overflow-x-auto">
          <table className="min-w-full text-sm">
            <thead className="bg-gray-50 text-gray-500 uppercase text-xs font-semibold tracking-wider">
              <tr>
                <th className="text-left px-6 py-3">팀원</th>
                <th className="text-left px-6 py-3 hidden md:table-cell">팀</th>
                <th className="text-left px-6 py-3">담당 현장</th>
                <th className="text-left px-6 py-3">상태</th>
                <th className="text-right px-6 py-3">액션</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {members.map((m) => {
                const status = MEMBER_STATUS[m.status] || MEMBER_STATUS.standby
                return (
                  <tr key={m.id} className="hover:bg-gray-50 transition">
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-3">
                        <div className="w-9 h-9 rounded-full bg-slate-800 text-white flex items-center justify-center text-xs font-bold shrink-0">
                          {m.initials}
                        </div>
                        <div className="min-w-0">
                          <p className="font-semibold text-slate-800 truncate">{m.name} {m.role}</p>
                          <p className="text-xs text-gray-500 md:hidden">{m.team}</p>
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4 hidden md:table-cell text-gray-600">{m.team}</td>
                    <td className="px-6 py-4 text-gray-700 break-keep">{m.assignedSite}</td>
                    <td className="px-6 py-4">
                      <span className={`inline-flex items-center gap-1.5 text-xs font-semibold px-2.5 py-1 rounded-full ${status.bg} ${status.text}`}>
                        <span className={`w-1.5 h-1.5 rounded-full ${status.dot}`} />
                        {status.label}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-right">
                      <button
                        type="button"
                        className="inline-flex items-center gap-1 text-xs font-bold text-blue-700 hover:text-blue-900 transition"
                        title="담당 현장 재배정 (준비 중)"
                      >
                        <UserCheck size={14} /> 재배정
                      </button>
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      </div>
    </section>
  )
}

/* ──────────────────────────────────────────────────────────────
   8. 최근 활동 타임라인
   ────────────────────────────────────────────────────────────── */

const ACTIVITY_STYLE = {
  report:     { icon: FileText,     iconBg: 'bg-green-100',  iconText: 'text-green-700' },
  inspection: { icon: CheckCircle,  iconBg: 'bg-blue-100',   iconText: 'text-blue-700' },
  upload:     { icon: Upload,       iconBg: 'bg-yellow-100', iconText: 'text-yellow-700' },
  schedule:   { icon: Calendar,     iconBg: 'bg-indigo-100', iconText: 'text-indigo-700' },
}

function RecentActivitySection({ activities }) {
  return (
    <section>
      <SectionHeader
        eyebrow="ACTIVITY"
        title="최근 활동"
        desc="팀 전체의 최근 작업 이력입니다."
      />
      <div className="bg-white rounded-xl shadow-md p-6 mt-6">
        <ol className="relative space-y-5 before:absolute before:top-0 before:bottom-0 before:left-4 before:w-px before:bg-gray-200">
          {activities.map((a) => {
            const style = ACTIVITY_STYLE[a.kind] || ACTIVITY_STYLE.inspection
            const Icon = style.icon
            return (
              <li key={a.id} className="relative pl-12">
                <div className={`absolute left-0 top-0 w-8 h-8 rounded-full ${style.iconBg} ${style.iconText} flex items-center justify-center ring-4 ring-white`}>
                  <Icon size={14} />
                </div>
                <p className="text-sm font-semibold text-slate-800 break-keep">{a.label}</p>
                <p className="text-xs text-gray-500 mt-1">
                  {a.date} · {a.actor}
                </p>
              </li>
            )
          })}
        </ol>
      </div>
    </section>
  )
}

/* ──────────────────────────────────────────────────────────────
   공용 섹션 헤더
   ────────────────────────────────────────────────────────────── */

function SectionHeader({ eyebrow, title, desc, rightSlot }) {
  return (
    <div className="flex flex-col md:flex-row md:items-end md:justify-between gap-2">
      <div>
        <p className="text-xs font-bold text-blue-600 uppercase tracking-[0.15em]">{eyebrow}</p>
        <h2 className="text-xl md:text-2xl font-bold text-slate-800 mt-1 break-keep">{title}</h2>
        {desc && <p className="text-sm text-gray-500 mt-1 break-keep">{desc}</p>}
      </div>
      {rightSlot && <div>{rightSlot}</div>}
    </div>
  )
}
