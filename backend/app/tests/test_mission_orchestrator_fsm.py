# =============================================
# test_mission_orchestrator_fsm.py
# FSM 전이 규칙(외부 의존 mock) + safety 결정 인터럽트 검증
# =============================================
from __future__ import annotations

import asyncio
import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.mission_orchestrator import (
    MissionOrchestrator, MissionPhase,
)
from app.services.safety_monitor import SafetyAction, SafetyDecision


@pytest.mark.asyncio
async def test_start_rejects_when_fc_not_attached():
    orch = MissionOrchestrator()
    with patch("app.services.mission_orchestrator.fc_bridge") as fc:
        fc.is_attached = False
        with pytest.raises(RuntimeError, match="fc_bridge_not_attached"):
            await orch.start("mission-1")


@pytest.mark.asyncio
async def test_start_rejects_when_already_running():
    orch = MissionOrchestrator()
    orch.state.phase = MissionPhase.MAPPING
    with patch("app.services.mission_orchestrator.fc_bridge") as fc:
        fc.is_attached = True
        with pytest.raises(RuntimeError, match="already in phase"):
            await orch.start("mission-2")


@pytest.mark.asyncio
async def test_safety_land_decision_triggers_failsafe():
    orch = MissionOrchestrator()
    orch.state.phase = MissionPhase.COVERAGE_FLY
    orch.state.mission_id = "m"
    decision = SafetyDecision(SafetyAction.LAND, "battery_low")
    with patch.object(orch, "_fail", new=AsyncMock()) as fail:
        await orch._on_safety_decision(decision)
        fail.assert_called_once()


@pytest.mark.asyncio
async def test_safety_hover_decision_calls_pause():
    orch = MissionOrchestrator()
    decision = SafetyDecision(SafetyAction.HOVER, "slam_low_conf")
    with patch.object(orch, "pause", new=AsyncMock()) as pause:
        await orch._on_safety_decision(decision)
        pause.assert_called_once()


@pytest.mark.asyncio
async def test_get_state_includes_verification_and_captured_cells():
    orch = MissionOrchestrator()
    s = orch.get_state()
    assert "phase" in s and "captured_cells" in s and "verification" in s
    # 초기 captured 0
    assert s["captured_cells"] == 0


@pytest.mark.asyncio
async def test_room_traversal_order_uses_pose_distance():
    """현재 pose 기준 가까운 룸부터 정렬."""
    from app.services.room_segmenter import RoomNode, RoomTopologyGraph
    from app.services.slam_runner import SlamPose

    orch = MissionOrchestrator()
    orch.state.last_pose = SlamPose(x=0.0, y=0.0, z=1.0, confidence=0.9)
    orch.state.topology = RoomTopologyGraph(
        nodes=[
            RoomNode(idx=0, name="far", centroid=(10.0, 0.0)),
            RoomNode(idx=1, name="near", centroid=(1.0, 0.0)),
        ],
    )
    order = orch._room_traversal_order()
    assert order[0] == 1   # 가까운 룸 먼저
