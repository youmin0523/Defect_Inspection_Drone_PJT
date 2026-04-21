/**
 * OrgRequired.jsx
 * 역할: 조직 소속 필수 라우트 가드
 *       - 미소속 사용자 → /employee/onboarding 리다이렉트
 *       - adminOnly 옵션: owner/admin 역할만 접근 허용
 */

import { Navigate } from 'react-router-dom'
import useAuthStore from '../../store/authStore'

export default function OrgRequired({ children, adminOnly = false }) {
  const { isAuthenticated, currentOrg } = useAuthStore()

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }

  if (!currentOrg) {
    return <Navigate to="/employee/onboarding" replace />
  }

  if (adminOnly && !['owner', 'admin'].includes(currentOrg.role)) {
    return <Navigate to="/employee" replace />
  }

  return children
}
