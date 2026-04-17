/**
 * authApi.js
 * 역할: 인증 관련 백엔드 API 호출
 *       - 일반 로그인 (아이디+비밀번호)
 *       - OAuth 코드 교환 (Google / Kakao / Naver)
 *       - 현재 사용자 조회 (GET /auth/me)
 */

import axios from 'axios'

const API = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',
})

// 요청 시 JWT 토큰 자동 첨부
API.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

/** 일반 로그인 */
export const login = (username, password) =>
  API.post('/api/v1/auth/login', { username, password })

/** OAuth 인가 코드 → JWT 교환 */
export const oauthLogin = (provider, code, redirectUri) =>
  API.post(`/api/v1/oauth/${provider}`, { code, redirect_uri: redirectUri })

/** 현재 로그인 사용자 조회 */
export const getMe = () => API.get('/api/v1/auth/me')


// ── OAuth 인가 URL 빌더 ─────────────────────
const REDIRECT_BASE = window.location.origin

export const getGoogleAuthUrl = () => {
  const params = new URLSearchParams({
    client_id: import.meta.env.VITE_GOOGLE_CLIENT_ID,
    redirect_uri: `${REDIRECT_BASE}/auth/google/callback`,
    response_type: 'code',
    scope: 'openid email profile',
    access_type: 'offline',
    prompt: 'consent',
  })
  return `https://accounts.google.com/o/oauth2/v2/auth?${params}`
}

export const getKakaoAuthUrl = () => {
  const params = new URLSearchParams({
    client_id: import.meta.env.VITE_KAKAO_JS_KEY,
    redirect_uri: `${REDIRECT_BASE}/auth/kakao/callback`,
    response_type: 'code',
  })
  return `https://kauth.kakao.com/oauth/authorize?${params}`
}

export const getNaverAuthUrl = () => {
  const state = crypto.randomUUID()
  sessionStorage.setItem('naver_oauth_state', state)
  const params = new URLSearchParams({
    client_id: import.meta.env.VITE_NAVER_CLIENT_ID || '',
    redirect_uri: `${REDIRECT_BASE}/auth/naver/callback`,
    response_type: 'code',
    state,
  })
  return `https://nid.naver.com/oauth2.0/authorize?${params}`
}
