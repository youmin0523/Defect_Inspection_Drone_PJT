/**
 * pages/employee/Chat.jsx
 * 역할: 사내 메신저 메인 페이지 — Slack 3컬럼 + 카카오톡 말풍선 스타일
 *       - 좌측: ConversationList (대화방 목록 + 검색 + 필터)
 *       - 중앙: MessageThread (메시지 히스토리 + 입력)
 *       - 우측: ParticipantPanel (참여자 정보, 접기 가능)
 */

import { useEffect } from 'react'
import { Link } from 'react-router-dom'
import { ArrowLeft, MessageSquare, Plus } from 'lucide-react'
import useChatStore from '../../store/chatStore.js'
import ConversationList from '../../components/chat/ConversationList.jsx'
import MessageThread from '../../components/chat/MessageThread.jsx'
import ParticipantPanel from '../../components/chat/ParticipantPanel.jsx'
import NewChatModal from '../../components/chat/NewChatModal.jsx'

export default function Chat() {
  const fetchConversations = useChatStore((s) => s.fetchConversations)
  const isParticipantPanelOpen = useChatStore((s) => s.isParticipantPanelOpen)
  const isNewChatModalOpen = useChatStore((s) => s.isNewChatModalOpen)
  const openNewChatModal = useChatStore((s) => s.openNewChatModal)

  // 초기 로드 — 대화방 목록만 가져오고, 자동 선택은 하지 않음
  // (사용자가 직접 좌측 패널에서 대화방을 선택해야 읽음 처리됨)
  useEffect(() => {
    fetchConversations()
  }, [fetchConversations])

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
              <ArrowLeft size={16} /> 직원 허브
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
