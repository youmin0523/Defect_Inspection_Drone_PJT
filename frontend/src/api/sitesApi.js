/**
 * api/sitesApi.js
 * 역할: 현장 관리 CRUD — **API 모양의 추상화**
 *
 *   현재 구현: localStorage (zustand persist 와 별개의 키)
 *   백엔드 연결 후: 이 파일의 함수 body 만 fetch() 호출로 교체하면 호출부(sitesStore / 컴포넌트) 변경 불필요.
 *
 *   예상 백엔드 엔드포인트 (DB 연결 단계에서 신설):
 *     GET    /api/v1/sites           → list
 *     GET    /api/v1/sites/{id}      → detail
 *     POST   /api/v1/sites           → create
 *     PATCH  /api/v1/sites/{id}      → update
 *     DELETE /api/v1/sites/{id}      → delete
 */

const STORAGE_KEY = 'drone-inspect-sites-v2'

/* ── 시드 데이터 ─────────────────────────────────────── */

const SEED_SITES = [
  // B2B — active
  {
    id: 'site-seed-001',
    seq: 1,
    name: '송파 헬리오시티 101동~109동',
    inspection_type: '사전점검',
    address: '서울특별시 송파구 신천동 7-34',
    building_type: '아파트',
    total_area: 84,
    building_count: 9,
    unit_count: 9510,
    client_type: 'B2B',
    client_name: '현대건설',
    client_contact: '02-746-1234',
    contract_start: '2026-03-01',
    contract_end: '2026-06-30',
    status: 'active',
    assigned_members: [
      { id: 't1', name: '유민수', role: '과장' },
      { id: 't2', name: '김다연', role: '대리' },
    ],
    memo: '',
    inspection_count: 12,
    last_inspection_date: '2026-04-15',
    recordings: [],
    created_at: Date.now() - 45 * 86400000,
    updated_at: Date.now() - 3 * 86400000,
  },
  // B2B — pending
  {
    id: 'site-seed-002',
    seq: 2,
    name: '판교 알파돔시티 A·B·C동',
    inspection_type: '정기점검',
    address: '경기도 성남시 분당구 판교역로 235',
    building_type: '오피스',
    total_area: 132,
    building_count: 3,
    unit_count: 480,
    client_type: 'B2B',
    client_name: '삼성물산',
    client_contact: '031-888-5678',
    contract_start: '2026-05-01',
    contract_end: '2026-08-31',
    status: 'pending',
    assigned_members: [
      { id: 't3', name: '이준혁', role: '차장' },
    ],
    memo: '5월 착수 예정, 사전 도면 확보 필요',
    inspection_count: 0,
    last_inspection_date: null,
    recordings: [],
    created_at: Date.now() - 10 * 86400000,
    updated_at: Date.now() - 10 * 86400000,
  },
  // B2B — completed (with recordings)
  {
    id: 'site-seed-003',
    seq: 3,
    name: '위례 자이 201동~205동',
    inspection_type: '사전점검',
    address: '서울특별시 송파구 위례성대로 100',
    building_type: '아파트',
    total_area: 59,
    building_count: 5,
    unit_count: 2200,
    client_type: 'B2B',
    client_name: 'GS건설',
    client_contact: '02-728-9900',
    contract_start: '2025-11-01',
    contract_end: '2026-02-28',
    status: 'completed',
    assigned_members: [
      { id: 't1', name: '유민수', role: '과장' },
      { id: 't4', name: '박서연', role: '사원' },
    ],
    memo: '전 동 점검 완료',
    inspection_count: 24,
    last_inspection_date: '2026-02-25',
    recordings: [
      { id: 'rec-001', date: '2026-02-20', type: 'RGB+Thermal', duration_sec: 754, url: null },
      { id: 'rec-002', date: '2026-02-22', type: 'RGB', duration_sec: 502, url: null },
      { id: 'rec-003', date: '2026-02-25', type: 'RGB+Thermal', duration_sec: 918, url: null },
    ],
    created_at: Date.now() - 160 * 86400000,
    updated_at: Date.now() - 52 * 86400000,
  },
  // B2C — active
  {
    id: 'site-seed-004',
    seq: 4,
    name: '성북구 성북로 23-5',
    inspection_type: '하자점검',
    address: '서울특별시 성북구 성북로 23-5',
    building_type: '단독주택',
    total_area: 42,
    building_count: 1,
    unit_count: 1,
    client_type: 'B2C',
    client_name: '박영호',
    client_contact: '010-3456-7890',
    contract_start: '2026-04-10',
    contract_end: '2026-04-20',
    status: 'active',
    assigned_members: [
      { id: 't2', name: '김다연', role: '대리' },
    ],
    memo: '신축 완공 후 입주 전 하자 점검 의뢰',
    inspection_count: 2,
    last_inspection_date: '2026-04-16',
    recordings: [],
    created_at: Date.now() - 8 * 86400000,
    updated_at: Date.now() - 2 * 86400000,
  },
  // B2C — pending
  {
    id: 'site-seed-005',
    seq: 5,
    name: '강남 래미안 1단지 103동 1201호',
    inspection_type: '입주점검',
    address: '서울특별시 강남구 도곡로 123',
    building_type: '아파트',
    total_area: 109,
    building_count: 1,
    unit_count: 1,
    client_type: 'B2C',
    client_name: '김철수',
    client_contact: '010-1234-5678',
    contract_start: '2026-04-25',
    contract_end: '2026-04-27',
    status: 'pending',
    assigned_members: [],
    memo: '입주 전 사전점검 의뢰 — 담당자 배정 필요',
    inspection_count: 0,
    last_inspection_date: null,
    recordings: [],
    created_at: Date.now() - 3 * 86400000,
    updated_at: Date.now() - 3 * 86400000,
  },
]

