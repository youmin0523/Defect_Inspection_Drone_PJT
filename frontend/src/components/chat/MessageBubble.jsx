/**
 * components/chat/MessageBubble.jsx
 * 역할: 카카오톡 스타일 말풍선 — 노란 내 메시지, 흰 상대 메시지, 연속 메시지 아바타 생략
 */

function getCurrentUserId() {
  const stored = JSON.parse(localStorage.getItem('user') || 'null')
  return stored?.id || null
}

function formatTime(ts) {
  const d = new Date(ts)
  return `${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
}

export default function MessageBubble({ message, showAvatar }) {
  const isMine = message.sender_id === getCurrentUserId()

  if (isMine) {
    return (
      <div className="flex justify-end mb-1 px-4">
        <div className="flex items-end gap-1.5 max-w-[70%]">
          {/* 읽음 + 시간 (왼쪽) */}
          <div className="flex flex-col items-end shrink-0 pb-0.5">
            {message.is_read && (
              <span className="text-[10px] text-yellow-600 font-medium leading-none"></span>
            )}
            <span className="text-[10px] text-gray-400 leading-none mt-0.5">
              {formatTime(message.created_at)}
            </span>
          </div>
          {/* 노란 말풍선 */}
          <div className="bg-yellow-300 text-slate-900 rounded-2xl rounded-br-sm px-3.5 py-2 shadow-sm">
            <p className="text-sm leading-relaxed whitespace-pre-wrap break-keep">{message.text}</p>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="flex gap-2 mb-1 px-4">
      {/* 아바타 (연속 메시지면 빈 공간) */}
      {showAvatar ? (
        message.sender_profile_image_url ? (
          <img
            src={`${import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'}${message.sender_profile_image_url}`}
            alt={message.sender_name}
            className="w-9 h-9 rounded-full object-cover shrink-0 mt-0.5"
          />
        ) : (
          <div className="w-9 h-9 rounded-full bg-slate-800 text-white flex items-center justify-center text-xs font-bold shrink-0 mt-0.5">
            {message.sender_initials}
          </div>
        )
      ) : (
        <div className="w-9 shrink-0" />
      )}

      <div className="max-w-[70%]">
        {/* 이름 (연속 메시지면 생략) */}
        {showAvatar && (
          <p className="text-xs font-semibold text-slate-600 mb-1 ml-1">{message.sender_name}</p>
        )}
        <div className="flex items-end gap-1.5">
          {/* 흰 말풍선 */}
          <div className="bg-white rounded-2xl rounded-bl-sm px-3.5 py-2 shadow-sm border border-gray-100">
            <p className="text-sm text-slate-800 leading-relaxed whitespace-pre-wrap break-keep">{message.text}</p>
          </div>
          {/* 시간 (오른쪽) */}
          <span className="text-[10px] text-gray-400 shrink-0 pb-0.5">
            {formatTime(message.created_at)}
          </span>
        </div>
      </div>
    </div>
  )
}
