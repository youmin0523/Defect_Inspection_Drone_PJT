/**
 * api/chatApi.js
 * 역할: 사내 메신저 CRUD — **API 모양의 추상화**
 *
 *   현재 구현: localStorage
 *   백엔드 연결 후: 이 파일의 함수 body 만 fetch() 호출로 교체하면 호출부(chatStore / 컴포넌트) 변경 불필요.
 *
 *   예상 백엔드 엔드포인트:
 *     GET    /api/v1/chat/conversations                   → 대화방 목록
 *     POST   /api/v1/chat/conversations                   → 새 대화방 생성
 *     GET    /api/v1/chat/conversations/{id}/messages      → 메시지 목록
 *     POST   /api/v1/chat/conversations/{id}/messages      → 메시지 전송
 *     PATCH  /api/v1/chat/conversations/{id}/read          → 읽음 처리
 *     GET    /api/v1/chat/unread-counts                    → 미읽음 카운트
 */

const CONV_KEY = 'drone-inspect-conversations'
const MSG_KEY = 'drone-inspect-messages'

/* ── 시드 데이터 ─────────────────────────────────────── */

const SEED_CONVERSATIONS = [
  {
    id: 'conv-ch-team1',
    type: 'channel',
    name: '안전진단 1팀',
    participants: ['t1', 't2'],
    created_by: 'system',
    created_at: Date.now() - 7 * 86400000,
    updated_at: Date.now() - 1 * 3600000,
    last_message: { text: '오늘 102동 15층 외벽 균열 의심 부위 추가 확인 필요합니다.', sender_name: '유민수', created_at: Date.now() - 1 * 3600000 },
  },
  {
    id: 'conv-ch-all',
    type: 'channel',
    name: '전체 공지',
    participants: ['t1', 't2', 't3', 't4'],
    created_by: 'system',
    created_at: Date.now() - 7 * 86400000,
    updated_at: Date.now() - 3 * 3600000,
    last_message: { text: '확인했습니다. 리센츠 현장 진행상황 보고 준비하겠습니다.', sender_name: '김다연', created_at: Date.now() - 3 * 3600000 },
  },
  {
    id: 'conv-dm-t1-t2',
    type: 'dm',
    name: null,
    participants: ['t1', 't2'],
    created_by: 't1',
    created_at: Date.now() - 5 * 86400000,
    updated_at: Date.now() - 30 * 60000,
    last_message: { text: '알겠습니다. 4시까지 완료하겠습니다.', sender_name: '김다연', created_at: Date.now() - 30 * 60000 },
  },
]

