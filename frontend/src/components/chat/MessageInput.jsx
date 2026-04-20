/**
 * components/chat/MessageInput.jsx
 * 역할: 하단 메시지 입력 — Enter 전송, Shift+Enter 줄바꿈, 파일/이모지 placeholder
 */

import { useState, useRef } from 'react'
import { Paperclip, Smile, Send } from 'lucide-react'
import useChatStore from '../../store/chatStore.js'

export default function MessageInput() {
  const [text, setText] = useState('')
  const inputRef = useRef(null)
  const sendMessage = useChatStore((s) => s.sendMessage)

  const handleSend = () => {
    if (!text.trim()) return
    sendMessage({ text: text.trim() })
    setText('')
    inputRef.current?.focus()
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <div className="bg-white border-t border-gray-200 px-4 py-3">
      <div className="flex items-end gap-2">
        <button
          type="button"
          title="파일 첨부 (준비 중)"
          className="p-2 text-gray-400 rounded-lg cursor-not-allowed opacity-50"
          disabled
        >
          <Paperclip size={18} />
        </button>

        <div className="flex-1">
          <textarea
            ref={inputRef}
            rows={1}
            value={text}
            onChange={(e) => setText(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="메시지를 입력하세요..."
            className="w-full resize-none rounded-xl border border-gray-200 bg-gray-50 px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-400 focus:border-transparent placeholder:text-gray-400 max-h-32"
            style={{ minHeight: '40px' }}
          />
        </div>

        <button
          type="button"
          title="이모지 (준비 중)"
          className="p-2 text-gray-400 rounded-lg cursor-not-allowed opacity-50"
          disabled
        >
          <Smile size={18} />
        </button>

        <button
          type="button"
          onClick={handleSend}
          disabled={!text.trim()}
          className="p-2.5 bg-blue-600 text-white rounded-xl hover:bg-blue-700 disabled:opacity-40 disabled:cursor-not-allowed transition shadow-sm"
          title="전송"
        >
          <Send size={16} />
        </button>
      </div>
    </div>
  )
}
