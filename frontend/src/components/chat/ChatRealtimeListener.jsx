/**
 * components/chat/ChatRealtimeListener.jsx
 * 역할: 전역 채팅 실시간 리스너 — `user:{userId}` 개인 채널에 항상 연결되어
 *       페이지 어디에 있든 새 메시지 수신 시 chatStore와 notificationStore를 갱신.
 *
 *   - chatStore.receiveMessage()로 미읽음 카운트/대화 목록 갱신
 *   - 현재 보고 있지 않은 대화의 메시지에 한해 notificationStore.pushChatNotification()
 *     호출 → 알림 벨에 "(보낸 사람)님께서 메시지를 보냈습니다." 항목 즉시 추가
 *
 *   기존 Chat.jsx 의 user 채널 WS 는 본 리스너로 이관(중복 연결 방지). Chat.jsx 는
 *   활성 대화방의 chat:{convId} 채널만 유지.
 *
 *   App.jsx 에서 /employee/* 경로에서만 마운트하여 비로그인/공개 페이지에서는 비용 0.
 */

import { useEffect } from 'react'
import useAuthStore from '../../store/authStore.js'
import useChatStore from '../../store/chatStore.js'
import useNotificationStore from '../../store/notificationStore.js'

const WS_BASE = (import.meta.env.VITE_WS_URL || 'ws://localhost:8000/api/v1/ws').replace('/ws', '')

export default function ChatRealtimeListener() {
  const userId = useAuthStore((s) => s.user?.id)

  useEffect(() => {
    if (!userId) return

    const ws = new WebSocket(`${WS_BASE}/ws?channel=user:${userId}`)

    ws.onmessage = (event) => {
      try {
        const { type, data } = JSON.parse(event.data)

        if (type === 'chat.new_message' && data) {
          // 내가 보낸 메시지는 receiveMessage 내부에서 무시되지만, 알림 push도 막아야 하므로 조기 반환
          if (data.sender_id === userId) return

          // chatStore: 메시지 추가 / 미읽음 카운트 / 대화방 정렬
          useChatStore.getState().receiveMessage(data)

          // 알림: 현재 보고 있는 대화가 아닐 때만 push
          const activeId = useChatStore.getState().activeConversationId
          if (data.conversation_id !== activeId) {
            useNotificationStore.getState().pushChatNotification({
              id: `chat-${data.id}`,
              message_id: data.id,
              sender_id: data.sender_id,
              sender_name: data.sender_name,
              conversation_id: data.conversation_id,
              text: data.text,
              file_name: data.file_name,
              created_at: data.created_at,
            })
          }
          return
        }

        if (type === 'chat.read' && data) {
          // 상대방 읽음 → 활성 대화방이면 메시지 다시 로드(읽음 카운트 갱신)
          const activeId = useChatStore.getState().activeConversationId
          if (data.conversation_id === activeId) {
            useChatStore.getState().refreshMessages(activeId)
          }
          return
        }

        if (type === 'ping') {
          ws.send(JSON.stringify({ type: 'pong' }))
        }
      } catch {
        // 파싱 실패 등은 무시 — 네트워크 노이즈로 간주
      }
    }

    ws.onerror = () => {}
    ws.onclose = () => {}

    return () => {
      ws.close()
    }
  }, [userId])

  return null
}
