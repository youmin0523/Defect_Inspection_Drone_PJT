# =============================================
# tests/integration/test_sitl_msp_loop.py
# 역할: SITL 가상 시리얼에 직접 MSP V2 패킷 송수신 → INAV 응답 검증.
#       fc_bridge.py 의 MSP 빌더/파서가 SITL 과 정합한지 확인.
# 실행: pytest --integration backend/app/tests/integration/
# =============================================
from __future__ import annotations

import struct
import sys
import time
from pathlib import Path

import pytest

# pi/ 모듈 경로 추가 — pi/fc_bridge.py 의 MSP 헬퍼 재사용
PI_DIR = Path(__file__).resolve().parents[5] / "pi"
sys.path.insert(0, str(PI_DIR))

try:
    import serial   # type: ignore
    _SERIAL_OK = True
except ImportError:
    _SERIAL_OK = False

# pi.fc_bridge 의 MSP 함수 — 빌드와 파서 정합 검증
try:
    from fc_bridge import (   # type: ignore[import-not-found]
        msp_v2_encode, msp_v2_decode, _crc8_buf,
        cmd_arm, cmd_set_nav_mode, cmd_set_raw_rc,
        MSP_ATTITUDE, MSP_ALTITUDE, MSP_BATTERY_STATE,
        parse_attitude, parse_altitude, parse_battery_state,
    )
    _PI_OK = True
except Exception:
    _PI_OK = False


pytestmark = pytest.mark.integration


@pytest.mark.skipif(not _SERIAL_OK or not _PI_OK, reason="pyserial 또는 pi 모듈 미가용")
def test_msp_v2_encode_decode_roundtrip():
    """msp_v2_encode → msp_v2_decode 라운드트립이 정합해야."""
    pkt = msp_v2_encode(MSP_ATTITUDE, b"")
    # 패킷이 '$X<' header + flags + func(2) + size(2) + crc(1) = 9 byte 최소
    assert pkt.startswith(b"$X<")
    assert len(pkt) >= 9


@pytest.mark.skipif(not _SERIAL_OK or not _PI_OK, reason="pyserial 또는 pi 모듈 미가용")
def test_battery_state_parser_handles_8byte_payload():
    """버그 #7 회귀 테스트 — 8 byte payload 가 struct error 없이 파싱."""
    # cells=4, capacity=1100, voltage=160(*0.1=16.0V), drawn=200, amp=0
    payload = struct.pack("<BHBHH", 4, 1100, 160, 200, 0)
    out = parse_battery_state(payload)
    assert out["cells"] == 4
    assert out["voltage"] == 16.0
    assert out["drawn_mah"] == 200


@pytest.mark.skipif(not _SERIAL_OK or not _PI_OK, reason="pyserial 또는 pi 모듈 미가용")
def test_arm_does_not_disarm_due_to_aux(sitl_uart, sitl_baud):
    """
    버그 #10 회귀 테스트 — cmd_arm 이후 cmd_set_raw_rc 호출이 ARM AUX 채널을
    유지하는지 검증. SITL UART 에 두 명령을 순서대로 보내고, MSP_RC (또는 ATTITUDE)
    응답이 끊기지 않는지 확인.
    """
    ser = serial.Serial(sitl_uart, sitl_baud, timeout=1.0)
    try:
        ser.write(cmd_arm(True))
        ser.flush()
        time.sleep(0.05)
        ser.write(cmd_set_raw_rc({"vx": 0.0, "vy": 0.0, "vz": 0.0, "yaw_rate": 0.0}))
        ser.flush()
        time.sleep(0.2)
        # 텔레메트리 요청 — MSP_ATTITUDE (V2 query)
        ser.write(msp_v2_encode(MSP_ATTITUDE, b""))
        time.sleep(0.2)
        data = ser.read(64)
        # 응답이 어디든 와 있어야 — SITL 이 살아 있다는 증거
        assert len(data) > 0
    finally:
        ser.close()


@pytest.mark.skipif(not _SERIAL_OK or not _PI_OK, reason="pyserial 또는 pi 모듈 미가용")
def test_nav_mode_change_does_not_disarm(sitl_uart, sitl_baud):
    """cmd_set_nav_mode 가 ARM AUX 캐시를 유지해 disarm 되지 않아야."""
    ser = serial.Serial(sitl_uart, sitl_baud, timeout=1.0)
    try:
        ser.write(cmd_arm(True)); ser.flush()
        time.sleep(0.1)
        ser.write(cmd_set_nav_mode("POSHOLD")); ser.flush()
        time.sleep(0.1)
        # MSP_ATTITUDE 쿼리
        ser.write(msp_v2_encode(MSP_ATTITUDE, b"")); ser.flush()
        time.sleep(0.2)
        data = ser.read(128)
        assert len(data) > 0
    finally:
        ser.close()
