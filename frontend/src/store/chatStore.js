/**
 * store/chatStore.js
 * 역할: 사내 메신저 상태 관리 — chatApi 래퍼 (Zustand, persist 없음)
 *
 *   백엔드 REST API 연동 — JWT 토큰으로 현재 사용자 자동 식별.
 *   CURRENT_USER 는 fallback 용도로만 유지 (authStore.user 우선).
 */

import { create } from 'zustand'
import {
  listConversations,
  getMessages,
  sendMessage,
  createConversation,
  markConversationRead,
  getUnreadCounts,
  findDMConversation,
  leaveConversation as leaveConvApi,
} from '../api/chatApi.js'

/** authStore에서 현재 사용자 가져오기 (store 순환 import 방지) */
function getCurrentUser() {
  const stored = JSON.parse(localStorage.getItem('user') || 'null')
  return stored || { id: null, name: '사용자', initials: '??' }
}

const useChatStore = create((set, get) => ({
  // State
  conversations: [],
  activeConversationId: null,
  messages: [],
  unreadTotal: 0,
  unreadPerConv: {},
  loading: false,
  messagesLoading: false,
  error: null,
  isParticipantPanelOpen: false,
  isNewChatModalOpen: false,
  searchQuery: '',
  filterType: 'all',

  /** 대화방 목록 동기화 */
  fetchConversations: async () => {
    set({ loading: true, error: null })
    try {
      const convs = await listConversations()
      const { total, per_conversation } = await getUnreadCounts()
      set({ conversations: convs, unreadTotal: total, unreadPerConv: per_conversation || {}, loading: false })
    } catch (err) {
      set({ error: err.message, loading: false })
    }
  },

  /** 대화방 선택 → 메시지 로드 + 읽음 처리 */
  selectConversation: async (convId) => {
    set({ activeConversationId: convId, messagesLoading: true })
    try {
      const msgs = await getMessages(convId)
      await markConversationRead(convId)
      const { total, per_conversation } = await getUnreadCounts()
      set({ messages: msgs, messagesLoading: false, unreadTotal: total, unreadPerConv: per_conversation || {} })
    } catch (err) {
      set({ error: err.message, messagesLoading: false })
    }
  },

  /** 메시지 전송 */
  sendMessage: async ({ text }) => {
    const { activeConversationId } = get()
    if (!activeConversationId || !text.trim()) return

    const msg = await sendMessage({
      conversation_id: activeConversationId,
      text: text.trim(),
    })

    // 메시지 목록에 추가
    set((s) => ({ messages: [...s.messages, msg] }))

    // 대화방 목록 갱신 (순서 변경 + last_message)
    const convs = await listConversations()
    set({ conversations: convs })
  },

  /** 새 대화방 생성 */
  createConversation: async ({ type, name, participants }) => {
    const user = getCurrentUser()
    const conv = await createConversation({
      type,
      name,
      participant_ids: [...participants, user.id].filter(Boolean),
    })
    const convs = await listConversations()
    set({ conversations: convs, isNewChatModalOpen: false })
    // 생성 후 바로 선택
    get().selectConversation(conv.id)
    return conv
  },

  /** DM 시작 (기존 DM 있으면 선택, 없으면 생성) */
  startDM: async (targetUserId) => {
    const user = getCurrentUser()
    const existing = await findDMConversation(user.id, targetUserId)
    if (existing) {
      get().selectConversation(existing.id)
      return existing
    }
    return get().createConversation({
      type: 'dm',
      name: null,
      participants: [targetUserId],
    })
  },

  /** 읽음 처리 */
  markRead: async (convId) => {
    await markConversationRead(convId)
    const { total, per_conversation } = await getUnreadCounts()
    set({ unreadTotal: total, unreadPerConv: per_conversation || {} })
  },

  /** 대화방 나가기 */
  leaveConversation: async (convId) => {
    try {
      await leaveConvApi(convId)
      const convs = await listConversations()
      set({ conversations: convs, activeConversationId: null, messages: [] })
    } catch (err) {
      set({ error: err.message })
    }
  },

  // 필터 / 검색
  setFilter: (type) => set({ filterType: type }),
  setSearch: (query) => set({ searchQuery: query }),

  // UI 상태
  toggleParticipantPanel: () => set((s) => ({ isParticipantPanelOpen: !s.isParticipantPanelOpen })),
  openNewChatModal: () => set({ isNewChatModalOpen: true }),
  closeNewChatModal: () => set({ isNewChatModalOpen: false }),

  /** 미읽음 카운트 갱신 (사이드바 뱃지용) */
  refreshUnreadCounts: async () => {
    try {
      const { total, per_conversation } = await getUnreadCounts()
      set({ unreadTotal: total, unreadPerConv: per_conversation || {} })
    } catch {}
  },
}))

export default useChatStore