const SEED_MESSAGES = [
  // 안전진단 1팀 채널 (5건)
  { id: 'msg-001', conversation_id: 'conv-ch-team1', sender_id: 't1', sender_name: '유민수', sender_initials: 'YS', text: '이번 주 헬리오시티 102동 점검 일정 공유드립니다. 월/수/금 오전 진행 예정입니다.', created_at: Date.now() - 6 * 3600000, is_read: true },
  { id: 'msg-002', conversation_id: 'conv-ch-team1', sender_id: 't2', sender_name: '김다연', sender_initials: 'KD', text: '확인했습니다. 월요일 드론 배터리 3개 충전 완료해두겠습니다.', created_at: Date.now() - 5 * 3600000, is_read: true },
  { id: 'msg-003', conversation_id: 'conv-ch-team1', sender_id: 't1', sender_name: '유민수', sender_initials: 'YS', text: '네 감사합니다. 열화상 카메라 캘리브레이션도 사전 점검 부탁드려요.', created_at: Date.now() - 4.5 * 3600000, is_read: true },
  { id: 'msg-004', conversation_id: 'conv-ch-team1', sender_id: 't2', sender_name: '김다연', sender_initials: 'KD', text: '캘리브레이션 완료했습니다. 외기온 보정값 반영했어요.', created_at: Date.now() - 3 * 3600000, is_read: true },
  { id: 'msg-005', conversation_id: 'conv-ch-team1', sender_id: 't1', sender_name: '유민수', sender_initials: 'YS', text: '수고하셨습니다. 오늘 102동 15층 외벽 균열 의심 부위 추가 확인 필요합니다.', created_at: Date.now() - 1 * 3600000, is_read: true },

  // 전체 공지 채널 (5건)
  { id: 'msg-006', conversation_id: 'conv-ch-all', sender_id: 't1', sender_name: '유민수', sender_initials: 'YS', text: '[공지] 4월 안전교육 일정 안내 — 4/25(금) 14:00 본사 대회의실', created_at: Date.now() - 3 * 86400000, is_read: true },
  { id: 'msg-007', conversation_id: 'conv-ch-all', sender_id: 't3', sender_name: '박지훈', sender_initials: 'PJ', text: '참석 확인했습니다.', created_at: Date.now() - 3 * 86400000 + 3600000, is_read: true },
  { id: 'msg-008', conversation_id: 'conv-ch-all', sender_id: 't4', sender_name: '이서현', sender_initials: 'LS', text: '저도 참석 가능합니다.', created_at: Date.now() - 3 * 86400000 + 7200000, is_read: true },
  { id: 'msg-009', conversation_id: 'conv-ch-all', sender_id: 't1', sender_name: '유민수', sender_initials: 'YS', text: '[공지] 이번 주 주간회의 목요일 10:00으로 변경됩니다.', created_at: Date.now() - 1 * 86400000, is_read: true },
  { id: 'msg-010', conversation_id: 'conv-ch-all', sender_id: 't2', sender_name: '김다연', sender_initials: 'KD', text: '확인했습니다. 리센츠 현장 진행상황 보고 준비하겠습니다.', created_at: Date.now() - 3 * 3600000, is_read: true },

  // DM t1 <-> t2 (5건)
  { id: 'msg-011', conversation_id: 'conv-dm-t1-t2', sender_id: 't2', sender_name: '김다연', sender_initials: 'KD', text: '과장님, 리센츠 303동 503호 균열 사진 보내드립니다. 심각도 HIGH로 분류했습니다.', created_at: Date.now() - 2 * 3600000, is_read: true },
  { id: 'msg-012', conversation_id: 'conv-dm-t1-t2', sender_id: 't1', sender_name: '유민수', sender_initials: 'YS', text: '확인했습니다. 구조부 균열이라 즉시 보수 권고 의견서 작성해주세요.', created_at: Date.now() - 1.5 * 3600000, is_read: true },
  { id: 'msg-013', conversation_id: 'conv-dm-t1-t2', sender_id: 't2', sender_name: '김다연', sender_initials: 'KD', text: '네, 오늘 중으로 보고서 초안 올리겠습니다. 열화상 데이터도 첨부할까요?', created_at: Date.now() - 1 * 3600000, is_read: true },
  { id: 'msg-014', conversation_id: 'conv-dm-t1-t2', sender_id: 't1', sender_name: '유민수', sender_initials: 'YS', text: '네 열화상 + RGB 비교 이미지 같이 넣어주세요. 시공사 제출용이라 상세할수록 좋습니다.', created_at: Date.now() - 45 * 60000, is_read: true },
  { id: 'msg-015', conversation_id: 'conv-dm-t1-t2', sender_id: 't2', sender_name: '김다연', sender_initials: 'KD', text: '알겠습니다. 4시까지 완료하겠습니다.', created_at: Date.now() - 30 * 60000, is_read: true },
]

/* ── 내부 유틸 ───────────────────────────────────────── */

function readConversations() {
  try {
    const raw = localStorage.getItem(CONV_KEY)
    if (!raw) return null
    const parsed = JSON.parse(raw)
    return Array.isArray(parsed) ? parsed : []
  } catch { return [] }
}

function writeConversations(data) {
  localStorage.setItem(CONV_KEY, JSON.stringify(data))
}

