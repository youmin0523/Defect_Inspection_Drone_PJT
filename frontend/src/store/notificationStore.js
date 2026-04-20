/**
 * store/notificationStore.js
 * 역할: 알림 상태 관리 — notificationApi 래퍼 (Zustand, persist 없음)
 *
 *   persist 를 쓰지 않는 이유: 저장소 SoT(Source of Truth) 는 api/notificationApi.js 의 localStorage 키
 *   (그리고 향후 백엔드 DB). 이 store 는 그 데이터의 "메모리 캐시" 일 뿐.
 *
 *   백엔드 연결 시: notificationApi 만 교체하면 여기는 변경 없음.
 */

import { create } from 'zustand'
import {
  listNotifications,
  getUnreadCount,
  markAsRead,
  markAllAsRead,
  deleteNotification,
} from '../api/notificationApi.js'

const useNotificationStore = create((set, get) => ({
  // State
  notifications: [],
  unreadCount: 0,
  loading: false,
  error: null,
  isDropdownOpen: false,

  /** 전체 목록 동기화 — 드롭다운 열릴 때 호출 */
  fetchAll: async (filters = {}) => {
    set({ loading: true, error: null })
    try {
      const { items } = await listNotifications(filters)
      set({ notifications: items, loading: false })
    } catch (err) {
      set({ error: err.message, loading: false })
    }
  },

  /** 미읽음 카운트 — 뱃지 표시용 */
  fetchUnreadCount: async () => {
    try {
      const { count } = await getUnreadCount()
      set({ unreadCount: count })
    } catch (err) {
      console.warn('[notificationStore] unread count fetch failed:', err)
    }
  },

  /** 단건 읽음 처리 */
  markRead: async (id) => {
    await markAsRead(id)
    set((state) => ({
      notifications: state.notifications.map((n) =>
        n.id === id ? { ...n, is_read: true } : n
      ),
      unreadCount: Math.max(0, state.unreadCount - 1),
    }))
  },

  /** 전체 읽음 처리 */
  markAllRead: async () => {
    await markAllAsRead()
    set((state) => ({
      notifications: state.notifications.map((n) => ({ ...n, is_read: true })),
      unreadCount: 0,
    }))
  },

  /** 단건 삭제 */
  remove: async (id) => {
    const wasUnread = get().notifications.find((n) => n.id === id && !n.is_read)
    await deleteNotification(id)
    set((state) => ({
      notifications: state.notifications.filter((n) => n.id !== id),
      unreadCount: wasUnread ? Math.max(0, state.unreadCount - 1) : state.unreadCount,
    }))
  },

  // Dropdown UI state
  toggleDropdown: () => set((s) => ({ isDropdownOpen: !s.isDropdownOpen })),
  closeDropdown: () => set({ isDropdownOpen: false }),

  /** WebSocket push handler — 백엔드 연결 시 useWebSocket.js 에서 호출 */
  pushNotification: (notification) => {
    set((state) => ({
      notifications: [notification, ...state.notifications],
      unreadCount: state.unreadCount + 1,
    }))
  },
}))

export default useNotificationStore