/* ── 내부 유틸 ───────────────────────────────────────── */

function readAll() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (!raw) return null // 최초 접근 구분
    const parsed = JSON.parse(raw)
    return Array.isArray(parsed) ? parsed : []
  } catch (err) {
    console.warn('[sitesApi] 파싱 실패, 빈 배열로 복구:', err)
    return []
  }
}

function writeAll(sites) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(sites))
  } catch (err) {
    console.error('[sitesApi] 저장 실패 (localStorage 쿼터 확인):', err)
    throw err
  }
}

/** 최초 접근 시 시드 데이터 삽입 */
function ensureSeeded() {
  const data = readAll()
  if (data === null) {
    writeAll(SEED_SITES)
    return SEED_SITES
  }
  return data
}

const simulateLatency = () => new Promise((r) => setTimeout(r, 80))

/* ── Public API ──────────────────────────────────────── */

/** GET /api/v1/sites */
export async function listSites() {
  await simulateLatency()
  return ensureSeeded().sort((a, b) => (b.updated_at ?? b.created_at) - (a.updated_at ?? a.created_at))
}

/** GET /api/v1/sites/{id} */
export async function getSite(id) {
  await simulateLatency()
  return ensureSeeded().find((s) => s.id === id) ?? null
}

/** POST /api/v1/sites */
export async function createSite(payload) {
  await simulateLatency()
  const sites = ensureSeeded()
  const now = Date.now()
  // seq 자동 증가: 기존 최대 seq + 1
  const maxSeq = sites.reduce((max, s) => Math.max(max, s.seq ?? 0), 0)
  const site = {
    id: crypto.randomUUID(),
    seq: maxSeq + 1,
    inspection_type: '사전점검',
    status: 'pending',
    assigned_members: [],
    memo: '',
    inspection_count: 0,
    last_inspection_date: null,
    recordings: [],
    ...payload,
    created_at: now,
    updated_at: now,
  }
  sites.push(site)
  writeAll(sites)
  return site
}

/** PATCH /api/v1/sites/{id} */
export async function updateSite(id, patch) {
  await simulateLatency()
  const sites = ensureSeeded()
  const idx = sites.findIndex((s) => s.id === id)
  if (idx < 0) throw new Error(`현장을 찾을 수 없습니다: ${id}`)
  const updated = { ...sites[idx], ...patch, id, updated_at: Date.now() }
  sites[idx] = updated
  writeAll(sites)
  return updated
}

/** DELETE /api/v1/sites/{id} */
export async function deleteSite(id) {
  await simulateLatency()
  const next = ensureSeeded().filter((s) => s.id !== id)
  writeAll(next)
  return { ok: true }
}
