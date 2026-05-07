# =============================================
# test_safety_monitor.py
# 안전 단일 진입점 — 임계값 우선순위 검증
# =============================================
from __future__ import annotations

import asyncio
import time

import pytest

from app.services.safety_monitor import (
    SafetyAction, SafetyMonitor, TelemetrySnapshot, Thresholds,
)


def _snap(**overrides) -> TelemetrySnapshot:
    base = dict(
        battery_pct=80.0,
        voltage_per_cell=4.0,
        tilt_deg=5.0,
        pos_var_m=0.1,
        last_telemetry_ts=time.time(),
        last_pi_heartbeat_ts=time.time(),
        inside_geofence=True,
        obstacle_min_dist_m=1.0,
        slam_confidence=0.9,
    )
    base.update(overrides)
    return TelemetrySnapshot(**base)


@pytest.mark.asyncio
async def test_continue_when_all_normal():
    sm = SafetyMonitor()
    d = await sm.check(_snap())
    assert d.action is SafetyAction.CONTINUE


@pytest.mark.asyncio
async def test_estop_overrides_all():
    sm = SafetyMonitor()
    sm.trigger_estop("test")
    d = await sm.check(_snap(battery_pct=10.0, inside_geofence=False))
    assert d.action is SafetyAction.ESTOP


@pytest.mark.asyncio
async def test_comm_loss_returns_land():
    sm = SafetyMonitor()
    d = await sm.check(_snap(last_pi_heartbeat_ts=time.time() - 10.0))
    assert d.action is SafetyAction.LAND
    assert d.reason == "comm_loss"


@pytest.mark.asyncio
async def test_geofence_breach_returns_rtl():
    sm = SafetyMonitor()
    d = await sm.check(_snap(inside_geofence=False))
    assert d.action is SafetyAction.RTL


@pytest.mark.asyncio
async def test_battery_low_returns_rtl():
    sm = SafetyMonitor()
    d = await sm.check(_snap(battery_pct=Thresholds.BATTERY_PCT_RTL - 5))
    assert d.action is SafetyAction.RTL


@pytest.mark.asyncio
async def test_tilt_anomaly_returns_land():
    sm = SafetyMonitor()
    d = await sm.check(_snap(tilt_deg=Thresholds.TILT_LIMIT_DEG + 10))
    assert d.action is SafetyAction.LAND


@pytest.mark.asyncio
async def test_slam_pos_var_returns_hover():
    sm = SafetyMonitor()
    d = await sm.check(_snap(pos_var_m=Thresholds.SLAM_POS_VAR_M + 0.2))
    assert d.action is SafetyAction.HOVER


@pytest.mark.asyncio
async def test_obstacle_breach_returns_hover():
    sm = SafetyMonitor()
    d = await sm.check(_snap(obstacle_min_dist_m=0.10))
    assert d.action is SafetyAction.HOVER


@pytest.mark.asyncio
async def test_callback_invoked_on_unsafe():
    sm = SafetyMonitor()
    received = []

    async def cb(decision):
        received.append(decision.action)

    sm.register(cb)
    await sm.check(_snap(inside_geofence=False))
    assert SafetyAction.RTL in received
