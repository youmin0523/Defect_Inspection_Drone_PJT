/**
 * AdminGpu.jsx
 * 역할: 슈퍼어드민 전용 — GCP GPU VM (drone-stream-api) 원격 제어
 *       - 상태 조회 / 시작 / 정지
 *       - 로컬 bat 파일 의존 제거 → 어떤 브라우저든 admin 권한이면 제어 가능 (상용 멀티유저 운영)
 *       - 시간당 ~$0.71 (L4 GPU) 과금 시각화 + 누적 분 단위 사용 시간 표시
 */

import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import axios from 'axios'
import { ArrowLeft, Power, PowerOff, RefreshCw, Cpu, AlertTriangle, Clock } from 'lucide-react'
import useAuthStore from '../../store/authStore'

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

const STATUS_BADGE = {
  RUNNING: 'bg-green-100 text-green-700 border-green-200',
  STAGING: 'bg-amber-100 text-amber-700 border-amber-200',
  PROVISIONING: 'bg-amber-100 text-amber-700 border-amber-200',
  STOPPING: 'bg-orange-100 text-orange-700 border-orange-200',
  TERMINATED: 'bg-gray-100 text-gray-600 border-gray-200',
}

const STATUS_LABEL = {
  RUNNING: '실행 중',
  STAGING: '준비 중',
  PROVISIONING: '준비 중',
  STOPPING: '정지 중',
  TERMINATED: '정지됨',
}

const HOURLY_RATE_USD = 0.71  // L4 GPU asia-northeast3-a 기준
const POLL_INTERVAL_MS = 10_000

