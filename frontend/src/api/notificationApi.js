/**
 * api/notificationApi.js
 * 역할: 알림 CRUD — **API 모양의 추상화**
 *
 *   현재 구현: localStorage
 *   백엔드 연결 후: 이 파일의 함수 body 만 fetch() 호출로 교체하면 호출부(notificationStore / 컴포넌트) 변경 불필요.
 *
 *   예상 백엔드 엔드포인트 (DB 연결 단계에서 신설):
 *     GET    /api/v1/notifications              → list (paginated, filterable)
 *     GET    /api/v1/notifications/unread-count  → badge count
 *     PATCH  /api/v1/notifications/{id}/read     → mark single read
 *     PATCH  /api/v1/notifications/read-all      → mark all read
 *     DELETE /api/v1/notifications/{id}          → delete
 */

const STORAGE_KEY = 'drone-inspect-notifications-v1'

/* ── 시드 데이터 (10종 카테고리 커버, 14건) ────────────── */

const SEED_NOTIFICATIONS = [
  // schedule (2)
  {
    id: 'notif-001',
    category: 'schedule',
    title: '내일 09:00 송파 헬리오시티 102동 점검 예정',
    message: '점검 담당: 유민수 과장. 드론 배터리 충전 상태를 확인해주세요.',
    metadata: { site_id: 'site-seed-001' },
    is_read: false,
    created_at: Date.now() - 2 * 3600000,
  },
  {
    id: 'notif-002',
    category: 'schedule',
    title: '잠실 리센츠 303동 점검 일정 변경 (14:00 → 15:30)',
    message: '고객사 요청에 의한 시간 조정입니다. 변경된 일정을 확인해주세요.',
    metadata: { site_id: 'site-seed-001' },
    is_read: false,
    created_at: Date.now() - 5 * 3600000,
  },

  // site (2)
  {
    id: 'notif-003',
    category: 'site',
    title: '판교 알파돔시티 현장 상태 변경: 대기 → 진행 중',
    message: '5월 착수 예정이었으나 조기 착수로 전환되었습니다.',
    metadata: { site_id: 'site-seed-002', link: '/employee/sites' },
    is_read: false,
    created_at: Date.now() - 8 * 3600000,
  },
  {
    id: 'notif-004',
    category: 'site',
    title: '강남 래미안 현장에 담당자로 배정되었습니다',
    message: '김철수 의뢰인, B2C 입주점검. 4/25~4/27 일정.',
    metadata: { site_id: 'site-seed-005', link: '/employee/sites' },
    is_read: true,
    created_at: Date.now() - 24 * 3600000,
  },

  // blueprint (1)
  {
    id: 'notif-005',
    category: 'blueprint',
    title: '헬리오시티 102동 15층 평면도 업로드 완료',
    message: '벽체 추출 처리가 시작되었습니다. 완료 시 다시 알려드립니다.',
    metadata: { link: '/employee/pre-work' },
    is_read: false,
    created_at: Date.now() - 3 * 3600000,
  },

  // work (1)
  {
    id: 'notif-006',
    category: 'work',
    title: '주간업무보고서 제출 마감: 오늘 18:00',
    message: '이번 주 점검 실적 및 이슈 사항을 정리해주세요.',
    metadata: { link: '/employee/analytics' },
    is_read: false,
    created_at: Date.now() - 1 * 3600000,
  },

  // defect (2)
  {
    id: 'notif-007',
    category: 'defect',
    title: '[HIGH] 구조 균열 탐지 — 헬리오시티 1501호',
    message: '심각도 HIGH, 신뢰도 0.92. 구조 안전 즉시 점검 필요.',
    metadata: { site_id: 'site-seed-001', severity: 'HIGH' },
    is_read: false,
    created_at: Date.now() - 30 * 60000,
  },
  {
    id: 'notif-008',
    category: 'defect',
    title: '[HIGH] 벽체 단열 공백 탐지 — 헬리오시티 1501호',
    message: '열화상 분석 결과 B-02 단열 공백 확인. 즉시 보수 필요.',
    metadata: { site_id: 'site-seed-001', severity: 'HIGH' },
    is_read: false,
    created_at: Date.now() - 25 * 60000,
  },

  // report (1)
  {
    id: 'notif-009',
    category: 'report',
    title: '위례 자이 201동 점검 보고서 생성 완료',
    message: 'LLM 기반 보고서가 생성되었습니다. 검토 후 발행해주세요.',
    metadata: { site_id: 'site-seed-003', link: '/employee/reports' },
    is_read: true,
    created_at: Date.now() - 48 * 3600000,
  },

  // drone (1)
  {
    id: 'notif-010',
    category: 'drone',
    title: '드론 #2 배터리 잔량 15% — 교체 필요',
    message: '현재 비행 중 배터리 부족 경고. 착륙 후 즉시 교체 바랍니다.',
    metadata: { drone_id: 'drone-02' },
    is_read: false,
    created_at: Date.now() - 45 * 60000,
  },

  // team (1)
  {
    id: 'notif-011',
    category: 'team',
    title: '이서현 사원이 안전진단 2팀에 배정되었습니다',
    message: '팀원 현황이 업데이트되었습니다.',
    metadata: {},
    is_read: true,
    created_at: Date.now() - 72 * 3600000,
  },

  // system (1)
  {
    id: 'notif-012',
    category: 'system',
    title: 'AI 모델 v2.1 정식 배포 완료',
    message: 'YOLOv8 하자 탐지 모델이 업데이트되었습니다. 신뢰도가 평균 8% 향상.',
    metadata: {},
    is_read: true,
    created_at: Date.now() - 96 * 3600000,
  },

  // compliance (1)
  {
    id: 'notif-013',
    category: 'compliance',
    title: '위례 자이 계약 만료 D-3',
    message: '계약 종료일: 2026-02-28. 정산 및 최종 보고서 제출을 확인해주세요.',
    metadata: { site_id: 'site-seed-003' },
    is_read: true,
    created_at: Date.now() - 120 * 3600000,
  },

  // schedule (추가 — 공지성)
  {
    id: 'notif-014',
    category: 'schedule',
    title: '5월 법정 안전교육 사전 예약 안내',
    message: '전 직원 필수 참석. 교육일시: 2026-05-15 14:00. 인트라넷에서 사전 예약 바랍니다.',
    metadata: {},
    is_read: false,
    created_at: Date.now() - 6 * 86400000,
  },
]

