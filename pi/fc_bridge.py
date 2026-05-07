#!/usr/bin/env python3
# =============================================
# pi/fc_bridge.py
# 역할: Raspberry Pi Zero 2 W 측 메시지 펌프
#       (백엔드 ↔ FC INAV) 양방향 WebSocket ↔ MSP V2 UART 게이트웨이
#
# 본 스크립트는 Pi 의 단일 프로세스로 동작하며, Pi 에서는 자율비행 알고리즘을
# 일절 수행하지 않는다. (메모리 512MB 제약 — SLAM/추론은 백엔드 GPU 서버에서)
#
# 환경변수:
#   AEROINSPECT_BACKEND_WS_URL  ws://<backend>:8000/api/v1/mission/fc-bridge
#   AEROINSPECT_FC_UART         /dev/serial0  (혹은 /dev/ttyAMA0, /dev/ttyUSB0)
#   AEROINSPECT_FC_BAUD         115200
#   AEROINSPECT_PI_TOKEN        백엔드와 공유하는 attach 토큰 (미사용 시 빈 문자열)
#
# 의존성: python3, asyncio, websockets, pyserial
# =============================================
from __future__ import annotations

import asyncio
import json
import os
import struct
import sys
import time
from typing import Any, Dict, List, Optional

import serial  # type: ignore[import-not-found]   # Pi 전용 (pyserial)
import websockets  # type: ignore[import-not-found]   # Pi 전용

# ── 환경변수 ──────────────────────────────
WS_URL = os.environ.get(
    "AEROINSPECT_BACKEND_WS_URL",
    "ws://192.168.1.10:8000/api/v1/mission/fc-bridge",
)
UART_DEV = os.environ.get("AEROINSPECT_FC_UART", "/dev/serial0")
UART_BAUD = int(os.environ.get("AEROINSPECT_FC_BAUD", "115200"))
PI_TOKEN = os.environ.get("AEROINSPECT_PI_TOKEN", "")
HEARTBEAT_SEC = 0.2
RECONNECT_BACKOFF_SEC = 2.0
RECONNECT_BACKOFF_MAX = 30.0


# ── MSP V2 함수 코드 (INAV) ────────────────
# https://github.com/iNavFlight/inav/wiki/MSP-V2
MSP_SET_RAW_RC = 200
MSP_RAW_IMU = 102
MSP_ATTITUDE = 108
MSP_ALTITUDE = 109
MSP_BATTERY_STATE = 130
MSP_NAV_STATUS = 121
MSP_SET_NAV_MODE = 217          # MSP2_NAV_SET_MODE (INAV 확장)
MSP2_INAV_MISSION_LOAD = 0x2003
MSP2_INAV_SET_ATTITUDE = 0x2070  # 가상 — INAV 빌드별 매핑 다를 수 있음
MSP2_COMMON_SETTING = 0x1003    # placeholder

# AUX 채널 매핑 (INAV CLI 의 modes 설정과 일치해야 함)
AUX_ARM = 5      # CH5
AUX_NAV_MODE = 6 # CH6 (POSHOLD/WP/RTH/LAND)
RC_NEUTRAL = 1500
RC_HIGH = 2000
RC_LOW = 1000

NAV_MODE_VALUES = {
    "POSHOLD": 1700,
    "WP": 1900,
    "RTH": 1500,
    "LAND": 1300,
}

# ── RC 채널 상태 캐시 ─────────────────────
# INAV 의 MSP_SET_RAW_RC 는 8채널 전체를 한 번에 갱신하는 명령이다.
# 따라서 set_raw_rc / arm / set_nav_mode / set_attitude 가 매번 부분 채널만 보내면
# 나머지 채널이 NEUTRAL 로 reset 되어 ARM 풀림 / NAV 모드 풀림이 발생한다.
# 본 모듈은 RC 채널 상태를 모듈 레벨로 캐시해 매번 8채널 전체를 빌드한다.
# index: 0=roll/vy, 1=pitch/vx, 2=throttle/vz, 3=yaw, 4=AUX1(ARM), 5=AUX2(NAV mode), 6,7=spare
_rc_state: List[int] = [RC_NEUTRAL] * 8
_rc_state[AUX_ARM - 1] = RC_LOW                           # 시동 OFF
_rc_state[AUX_NAV_MODE - 1] = NAV_MODE_VALUES["POSHOLD"]  # 기본 모드 POSHOLD
_rc_state[2] = RC_LOW                                      # throttle 시작점 LOW (안전)


