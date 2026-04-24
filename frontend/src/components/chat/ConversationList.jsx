/**
 * components/chat/ConversationList.jsx
 * 역할: 좌측 패널 — Slack 스타일 대화방 목록 (검색 + 필터 탭 + 스크롤 목록)
 */

import { Search } from 'lucide-react'
import useChatStore from '../../store/chatStore.js'
import { CHAT_FILTER_TABS } from '../../constants/chatConstants.js'
import ConversationItem from './ConversationItem.jsx'

function getCurrentUserId() {
  const stored = JSON.parse(localStorage.getItem('user') || 'null')
  return stored?.id || null
}

export default function ConversationList() {
  const conversations = useChatStore((s) => s.conversations)
  const filterType = useChatStore((s) => s.filterType)
  const searchQuery = useChatStore((s) => s.searchQuery)
  const setFilter = useChatStore((s) => s.setFilter)
  const setSearch = useChatStore((s) => s.setSearch)

  // 필터 적용
  let filtered = conversations
  if (filterType !== 'all') {
    filtered = filtered.filter((c) => c.type === filterType)
  }
  if (searchQuery.trim()) {
    const q = searchQuery.toLowerCase()
    const currentUserId = getCurrentUserId()
    filtered = filtered.filter((c) => {
      if (c.name?.toLowerCase().includes(q)) return true
      // DM: 상대방 이름으로 검색 (participants 는 {user_id, name, initials} 객체 배열)
      if (c.type === 'dm') {
        const other = c.participants?.find((p) => p.user_id !== currentUserId)
        return other?.name?.toLowerCase().includes(q)
      }
      return false
    })
  }

  return (
    <aside className="w-80 bg-white border-r border-gray-200 flex flex-col shrink-0">
      {/* 검색 */}
      <div className="p-3 border-b border-gray-100">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={14} />
          <input
            type="text"
            placeholder="대화 검색..."
            value={searchQuery}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-9 pr-3 py-2 text-sm bg-gray-50 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-400 focus:border-transparent placeholder:text-gray-400"
          />
        </div>
      </div>

      {/* 필터 탭 */}
      <div className="flex px-3 pt-2 pb-2 gap-1 border-b border-gray-100">
        {CHAT_FILTER_TABS.map((tab) => (
          <button
            key={tab.value}
            type="button"
            onClick={() => setFilter(tab.value)}
            className={`px-3 py-1.5 text-xs font-semibold rounded-md transition ${
              filterType === tab.value
                ? 'bg-blue-600 text-white'
                : 'text-gray-500 hover:bg-gray-100'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* 대화 목록 */}
      <div className="flex-1 overflow-y-auto py-1">
        {filtered.length === 0 ? (
          <p className="text-center text-sm text-gray-400 py-8">대화가 없습니다</p>
        ) : (
          filtered.map((conv) => <ConversationItem key={conv.id} conv={conv} />)
        )}
      </div>
    </aside>
  )
}
