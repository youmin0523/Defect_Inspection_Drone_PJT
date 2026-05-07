# =============================================
# test_inspection_area.py
# 바닥 + 천장 + 벽 + 창호 합산 면적 / 면별 커버리지율 산출 검증
# =============================================
from __future__ import annotations

import math

import pytest

from app.services.inspection_area import (
    InspectionAreaCalculator, polygon_area_m2, polygon_perimeter_m,
)
from app.services.path_planner import PathPlanner, PlanParams


ROOM_RECT = [(0.0, 0.0), (5.0, 0.0), (5.0, 4.0), (0.0, 4.0)]


def test_polygon_area_rect():
    assert math.isclose(polygon_area_m2(ROOM_RECT), 20.0, abs_tol=1e-6)


def test_polygon_perimeter_rect():
    assert math.isclose(polygon_perimeter_m(ROOM_RECT), 18.0, abs_tol=1e-6)


def test_compute_room_total_area_no_windows():
    """바닥 20㎡ + 천장 20㎡ + 벽 18m × 2.4m = 43.2㎡ → 총 83.2㎡."""
    params = PlanParams(
        floor_z_m=0.0, ceiling_z_m=2.4,
        scan_walls=True, scan_ceiling=True, scan_floor=True, scan_windows=False,
    )
    plan = PathPlanner(params).plan_room(0, ROOM_RECT)
    calc = InspectionAreaCalculator(params)
    summary = calc.compute_room(
        room_idx=0, polygon=ROOM_RECT,
        room_waypoints=plan.waypoints, captured_cells=set(),
    )
    assert math.isclose(summary.area.floor_m2, 20.0, abs_tol=1e-6)
    assert math.isclose(summary.area.ceiling_m2, 20.0, abs_tol=1e-6)
    assert math.isclose(summary.area.walls_m2, 18.0 * 2.4, abs_tol=1e-6)
    assert math.isclose(summary.area.total_m2, 20.0 + 20.0 + 18.0 * 2.4, abs_tol=1e-6)


def test_compute_room_subtracts_window_area_from_walls():
    """창호 면적은 벽에서 차감되고 별도 windows_m2 로 산입."""
    win = [(1.0, -0.05), (3.0, -0.05), (3.0, 0.05), (1.0, 0.05)]   # 0.2㎡
    params = PlanParams(
        floor_z_m=0.0, ceiling_z_m=2.4,
        scan_walls=True, scan_ceiling=True, scan_floor=True, scan_windows=True,
    )
    plan = PathPlanner(params).plan_room(0, ROOM_RECT, window_polygons=[win])
    calc = InspectionAreaCalculator(params)
    summary = calc.compute_room(
        room_idx=0, polygon=ROOM_RECT,
        room_waypoints=plan.waypoints, captured_cells=set(),
        window_polygons=[win],
    )
    walls_gross = 18.0 * 2.4
    win_area = 0.2
    assert math.isclose(summary.area.windows_m2, win_area, abs_tol=1e-6)
    assert math.isclose(summary.area.walls_m2, walls_gross - win_area, abs_tol=1e-6)


def test_coverage_ratio_zero_then_full():
    params = PlanParams(scan_walls=False, scan_ceiling=False, scan_floor=True)
    plan = PathPlanner(params).plan_room(0, ROOM_RECT)
    calc = InspectionAreaCalculator(params)

    summary0 = calc.compute_room(
        room_idx=0, polygon=ROOM_RECT,
        room_waypoints=plan.waypoints, captured_cells=set(),
    )
    assert summary0.overall_coverage.ratio == 0.0

    all_cells = {w.cell_idx for w in plan.waypoints if w.purpose != "discrepancy"}
    summary1 = calc.compute_room(
        room_idx=0, polygon=ROOM_RECT,
        room_waypoints=plan.waypoints, captured_cells=all_cells,
    )
    assert math.isclose(summary1.overall_coverage.ratio, 1.0, abs_tol=1e-6)


def test_compute_mission_supplied_ratio():
    params = PlanParams(scan_walls=False, scan_ceiling=False, scan_floor=True)
    plan = PathPlanner(params).plan_mission(
        topology_nodes=[{"idx": 0, "polygon": [list(p) for p in ROOM_RECT]}],
    )
    calc = InspectionAreaCalculator(params)
    summary = calc.compute_mission(
        plan=plan,
        topology_nodes=[{"idx": 0, "name": "room_0", "polygon": [list(p) for p in ROOM_RECT]}],
        captured_cells=set(),
        supplied_area_m2=40.0,   # 분양면적이 SLAM 실측(20㎡)의 2배
    )
    assert summary.supplied_coverage_ratio is not None
    assert math.isclose(summary.supplied_coverage_ratio, 0.5, abs_tol=1e-6)