def _build_set_raw_rc_packet() -> bytes:
    payload = b"".join(struct.pack("<H", int(c)) for c in _rc_state)
    return msp_v2_encode(MSP_SET_RAW_RC, payload)


# ── CRC8 DVB-S2 ─────────────────────────────
def _crc8_dvb_s2(crc: int, b: int) -> int:
    crc ^= b & 0xFF
    for _ in range(8):
        if crc & 0x80:
            crc = ((crc << 1) ^ 0xD5) & 0xFF
        else:
            crc = (crc << 1) & 0xFF
    return crc


def _crc8_buf(buf: bytes) -> int:
    crc = 0
    for b in buf:
        crc = _crc8_dvb_s2(crc, b)
    return crc


# ── MSP V2 직렬화 ────────────────────────────
def msp_v2_encode(function: int, payload: bytes = b"") -> bytes:
    """
    MSP V2 패킷 (master→FC, '$X<'). flags=0.
    header(3) + flags(1) + func(2) + size(2) + payload + crc(1)
    """
    flags = 0
    body = struct.pack("<BHH", flags, function, len(payload)) + payload
    crc = _crc8_buf(body)
    return b"$X<" + body + bytes([crc])


def msp_v2_decode(buf: bytes) -> Optional[Dict[str, Any]]:
    """간단 V2 응답 파서. 최소 sanity check."""
    if len(buf) < 9:
        return None
    if buf[:3] != b"$X>":
        return None
    flags, function, size = struct.unpack("<BHH", buf[3:8])
    if len(buf) < 8 + size + 1:
        return None
    payload = buf[8 : 8 + size]
    crc = buf[8 + size]
    body = buf[3 : 8 + size]
    if _crc8_buf(body) != crc:
        return None
    return {"flags": flags, "function": function, "payload": payload}


# ── 명령 → MSP 매핑 (모두 _rc_state 캐시 변경 후 8채널 전체 송신) ─
def _clamp_pwm(v: float, lim: float) -> int:
    norm = max(-1.0, min(1.0, v / max(lim, 1e-6)))
    return int(round(1500 + norm * 500))


def cmd_set_raw_rc(rc_channels: Dict[str, float]) -> bytes:
    """
    vx/vy/vz/yaw_rate 만 갱신. ARM/NAV/throttle 등 다른 채널은 캐시 유지 → ARM 풀림 방지.
    매핑(angle 모드 가정):
      ch1 roll     ← vy
      ch2 pitch    ← vx
      ch3 throttle ← 1500 + vz/v_max*500 (호버 보상)
      ch4 yaw_rate ← yaw_rate
    """
    v_max = 0.8
    yaw_max = 1.5
    _rc_state[0] = _clamp_pwm(rc_channels.get("vy", 0.0), v_max)   # roll
    _rc_state[1] = _clamp_pwm(rc_channels.get("vx", 0.0), v_max)   # pitch
    _rc_state[2] = _clamp_pwm(rc_channels.get("vz", 0.0), v_max)   # throttle (호버 1500)
    _rc_state[3] = _clamp_pwm(rc_channels.get("yaw_rate", 0.0), yaw_max)
    return _build_set_raw_rc_packet()


def cmd_set_nav_mode(mode: str) -> bytes:
    """AUX_NAV_MODE 만 갱신."""
    _rc_state[AUX_NAV_MODE - 1] = NAV_MODE_VALUES.get(mode.upper(), RC_NEUTRAL)
    return _build_set_raw_rc_packet()


def cmd_arm(arm: bool) -> bytes:
    """AUX_ARM 만 갱신. arm=True 시 HIGH, False 시 LOW."""
    _rc_state[AUX_ARM - 1] = RC_HIGH if arm else RC_LOW
    return _build_set_raw_rc_packet()


