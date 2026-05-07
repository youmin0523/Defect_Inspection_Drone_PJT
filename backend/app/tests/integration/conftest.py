# =============================================
# tests/integration/conftest.py
# 역할: SITL/Docker 환경에서만 동작하는 통합 테스트용 fixture + pytest 마커.
#
# 마커:
#   @pytest.mark.integration   — 외부 환경 필요 (SITL/Docker/카메라). 기본 skip.
#   --integration 플래그를 주면 실행.
#
# 환경변수:
#   AEROINSPECT_SITL_UART      /tmp/aeroinspect-fc-uart  (socat 가상 PTY)
#   AEROINSPECT_SITL_BAUD      115200
# =============================================
from __future__ import annotations

import os
from pathlib import Path

import pytest


def pytest_addoption(parser):
    parser.addoption(
        "--integration", action="store_true", default=False,
        help="외부 환경(SITL/Docker/카메라) 필요한 통합 테스트 실행",
    )


def pytest_configure(config):
    config.addinivalue_line(
        "markers", "integration: 외부 환경 필요. 기본 skip. --integration 으로 실행."
    )


def pytest_collection_modifyitems(config, items):
    if config.getoption("--integration"):
        return
    skip_integration = pytest.mark.skip(reason="외부 환경 미준비 — --integration 으로 실행")
    for item in items:
        if "integration" in item.keywords:
            item.add_marker(skip_integration)


# ── fixtures ──────────────────────────────
@pytest.fixture(scope="session")
def sitl_uart() -> str:
    """SITL 가상 PTY 경로. 미존재 시 테스트 skip."""
    path = os.environ.get("AEROINSPECT_SITL_UART", "/tmp/aeroinspect-fc-uart")
    if not Path(path).exists():
        pytest.skip(f"SITL UART {path} 미존재 — bash tools/inav-sitl/run.sh up 후 재시도")
    return path


@pytest.fixture(scope="session")
def sitl_baud() -> int:
    return int(os.environ.get("AEROINSPECT_SITL_BAUD", "115200"))