/* ── 내부 유틸 ───────────────────────────────────────── */

function readAll() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (!raw) return null
    const parsed = JSON.parse(raw)
    return Array.isArray(parsed) ? parsed : []
  } catch (err) {
    console.warn('[notificationApi] 파싱 실패, 빈 배열로 복구:', err)
    return []
  }
}

function writeAll(notifications) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(notifications))
  } catch (err) {
    console.error('[notificationApi] 저장 실패 (localStorage 쿼터 확인):', err)
    throw err
  }
}

/** 최초 접근 시 시드 데이터 삽입 */
function ensureSeeded() {
  const data = readAll()
  if (data === null) {
    writeAll(SEED_NOTIFICATIONS)
    return SEED_NOTIFICATIONS
  }
  return data
}

const simulateLatency = () => new Promise((r) => setTimeout(r, 80))

/* ── Public API ──────────────────────────────────────── */

/** GET /api/v1/notifications */
export async function listNotifications({ category, is_read, limit = 20, offset = 0 } = {}) {
  await simulateLatency()
  let items = ensureSeeded()

  // 필터
  if (category != null) items = items.filter((n) => n.category === category)
  if (is_read != null) items = items.filter((n) => n.is_read === is_read)

  // 최신순 정렬
  items.sort((a, b) => b.created_at - a.created_at)

  const total = items.length
  items = items.slice(offset, offset + limit)

  return { items, total, limit, offset }
}

/** GET /api/v1/notifications/unread-count */
export async function getUnreadCount() {
  await simulateLatency()
  const count = ensureSeeded().filter((n) => !n.is_read).length
  return { count }
}

/** PATCH /api/v1/notifications/{id}/read */
export async function markAsRead(id) {
  await simulateLatency()
  const all = ensureSeeded()
  const idx = all.findIndex((n) => n.id === id)
  if (idx < 0) return null
  all[idx] = { ...all[idx], is_read: true }
  writeAll(all)
  return all[idx]
}

/** PATCH /api/v1/notifications/read-all */
export async function markAllAsRead() {
  await simulateLatency()
  const all = ensureSeeded().map((n) => ({ ...n, is_read: true }))
  writeAll(all)
  return { updated: all.filter((n) => n.is_read).length }
}

/** DELETE /api/v1/notifications/{id} */
export async function deleteNotification(id) {
  await simulateLatency()
  const next = ensureSeeded().filter((n) => n.id !== id)
  writeAll(next)
  return { ok: true }
}

/** POST /api/v1/notifications — 테스트/시딩용 (다른 store 에서 알림 생성 시 사용) */
export async function addNotification(payload) {
  await simulateLatency()
  const all = ensureSeeded()
  const notif = {
    id: crypto.randomUUID(),
    is_read: false,
    created_at: Date.now(),
    metadata: {},
    message: null,
    ...payload,
  }
  all.push(notif)
  writeAll(all)
  return notif
}