def cmd_set_attitude(roll: float, pitch: float, yaw: float, thrust: float) -> bytes:
    """
    INAV angle 모드 RC 채널 환산 — roll/pitch 절대값 ≤30°, throttle 0~1.
    yaw 와 thrust 는 절대값. 다른 채널(ARM/NAV)은 캐시 유지.
    """
    def clamp_attitude_pwm(angle_rad: float, lim_rad: float = 0.523) -> int:
        norm = max(-1.0, min(1.0, angle_rad / lim_rad))
        return int(round(1500 + norm * 500))

    _rc_state[0] = clamp_attitude_pwm(roll)
    _rc_state[1] = clamp_attitude_pwm(pitch)
    _rc_state[3] = int(round(1500 + max(-1.0, min(1.0, yaw / 3.1416)) * 500))
    _rc_state[2] = int(round(1000 + max(0.0, min(1.0, thrust)) * 1000))
    return _build_set_raw_rc_packet()


# ── 텔레메트리 디코더 (수신만) ───────────────
def parse_attitude(payload: bytes) -> Dict[str, float]:
    """MSP_ATTITUDE: roll(1/10°), pitch(1/10°), yaw(°)."""
    if len(payload) < 6:
        return {}
    roll, pitch, yaw = struct.unpack("<hhh", payload[:6])
    return {"roll": roll / 10.0, "pitch": pitch / 10.0, "yaw": float(yaw)}


def parse_altitude(payload: bytes) -> Dict[str, float]:
    """MSP_ALTITUDE: alt(int32, cm), vario(int16, cm/s)."""
    if len(payload) < 6:
        return {}
    alt, vario = struct.unpack("<ih", payload[:6])
    return {"alt_m": alt / 100.0, "vario_mps": vario / 100.0}


def parse_battery_state(payload: bytes) -> Dict[str, Any]:
    """
    MSP_BATTERY_STATE V1 페이로드 (INAV 7.x 기준):
      cells(uint8), capacity(uint16,mAh), voltage(uint8,*0.1V),
      drawn(uint16,mAh), amperage(uint16,*0.01A)
    총 8바이트. struct.unpack 포맷 "<BHBHH" = 1+2+1+2+2 = 8.
    """
    if len(payload) < 8:
        return {}
    try:
        cells, capacity, voltage, drawn, amp = struct.unpack("<BHBHH", payload[:8])
    except struct.error:
        return {}
    return {
        "cells": cells,
        "capacity_mah": capacity,
        "voltage": voltage / 10.0,
        "drawn_mah": drawn,
        "current_a": amp / 100.0,
    }


# ── UART 직렬화기 (MSP 요청 큐 → UART) ──────
class FcSerial:
    def __init__(self, dev: str, baud: int) -> None:
        self.dev = dev; self.baud = baud
        self._ser: Optional[serial.Serial] = None
        self._lock = asyncio.Lock()

    async def open(self) -> None:
        loop = asyncio.get_running_loop()
        self._ser = await loop.run_in_executor(
            None, lambda: serial.Serial(self.dev, self.baud, timeout=0.05),
        )

    async def write(self, packet: bytes) -> None:
        if self._ser is None:
            return
        async with self._lock:
            await asyncio.get_running_loop().run_in_executor(None, self._ser.write, packet)

    async def read_chunk(self, n: int = 256) -> bytes:
        if self._ser is None:
            return b""
        return await asyncio.get_running_loop().run_in_executor(None, self._ser.read, n)


