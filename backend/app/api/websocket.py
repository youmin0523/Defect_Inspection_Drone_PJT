# =============================================
# app/api/websocket.py
# 역할: WebSocket 실시간 이벤트 엔드포인트
#       - WS /ws?channel={channel} → 채널 구독
#       - 채널: defects / telemetry / thermal / camera / notifications:{user_uuid}
#       - 연결 시 현재 카메라 모드 즉시 전송
#       - WS_HEARTBEAT_INTERVAL 초마다 ping 전송으로 죽은 연결 감지
# =============================================

import asyncio
import re

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends

from app.config import settings
from app.core.ws_manager import ConnectionManager
from app.dependencies import get_ws_manager

router = APIRouter()

VALID_CHANNELS = {"defects", "telemetry", "thermal", "camera"}

# notifications:{user_uuid} 패턴 허용 (사용자별 개인 알림 채널 — notification_service가 사용)
# TODO: JWT 토큰으로 본인만 자기 채널 구독 가능하게 인증 추가 필요 (현재는 UUID 형식만 검증)
_NOTIFICATION_CHANNEL_RE = re.compile(
    r"^notifications:[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-"
    r"[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"
)


def _is_valid_channel(channel: str) -> bool:
    """고정 채널 + notifications:{uuid} 패턴 허용."""
    return channel in VALID_CHANNELS or bool(_NOTIFICATION_CHANNEL_RE.match(channel))


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    channel: str = "defects",
    manager: ConnectionManager = Depends(get_ws_manager),
):
    """
    WebSocket 구독 엔드포인트.

    연결 방법:
        ws://localhost:8000/api/v1/ws?channel=defects

    수신 이벤트 타입:
        defects  채널: {"type": "defect.new", "data": {...}}
        telemetry채널: {"type": "telemetry.update", "data": {...}}
        thermal  채널: {"type": "thermal.frame", "data": {...}}
        camera   채널: {"type": "camera.mode_changed", "data": {"mode": "..."}}
    """
    # 유효하지 않은 채널이면 기본값 사용
    if not _is_valid_channel(channel):
        channel = "defects"

    await manager.connect(websocket, channel)

    # 연결 즉시 현재 상태 전송
    await manager.send_personal(websocket, {
        "type": "connection.established",
        "data": {
            "channel": channel,
            "message": f"'{channel}' 채널에 연결되었습니다.",
        },
    })

    try:
        # 하트비트 태스크: 주기적으로 ping을 보내 연결 유지
        async def heartbeat():
            while True:
                await asyncio.sleep(settings.WS_HEARTBEAT_INTERVAL)
                try:
                    await manager.send_personal(websocket, {"type": "ping"})
                except Exception:
                    break

        heartbeat_task = asyncio.create_task(heartbeat())

        try:
            # 클라이언트 메시지 수신 루프
            while True:
                data = await websocket.receive_json()
                # pong 응답 처리
                if data.get("type") == "pong":
                    continue
                # 기타 클라이언트 메시지 처리 (필요 시 확장)
        finally:
            heartbeat_task.cancel()

    except WebSocketDisconnect:
        pass
    finally:
        manager.disconnect(websocket, channel)
