"""
tests/test_ws_channel_whitelist.py
역할: WebSocket 채널 화이트리스트 검증.
  - 고정 채널 (defects/telemetry/thermal/camera) 허용
  - notifications:{user_uuid} 패턴 허용
  - 깨진 UUID, 다른 prefix, 빈 값 → 거부
실행: pytest tests/test_ws_channel_whitelist.py -v
"""

from uuid import uuid4

import pytest

from app.api.websocket import _is_valid_channel


@pytest.mark.parametrize("channel", ["defects", "telemetry", "thermal", "camera"])
def test_fixed_channels_pass(channel):
    assert _is_valid_channel(channel) is True


def test_notifications_with_valid_uuid_passes():
    user_id = str(uuid4())
    assert _is_valid_channel(f"notifications:{user_id}") is True


def test_notifications_with_invalid_uuid_rejected():
    assert _is_valid_channel("notifications:not-a-uuid") is False
    assert _is_valid_channel("notifications:12345") is False
    assert _is_valid_channel("notifications:") is False


def test_unknown_channel_rejected():
    assert _is_valid_channel("admin") is False
    assert _is_valid_channel("") is False
    assert _is_valid_channel("notifications") is False  # uuid 부분 누락
    assert _is_valid_channel(f"chat:{uuid4()}") is False  # 다른 prefix
