/**
 * authStore.js
 * 역할: 인증 상태 관리 (Zustand)
 *       - JWT 토큰 저장/삭제 (localStorage 연동)
 *       - 현재 로그인 사용자 정보 보관
 *       - 로그인/로그아웃 액션
 */

import { create } from 'zustand'

const useAuthStore = create((set) => ({
  // ── 상태 ──────────────────────────────────
  token: localStorage.getItem('access_token') || null,
  user: JSON.parse(localStorage.getItem('user') || 'null'),
  isAuthenticated: !!localStorage.getItem('access_token'),

  // ── 로그인 성공 시 호출 ───────────────────
  setAuth: (token, user) => {
    localStorage.setItem('access_token', token)
    localStorage.setItem('user', JSON.stringify(user))
    set({ token, user, isAuthenticated: true })
  },

  // ── 로그아웃 ──────────────────────────────
  logout: () => {
    localStorage.removeItem('access_token')
    localStorage.removeItem('user')
    set({ token: null, user: null, isAuthenticated: false })
  },
}))

export default useAuthStore