export default function AdminGpu() {
  const navigate = useNavigate()
  const { token, user } = useAuthStore()
  const isSuperadmin = user?.is_superadmin

  const [status, setStatus] = useState(null)
  const [loading, setLoading] = useState(true)
  const [busy, setBusy] = useState(false)  // start/stop 중일 때 버튼 비활성화
  const [error, setError] = useState('')
  const [confirmAction, setConfirmAction] = useState(null)  // 'start' | 'stop' | null

  const headers = useMemo(() => ({ Authorization: `Bearer ${token}` }), [token])
  const pollTimerRef = useRef(null)

  const fetchStatus = useCallback(async () => {
    try {
      setError('')
      const res = await axios.get(`${API_BASE}/api/v1/admin/gpu/status`, { headers })
      setStatus(res.data)
    } catch (err) {
      setError(err.response?.data?.detail || 'GPU 상태 조회에 실패했습니다.')
    } finally {
      setLoading(false)
    }
  }, [headers])

  useEffect(() => {
    if (!isSuperadmin) return
    fetchStatus()
    pollTimerRef.current = setInterval(fetchStatus, POLL_INTERVAL_MS)
    return () => clearInterval(pollTimerRef.current)
  }, [fetchStatus, isSuperadmin])

  const handleStart = async () => {
    setBusy(true)
    setError('')
    try {
      await axios.post(`${API_BASE}/api/v1/admin/gpu/start`, {}, { headers })
      await fetchStatus()
    } catch (err) {
      setError(err.response?.data?.detail || 'GPU 시작 요청에 실패했습니다.')
    } finally {
      setBusy(false)
      setConfirmAction(null)
    }
  }

  const handleStop = async () => {
    setBusy(true)
    setError('')
    try {
      await axios.post(`${API_BASE}/api/v1/admin/gpu/stop`, {}, { headers })
      await fetchStatus()
    } catch (err) {
      setError(err.response?.data?.detail || 'GPU 정지 요청에 실패했습니다.')
    } finally {
      setBusy(false)
      setConfirmAction(null)
    }
  }

  // 누적 사용 시간/예상 비용 (마지막 start 이후, RUNNING 상태일 때만)
  const runtimeInfo = useMemo(() => {
    if (status?.status !== 'RUNNING' || !status?.last_start_at) return null
    const startedAt = new Date(status.last_start_at)
    const now = new Date()
    const ms = now - startedAt
    const totalMin = Math.floor(ms / 60000)
    const hours = Math.floor(totalMin / 60)
    const minutes = totalMin % 60
    const cost = (totalMin / 60) * HOURLY_RATE_USD
    return {
      label: hours > 0 ? `${hours}시간 ${minutes}분` : `${minutes}분`,
      costUsd: cost,
    }
  }, [status])

  if (!isSuperadmin) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center p-6">
        <div className="bg-white rounded-2xl shadow-sm p-8 max-w-md text-center">
          <AlertTriangle className="w-12 h-12 text-amber-500 mx-auto mb-4" />
          <h2 className="text-lg font-bold text-slate-900 mb-2">접근 권한 없음</h2>
          <p className="text-sm text-gray-500 mb-6">GPU 제어는 플랫폼 슈퍼어드민 전용입니다.</p>
          <button onClick={() => navigate('/employee')} className="px-4 py-2 bg-slate-900 text-white text-sm rounded-lg hover:bg-slate-800 transition">
            대시보드로 돌아가기
          </button>
        </div>
      </div>
    )
  }

  const currentStatus = status?.status
  const isRunning = currentStatus === 'RUNNING'
  const isTransitioning = currentStatus === 'STAGING' || currentStatus === 'PROVISIONING' || currentStatus === 'STOPPING'

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-3xl mx-auto">
        {/* 헤더 */}
        <button onClick={() => navigate('/employee')} className="flex items-center gap-1 text-sm text-gray-500 hover:text-gray-700 mb-2">
          <ArrowLeft className="w-4 h-4" /> 대시보드로 돌아가기
        </button>
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-2xl font-bold text-slate-900 flex items-center gap-2">
              <Cpu className="w-6 h-6 text-blue-600" /> GPU 추론 서버 제어
            </h1>
            <p className="text-sm text-gray-500 mt-1">
              GCP L4 GPU VM (drone-stream-api) — 점검 시작 전 켜고, 종료 후 정지하세요.
            </p>
          </div>
          <span className="inline-block text-xs px-2 py-0.5 bg-red-100 text-red-700 rounded-full font-medium">슈퍼어드민</span>
        </div>

        {error && (
          <div className="mb-4 p-3 bg-red-50 border border-red-200 text-red-600 text-sm rounded-lg">{error}</div>
        )}

        {/* 상태 카드 */}
        <div className="bg-white rounded-2xl shadow-sm p-6 mb-4">
          <div className="flex items-center justify-between mb-4">
            <div>
              <div className="text-xs uppercase tracking-wide text-gray-400 mb-1">현재 상태</div>
              {loading ? (
                <div className="text-gray-400">불러오는 중...</div>
              ) : (
                <div className="flex items-center gap-3">
                  <span className={`inline-block px-3 py-1 text-sm font-semibold border rounded-full ${STATUS_BADGE[currentStatus] || 'bg-gray-100 text-gray-600 border-gray-200'}`}>
                    {STATUS_LABEL[currentStatus] || currentStatus || '알 수 없음'}
                  </span>
                  {status?.machine_type && (
                    <span className="text-xs text-gray-400">{status.machine_type} · {status.zone}</span>
                  )}
                </div>
              )}
            </div>
            <button
              onClick={fetchStatus}
              disabled={busy}
              title="상태 새로고침"
              className="p-2 rounded-lg border border-gray-200 hover:bg-gray-50 disabled:opacity-50"
            >
              <RefreshCw className={`w-4 h-4 text-gray-500 ${busy ? 'animate-spin' : ''}`} />
            </button>
          </div>

          {/* 실행 중일 때 누적 사용 시간 + 예상 비용 */}
          {runtimeInfo && (
            <div className="grid grid-cols-2 gap-3 mb-4 text-sm">
              <div className="p-3 bg-gray-50 rounded-lg">
                <div className="flex items-center gap-1 text-xs text-gray-400 mb-1"><Clock className="w-3 h-3" /> 마지막 시작 후 경과</div>
                <div className="font-semibold text-slate-900">{runtimeInfo.label}</div>
              </div>
              <div className="p-3 bg-gray-50 rounded-lg">
                <div className="text-xs text-gray-400 mb-1">이번 세션 누적 비용 (추정)</div>
                <div className="font-semibold text-slate-900">${runtimeInfo.costUsd.toFixed(2)}</div>
              </div>
            </div>
          )}

          {/* 버튼 */}
          <div className="grid grid-cols-2 gap-3">
            <button
              onClick={() => setConfirmAction('start')}
              disabled={busy || isRunning || isTransitioning}
              className="flex items-center justify-center gap-2 px-4 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 transition disabled:opacity-50 disabled:cursor-not-allowed font-medium"
            >
              <Power className="w-4 h-4" /> 시작
            </button>
            <button
              onClick={() => setConfirmAction('stop')}
              disabled={busy || !isRunning}
              className="flex items-center justify-center gap-2 px-4 py-3 bg-slate-900 text-white rounded-lg hover:bg-slate-800 transition disabled:opacity-50 disabled:cursor-not-allowed font-medium"
            >
              <PowerOff className="w-4 h-4" /> 정지
            </button>
          </div>

          {isTransitioning && (
            <p className="text-xs text-amber-600 mt-3 text-center">
              상태 전환 중입니다. 1~2분 정도 걸릴 수 있어요. (10초마다 자동 갱신)
            </p>
          )}
        </div>

        {/* 비용 가이드 */}
        <div className="bg-white rounded-2xl shadow-sm p-5 text-sm text-gray-600 space-y-2">
          <div className="font-semibold text-slate-900">비용 가이드</div>
          <ul className="list-disc list-inside space-y-1">
            <li><span className="font-medium text-green-700">실행 중</span>: 시간당 ~${HOURLY_RATE_USD.toFixed(2)} (L4 GPU)</li>
            <li><span className="font-medium text-gray-700">정지됨</span>: GPU 과금 중단, 디스크/IP 만 ~$13/월 유지</li>
            <li>점검 직전 켜고, 종료 직후 정지하는 운영을 권장합니다.</li>
          </ul>
        </div>

        {/* 확인 모달 */}
        {confirmAction && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
            <div className="bg-white rounded-2xl p-6 w-full max-w-md mx-4 shadow-2xl">
              <h3 className="text-lg font-bold text-slate-900 mb-2">
                {confirmAction === 'start' ? 'GPU 서버를 시작할까요?' : 'GPU 서버를 정지할까요?'}
              </h3>
              <p className="text-sm text-gray-600 mb-5">
                {confirmAction === 'start'
                  ? `시작 직후 시간당 ~$${HOURLY_RATE_USD.toFixed(2)} 과금이 시작됩니다. 점검이 끝나면 반드시 정지해주세요.`
                  : '진행 중인 추론 세션이 모두 끊깁니다. 점검이 완전히 끝났는지 확인해주세요.'}
              </p>
              <div className="flex gap-3">
                <button
                  onClick={() => setConfirmAction(null)}
                  disabled={busy}
                  className="flex-1 px-4 py-2.5 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition disabled:opacity-50"
                >
                  취소
                </button>
                <button
                  onClick={confirmAction === 'start' ? handleStart : handleStop}
                  disabled={busy}
                  className={`flex-1 px-4 py-2.5 text-white rounded-lg transition disabled:opacity-50 ${confirmAction === 'start' ? 'bg-green-600 hover:bg-green-700' : 'bg-slate-900 hover:bg-slate-800'}`}
                >
                  {busy ? '처리 중...' : confirmAction === 'start' ? '시작' : '정지'}
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
