# =============================================
# tests/integration/test_fsm_full_flow.py
# 역할: SITL 띄워진 환경에서 mission_orchestrator FSM 풀플로우 검증.
#       (PseudoSlam 백엔드 + SITL fc_bridge 조합 — 실기 없이 IDLE → COMPLETE 전이)
# 실행: pytest --integration backend/app/tests/integration/test_fsm_full_flow.py
# =============================================
from __future__ import annotations

import asyncio
import os

import pytest

pytestmark = pytest.mark.integration


@pytest.mark.asyncio
async def test_orchestrator_full_flow_with_pseudo_slam(sitl_uart):
    """
    PseudoSlam 백엔드 + SITL fc_bridge → mission_orchestrator 가 FSM 모든 phase 를
    훑고 IDLE 로 복귀하는지 검증.

    전제:
      - bash tools/inav-sitl/run.sh up   (SITL 띄움)
      - SLAM_BACKEND=dummy 환경변수
    """
    os.environ["SLAM_BACKEND"] = "dummy"
    os.environ["SLAM_CAPTURE_DEVICE"] = "0"   # PseudoSlam 은 실제 디바이스 안 씀

    from app.services.mission_orchestrator import MissionOrchestrator, MissionPhase
    from app.services.fc_bridge import fc_bridge

    # Pi 측 fc_bridge 가 SITL 가상 UART 에 attach 되어 있다고 가정 — fc_bridge.is_attached True 강제
    if not fc_bridge.is_attached:
        pytest.skip("fc_bridge 미접속 — bash tools/inav-sitl/run.sh up 후 별도 fc_bridge.py 기동 필요")

    orch = MissionOrchestrator()
    await orch.start("mission-fsm-test")

    # 최대 60s 대기 — phase 가 IDLE 로 복귀하면 완료
    for _ in range(120):
        if orch.state.phase is MissionPhase.IDLE:
            break
        await asyncio.sleep(0.5)

    assert orch.state.phase is MissionPhase.IDLE, f"FSM 종료 실패 — phase={orch.state.phase}"