# ── 메인 펌프 ─────────────────────────────
class FcBridgePump:
    def __init__(self) -> None:
        self.fc = FcSerial(UART_DEV, UART_BAUD)
        self._rx_buf = bytearray()
        self._latest_telemetry: Dict[str, Any] = {}

    async def run(self) -> None:
        await self.fc.open()
        backoff = RECONNECT_BACKOFF_SEC
        while True:
            try:
                async with websockets.connect(
                    WS_URL,
                    extra_headers=[("X-Aeroinspect-Pi-Token", PI_TOKEN)] if PI_TOKEN else None,
                    max_size=2**20,
                ) as ws:
                    print(f"[fc_bridge] connected {WS_URL}")
                    backoff = RECONNECT_BACKOFF_SEC
                    await asyncio.gather(
                        self._cmd_consumer(ws),
                        self._uart_to_ws_loop(ws),
                        self._heartbeat_loop(ws),
                    )
            except (OSError, websockets.WebSocketException) as e:
                print(f"[fc_bridge] WS disconnected: {e}, retry in {backoff}s")
                await asyncio.sleep(backoff)
                backoff = min(RECONNECT_BACKOFF_MAX, backoff * 2)

    async def _cmd_consumer(self, ws) -> None:
        """백엔드 명령 메시지 → MSP 직렬화 → UART."""
        async for raw in ws:
            try:
                msg = json.loads(raw)
            except Exception:
                continue
            if msg.get("type") != "command":
                continue
            name = msg.get("name", "")
            payload = msg.get("payload") or {}
            packet = self._build_packet(name, payload)
            if packet:
                await self.fc.write(packet)

    def _build_packet(self, name: str, payload: dict) -> Optional[bytes]:
        if name == "set_raw_rc":
            return cmd_set_raw_rc(payload)
        if name == "set_nav_mode":
            return cmd_set_nav_mode(str(payload.get("mode", "POSHOLD")))
        if name == "arm":
            return cmd_arm(True)
        if name == "disarm":
            return cmd_arm(False)
        if name == "land":
            return cmd_set_nav_mode("LAND")
        if name == "rth":
            return cmd_set_nav_mode("RTH")
        if name == "set_attitude":
            return cmd_set_attitude(
                float(payload.get("roll_rad", 0.0)),
                float(payload.get("pitch_rad", 0.0)),
                float(payload.get("yaw_rad", 0.0)),
                float(payload.get("thrust_norm", 0.5)),
            )
        if name == "load_mission_wp":
            # 단순 — INAV WP 형식 직렬화는 빌드별 차이 큼. v1.1 에서는
            # set_raw_rc + set_nav_mode 조합으로 흐름 충분. 차후 확장.
            return None
        return None

    async def _uart_to_ws_loop(self, ws) -> None:
        """UART → MSP 파싱 → WS 텔레메트리 송출."""
        while True:
            chunk = await self.fc.read_chunk(256)
            if chunk:
                self._rx_buf.extend(chunk)
                self._consume_rx_buf(ws)
            else:
                await asyncio.sleep(0.005)

    def _consume_rx_buf(self, ws) -> None:
        """버퍼에서 MSP V2 패킷을 찾아 텔레메트리로 broadcast."""
        while True:
            i = self._rx_buf.find(b"$X>")
            if i < 0:
                if len(self._rx_buf) > 64:
                    self._rx_buf.clear()
                return
            del self._rx_buf[:i]
            if len(self._rx_buf) < 9:
                return
            flags, function, size = struct.unpack("<BHH", bytes(self._rx_buf[3:8]))
            full_len = 8 + size + 1
            if len(self._rx_buf) < full_len:
                return
            packet = bytes(self._rx_buf[:full_len])
            del self._rx_buf[:full_len]
            decoded = msp_v2_decode(packet)
            if decoded is None:
                continue
            self._update_telemetry(decoded["function"], decoded["payload"])
            asyncio.create_task(self._send_telemetry(ws))

    def _update_telemetry(self, function: int, payload: bytes) -> None:
        if function == MSP_ATTITUDE:
            self._latest_telemetry.update(parse_attitude(payload))
        elif function == MSP_ALTITUDE:
            d = parse_altitude(payload)
            self._latest_telemetry["pos_z"] = d.get("alt_m")
            self._latest_telemetry["vel_z"] = d.get("vario_mps")
        elif function == MSP_BATTERY_STATE:
            d = parse_battery_state(payload)
            self._latest_telemetry["voltage"] = d.get("voltage")
            cap = d.get("capacity_mah") or 0
            drawn = d.get("drawn_mah") or 0
            if cap > 0:
                self._latest_telemetry["battery_pct"] = max(0.0, 100.0 * (1.0 - drawn / cap))

    async def _send_telemetry(self, ws) -> None:
        try:
            await ws.send(json.dumps({
                "type": "telemetry",
                "ts": time.time(),
                **self._latest_telemetry,
            }))
        except Exception:
            pass

    async def _heartbeat_loop(self, ws) -> None:
        while True:
            try:
                await ws.send(json.dumps({"type": "heartbeat", "ts": time.time()}))
            except Exception:
                return
            await asyncio.sleep(HEARTBEAT_SEC)


def main() -> int:
    try:
        asyncio.run(FcBridgePump().run())
    except KeyboardInterrupt:
        return 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
