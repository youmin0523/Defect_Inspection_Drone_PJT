/**
 * store/chatStore.js
 * 역할: 사내 메신저 상태 관리 — chatApi 래퍼 (Zustand, persist 없음)
 *
 *   persist 를 쓰지 않는 이유: 저장소 SoT 는 api/chatApi.js 의 localStorage 키
 *   (그리고 향후 백엔드 DB). 이 store 는 그 데이터의 "메모리 캐시" 일 뿐.
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
} from '../api/chatApi.js'
import { CURRENT_USER } from '../constants/chatConstants.js'

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
      const convs = await listConversations(CURRENT_USER.id)
      const { total, perConversation } = await getUnreadCounts(CURRENT_USER.id)
      set({ conversations: convs, unreadTotal: total, unreadPerConv: perConversation, loading: false })
    } catch (err) {
      set({ error: err.message, loading: false })
    }
  },

  /** 대화방 선택 → 메시지 로드 + 읽음 처리 */
  selectConversation: async (convId) => {
    set({ activeConversationId: convId, messagesLoading: true })
    try {
      const msgs = await getMessages(convId)
      await markConversationRead(convId, CURRENT_USER.id)
      const { total, perConversation } = await getUnreadCounts(CURRENT_USER.id)
      set({ messages: msgs, messagesLoading: false, unreadTotal: total, unreadPerConv: perConversation })
    } catch (err) {
      set({ error: err.message, messagesLoading: false })
    }
  },

  /** 메시지 전송 */
  sendMessage: async ({ text }) => {
    const { activeConversationId } = get()
    if (!activeConversationId || !text.trim()) return

    // authStore에서 프로필 이미지 URL 가져오기
    const authUser = JSON.parse(localStorage.getItem('user') || '{}')

    const msg = await sendMessage({
      conversation_id: activeConversationId,
      sender_id: CURRENT_USER.id,
      sender_name: CURRENT_USER.name,
      sender_initials: CURRENT_USER.initials,
      sender_profile_image_url: authUser.profile_image_url || null,
      text: text.trim(),
    })

    // 메시지 목록에 추가
    set((s) => ({ messages: [...s.messages, msg] }))

    // 대화방 목록 갱신 (순서 변경 + last_message)
    const convs = await listConversations(CURRENT_USER.id)
    set({ conversations: convs })
  },

  /** 새 대화방 생성 */
  createConversation: async ({ type, name, participants }) => {
    const conv = await createConversation({
      type,
      name,
      participants: [...participants, CURRENT_USER.id],
      created_by: CURRENT_USER.id,
    })
    const convs = await listConversations(CURRENT_USER.id)
    set({ conversations: convs, isNewChatModalOpen: false })
    // 생성 후 바로 선택
    get().selectConversation(conv.id)
    return conv
  },

  /** DM 시작 (기존 DM 있으면 선택, 없으면 생성) */
  startDM: async (targetUserId) => {
    const existing = await findDMConversation(CURRENT_USER.id, targetUserId)
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
    await markConversationRead(convId, CURRENT_USER.id)
    const { total, perConversation } = await getUnreadCounts(CURRENT_USER.id)
    set({ unreadTotal: total, unreadPerConv: perConversation })
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
      const { total, perConversation } = await getUnreadCounts(CURRENT_USER.id)
      set({ unreadTotal: total, unreadPerConv: perConversation })
    } catch {}
  },
}))

export default useChatStore
