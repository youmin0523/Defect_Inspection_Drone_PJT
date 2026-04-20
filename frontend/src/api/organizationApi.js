/**
 * api/organizationApi.js
 * 역할: 조직(회사) 멤버 관리 — **API 모양의 추상화**
 *
 *   현재 구현: localStorage
 *   백엔드 연결 후: 함수 body 만 fetch() 호출로 교체.
 *
 *   예상 백엔드 엔드포인트:
 *     GET    /api/v1/organizations/my       → 내 조직 정보
 *     GET    /api/v1/organizations/members   → 같은 조직 멤버 목록
 *     POST   /api/v1/organizations           → 조직 생성
 *     POST   /api/v1/organizations/members/invite → 멤버 초대
 *
 *   설계 (혼합 방식):
 *     방식 1 — B2B 회원가입 시 biz_number 자동 매칭 → 같은 조직 소속
 *     방식 2 — admin/owner 가 이메일로 멤버 초대 → invited 상태 → 수락 시 active
 */

const ORG_KEY = 'drone-inspect-organization'
const MEMBERS_KEY = 'drone-inspect-org-members'

/* ── 시드 데이터 ─────────────────────────────────────── */

const SEED_ORGANIZATION = {
  id: 'org-001',
  name: '(주)드론인스펙트',
  biz_number: '1234567890',
  member_count: 4,
  created_at: Date.now() - 365 * 86400000,
}

const SEED_MEMBERS = [
  {
    user_id: 't1',
    name: '유민수',
    email: 'youms@droneinspect.co.kr',
    initials: 'YS',
    role: 'owner',
    department: '안전진단 1팀',
    position: '과장',
    status: 'active',
    online_status: 'online',
  },
  {
    user_id: 't2',
    name: '김다연',
    email: 'kimdy@droneinspect.co.kr',
    initials: 'KD',
    role: 'member',
    department: '안전진단 1팀',
    position: '대리',
    status: 'active',
    online_status: 'online',
  },
  {
    user_id: 't3',
    name: '박지훈',
    email: 'parkjh@droneinspect.co.kr',
    initials: 'PJ',
    role: 'member',
    department: '안전진단 2팀',
    position: '선임',
    status: 'active',
    online_status: 'away',
  },
  {
    user_id: 't4',
    name: '이서현',
    email: 'leesh@droneinspect.co.kr',
    initials: 'LS',
    role: 'member',
    department: '안전진단 2팀',
    position: '사원',
    status: 'active',
    online_status: 'offline',
  },
  {
    user_id: 't5',
    name: '최영진',
    email: 'choiyj@droneinspect.co.kr',
    initials: 'CY',
    role: 'admin',
    department: '드론운용팀',
    position: '팀장',
    status: 'active',
    online_status: 'online',
  },
  {
    user_id: 't6',
    name: '한소희',
    email: 'hansh@droneinspect.co.kr',
    initials: 'HS',
    role: 'member',
    department: '드론운용팀',
    position: '대리',
    status: 'active',
    online_status: 'away',
  },
  {
    user_id: 't7',
    name: '정민재',
    email: 'jungmj@droneinspect.co.kr',
    initials: 'JM',
    role: 'member',
    department: '기술연구소',
    position: '연구원',
    status: 'invited',
    online_status: 'offline',
  },
]

/* ── 내부 유틸 ───────────────────────────────────────── */

function readOrg() {
  try {
    const raw = localStorage.getItem(ORG_KEY)
    return raw ? JSON.parse(raw) : null
  } catch { return null }
}

function readMembers() {
  try {
    const raw = localStorage.getItem(MEMBERS_KEY)
    if (!raw) return null
    return JSON.parse(raw)
  } catch { return [] }
}

function writeMembers(data) {
  localStorage.setItem(MEMBERS_KEY, JSON.stringify(data))
}

function ensureSeeded() {
  if (!readOrg()) localStorage.setItem(ORG_KEY, JSON.stringify(SEED_ORGANIZATION))
  if (!readMembers()) writeMembers(SEED_MEMBERS)
}

const simulateLatency = () => new Promise((r) => setTimeout(r, 60))

/* ── Public API ──────────────────────────────────────── */

/** GET /api/v1/organizations/my */
export async function getMyOrganization() {
  await simulateLatency()
  ensureSeeded()
  return readOrg()
}

/** GET /api/v1/organizations/members */
export async function listOrganizationMembers() {
  await simulateLatency()
  ensureSeeded()
  const org = readOrg()
  const members = readMembers() || []
  return {
    organization: org,
    members: members.filter((m) => m.status === 'active' || m.status === 'invited'),
    total: members.length,
  }
}

/** POST /api/v1/organizations/members/invite */
export async function inviteMember({ email, role = 'member', department, position }) {
  await simulateLatency()
  ensureSeeded()
  const members = readMembers() || []

  // 이미 소속 확인
  if (members.find((m) => m.email === email)) {
    throw new Error('이미 조직에 소속된 사용자입니다.')
  }

  const newMember = {
    user_id: crypto.randomUUID(),
    name: email.split('@')[0],
    email,
    initials: email.slice(0, 2).toUpperCase(),
    role,
    department: department || null,
    position: position || null,
    status: 'invited',
    online_status: 'offline',
  }
  members.push(newMember)
  writeMembers(members)
  return newMember
}

/** PATCH /api/v1/organizations/members/{user_id} */
export async function updateMember(userId, patch) {
  await simulateLatency()
  ensureSeeded()
  const members = readMembers() || []
  const idx = members.findIndex((m) => m.user_id === userId)
  if (idx < 0) throw new Error('멤버를 찾을 수 없습니다.')
  members[idx] = { ...members[idx], ...patch }
  writeMembers(members)
  return members[idx]
}
