/**
 * pages/employee/Chat.jsx
 * 역할: 사내 메신저 메인 페이지 — Slack 3컬럼 + 카카오톡 말풍선 스타일
 *       - 좌측: ConversationList (대화방 목록 + 검색 + 필터)
 *       - 중앙: MessageThread (메시지 히스토리 + 입력)
 *       - 우측: ParticipantPanel (참여자 정보, 접기 가능)
 */

import { useEffect, useRef } from 'react'
import { Link } from 'react-router-dom'
import { ArrowLeft, MessageSquare, Plus } from 'lucide-react'
import useChatStore from '../../store/chatStore.js'
import ConversationList from '../../components/chat/ConversationList.jsx'
import MessageThread from '../../components/chat/MessageThread.jsx'
import ParticipantPanel from '../../components/chat/ParticipantPanel.jsx'
import NewChatModal from '../../components/chat/NewChatModal.jsx'

const WS_BASE = (import.meta.env.VITE_WS_URL || 'ws://localhost:8000/api/v1/ws').replace('/ws', '')

export default function Chat() {
  const fetchConversations = useChatStore((s) => s.fetchConversations)
  const refreshUnreadCounts = useChatStore((s) => s.refreshUnreadCounts)
  const activeConversationId = useChatStore((s) => s.activeConversationId)
  const isParticipantPanelOpen = useChatStore((s) => s.isParticipantPanelOpen)
  const isNewChatModalOpen = useChatStore((s) => s.isNewChatModalOpen)
  const openNewChatModal = useChatStore((s) => s.openNewChatModal)
  const chatWsRef = useRef(null)
  const userWsRef = useRef(null)

  // 현재 사용자 ID
  const currentUserId = JSON.parse(localStorage.getItem('user') || '{}')?.id

  // 공통 WS 메시지 핸들러
  const handleWsMessage = (event) => {
    try {
      const { type, data } = JSON.parse(event.data)
      if (type === 'chat.new_message' && data) {
        useChatStore.getState().receiveMessage(data)
      }
      if (type === 'chat.read' && data) {
        // 상대방이 읽음 → 읽음 카운트만 갱신 (selectConversation 금지 — markRead 재호출로 무한루프)
        const activeId = useChatStore.getState().activeConversationId
        if (data.conversation_id === activeId) {
          useChatStore.getState().refreshMessages(activeId)
        }
      }
      if (type === 'ping') {
        event.target.send(JSON.stringify({ type: 'pong' }))
      }
    } catch {}
  }

  // 초기 로드
  useEffect(() => {
    fetchConversations()
  }, [fetchConversations])

  // 개인 채널 WebSocket — 모든 대화방의 새 메시지 알림 수신
  useEffect(() => {
    if (!currentUserId) return

    const ws = new WebSocket(`${WS_BASE}/ws?channel=user:${currentUserId}`)
    userWsRef.current = ws
    ws.onmessage = handleWsMessage
    ws.onerror = () => {}
    ws.onclose = () => {}

    return () => {
      ws.close()
      userWsRef.current = null
    }
  }, [currentUserId])

  // 활성 대화방 WebSocket — 현재 보고 있는 대화의 실시간 메시지
  useEffect(() => {
    if (chatWsRef.current) {
      chatWsRef.current.close()
      chatWsRef.current = null
    }
    if (!activeConversationId) return

    const ws = new WebSocket(`${WS_BASE}/ws?channel=chat:${activeConversationId}`)
    chatWsRef.current = ws
    ws.onmessage = handleWsMessage
    ws.onerror = () => {}
    ws.onclose = () => {}

    return () => {
      ws.close()
      chatWsRef.current = null
    }
  }, [activeConversationId])

  // 주기적 미읽음 카운트 갱신 (백업 — WS 끊겼을 때 대비, 30초 간격)
  useEffect(() => {
    const interval = setInterval(() => {
      refreshUnreadCounts()
      fetchConversations()
    }, 30000)
    return () => clearInterval(interval)
  }, [refreshUnreadCounts, fetchConversations])

  return (
    <div className="h-screen flex flex-col bg-gray-50 text-slate-800 font-sans antialiased">
      {/* 상단 헤더 */}
      <header className="bg-white border-b border-gray-200 shadow-sm shrink-0">
        <div className="px-4 py-2.5 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Link
              to="/employee"
              className="inline-flex items-center gap-1.5 text-sm font-semibold text-gray-500 hover:text-blue-600 transition"
            >
              <ArrowLeft size={16} />
            </Link>
            <div className="h-5 w-px bg-gray-200" />
            <div className="flex items-center gap-2">
              <MessageSquare className="text-blue-600" size={20} />
              <span className="font-extrabold tracking-tight text-slate-800 text-base">
                메신저
              </span>
            </div>
          </div>
          <button
            type="button"
            onClick={openNewChatModal}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 text-sm font-semibold text-white bg-blue-600 hover:bg-blue-700 rounded-lg transition shadow-sm"
          >
            <Plus size={16} /> 새 대화
          </button>
        </div>
      </header>

      {/* 3컬럼 본문 */}
      <div className="flex-1 flex overflow-hidden">
        <ConversationList />
        <MessageThread />
        {isParticipantPanelOpen && <ParticipantPanel />}
      </div>

      {/* 새 대화 모달 */}
      {isNewChatModalOpen && <NewChatModal />}
    </div>
  )
}