function readMessages() {
  try {
    const raw = localStorage.getItem(MSG_KEY)
    if (!raw) return null
    const parsed = JSON.parse(raw)
    return Array.isArray(parsed) ? parsed : []
  } catch { return [] }
}

function writeMessages(data) {
  localStorage.setItem(MSG_KEY, JSON.stringify(data))
}

function ensureSeeded() {
  if (readConversations() === null) writeConversations(SEED_CONVERSATIONS)
  if (readMessages() === null) writeMessages(SEED_MESSAGES)
}

const simulateLatency = () => new Promise((r) => setTimeout(r, 60))

/* ── Public API ──────────────────────────────────────── */

/** GET /api/v1/chat/conversations */
export async function listConversations(userId) {
  await simulateLatency()
  ensureSeeded()
  return readConversations()
    .filter((c) => c.participants.includes(userId))
    .sort((a, b) => b.updated_at - a.updated_at)
}

/** GET /api/v1/chat/conversations/{id}/messages */
export async function getMessages(conversationId) {
  await simulateLatency()
  ensureSeeded()
  return readMessages()
    .filter((m) => m.conversation_id === conversationId)
    .sort((a, b) => a.created_at - b.created_at)
}

/** POST /api/v1/chat/conversations/{id}/messages */
export async function sendMessage({ conversation_id, sender_id, sender_name, sender_initials, sender_profile_image_url, text }) {
  await simulateLatency()
  ensureSeeded()

  const now = Date.now()
  const msg = {
    id: crypto.randomUUID(),
    conversation_id,
    sender_id,
    sender_name,
    sender_initials,
    sender_profile_image_url: sender_profile_image_url || null,
    text,
    created_at: now,
    is_read: true,
  }

  const msgs = readMessages()
  msgs.push(msg)
  writeMessages(msgs)

  // 대화방 updated_at + last_message 갱신
  const convs = readConversations()
  const idx = convs.findIndex((c) => c.id === conversation_id)
  if (idx >= 0) {
    convs[idx].updated_at = now
    convs[idx].last_message = { text, sender_name, created_at: now }
    writeConversations(convs)
  }

  return msg
}

/** POST /api/v1/chat/conversations */
export async function createConversation({ type, name, participants, created_by }) {
  await simulateLatency()
  ensureSeeded()

  const now = Date.now()
  const conv = {
    id: crypto.randomUUID(),
    type,
    name: name || null,
    participants,
    created_by,
    created_at: now,
    updated_at: now,
    last_message: null,
  }

  const convs = readConversations()
  convs.push(conv)
  writeConversations(convs)
  return conv
}

/** PATCH /api/v1/chat/conversations/{id}/read */
export async function markConversationRead(conversationId, userId) {
  await simulateLatency()
  ensureSeeded()

  const msgs = readMessages()
  let updated = 0
  msgs.forEach((m) => {
    if (m.conversation_id === conversationId && m.sender_id !== userId && !m.is_read) {
      m.is_read = true
      updated++
    }
  })
  writeMessages(msgs)
  return { updated }
}

/** GET /api/v1/chat/unread-counts */
export async function getUnreadCounts(userId) {
  await simulateLatency()
  ensureSeeded()

  const msgs = readMessages()
  const convs = readConversations().filter((c) => c.participants.includes(userId))
  const perConversation = {}
  let total = 0

  for (const conv of convs) {
    const count = msgs.filter(
      (m) => m.conversation_id === conv.id && m.sender_id !== userId && !m.is_read
    ).length
    if (count > 0) {
      perConversation[conv.id] = count
      total += count
    }
  }

  return { total, perConversation }
}

/** 기존 DM 대화방 검색 (중복 생성 방지) */
export async function findDMConversation(userId1, userId2) {
  await simulateLatency()
  ensureSeeded()

  return readConversations().find(
    (c) =>
      c.type === 'dm' &&
      c.participants.length === 2 &&
      c.participants.includes(userId1) &&
      c.participants.includes(userId2)
  ) || null
}
