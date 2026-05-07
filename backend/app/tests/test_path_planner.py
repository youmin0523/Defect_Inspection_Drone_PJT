# =============================================
# test_path_planner.py
# 보스트로페돈 그리드, 4면 + 천장 + 바닥 + 창호 스캔, 차이영역 가중 검증
# =============================================
from __future__ import annotations

import math

import pytest

from app.services.path_planner import (
    FACE_CEILING, FACE_FLOOR, FACE_WALL, FACE_WINDOW,
    PathPlanner, PlanParams, grid_spacing,
)


# 5m × 4m 직사각형 룸 (CCW)
ROOM_RECT = [(0.0, 0.0), (5.0, 0.0), (5.0, 4.0), (0.0, 4.0)]


def test_grid_spacing_decreases_with_overlap():
    """overlap 증가 시 spacing 감소."""
    p1 = PlanParams(fov_h_deg=80.0, d_inspect_m=1.5, overlap=0.0)
    p2 = PlanParams(fov_h_deg=80.0, d_inspect_m=1.5, overlap=0.5)
    assert grid_spacing(p1) > grid_spacing(p2)
    # 최소 가드
    p3 = PlanParams(fov_h_deg=80.0, d_inspect_m=0.1, overlap=0.99)
    assert grid_spacing(p3) >= 0.4


def test_plan_room_walls_only_yields_4_face_indices():
    """벽 4면(직사각형 4개 edge)에 대해 모두 face_idx 부여."""
    params = PlanParams(scan_walls=True, scan_ceiling=False, scan_floor=False, scan_windows=False)
    plan = PathPlanner(params).plan_room(0, ROOM_RECT)
    wall_face_idxs = {w.face_idx for w in plan.waypoints if w.face_kind == FACE_WALL}
    assert wall_face_idxs == {0, 1, 2, 3}


def test_plan_room_walls_yaw_faces_inward():
    """벽 WP yaw 가 룸 안쪽을 향하지 않도록 — 대신 normal 의 반대(=벽을 향함)."""
    params = PlanParams(scan_walls=True, scan_ceiling=False, scan_floor=False)
    plan = PathPlanner(params).plan_room(0, ROOM_RECT)
    wp = next(w for w in plan.waypoints if w.face_kind == FACE_WALL and w.face_idx == 0)
    # face 0: edge (0,0)→(5,0), 안쪽 normal = (0, +1), 카메라 yaw = -normal = -π/2
    assert math.isclose(wp.yaw_rad, -math.pi / 2.0, abs_tol=1e-6)


def test_plan_room_ceiling_z_below_ceiling_clearance():
    """천장 face WP z 는 (ceiling - clearance) 이하."""
    params = PlanParams(
        scan_walls=False, scan_ceiling=True, scan_floor=False,
        ceiling_z_m=2.4, ceiling_clearance_m=0.4,
    )
    plan = PathPlanner(params).plan_room(0, ROOM_RECT)
    wps = [w for w in plan.waypoints if w.face_kind == FACE_CEILING]
    assert len(wps) > 0
    expected_z = 2.4 - 0.4
    for w in wps:
        assert math.isclose(w.z, expected_z, abs_tol=1e-6)
        # 천장 메타: cam_pitch_rad = +π/2
        assert math.isclose(w.cam_pitch_rad, math.pi / 2.0, abs_tol=1e-6)


def test_plan_room_floor_meta():
    params = PlanParams(
        scan_walls=False, scan_ceiling=False, scan_floor=True,
        floor_z_m=0.0, floor_clearance_m=0.4,
    )
    plan = PathPlanner(params).plan_room(0, ROOM_RECT)
    wps = [w for w in plan.waypoints if w.face_kind == FACE_FLOOR]
    assert len(wps) > 0
    for w in wps:
        assert math.isclose(w.z, 0.4, abs_tol=1e-6)
        assert math.isclose(w.cam_pitch_rad, -math.pi / 2.0, abs_tol=1e-6)


def test_plan_room_windows_density_higher_than_walls():
    """창호 spacing 은 벽 spacing 의 window_density_factor 배(< 1)."""
    win = [(0.0, 0.0), (1.0, 0.0), (1.0, 0.0), (0.0, 0.0)]   # degenerate, 별도 진짜 창호 사용
    win = [(1.0, 0.0), (3.0, 0.0), (3.0, 0.0), (1.0, 0.0)]
    # 정상적인 창호 폴리곤: bottom edge at y=0
    win_poly = [(1.0, -0.05), (3.0, -0.05), (3.0, 0.05), (1.0, 0.05)]
    params = PlanParams(
        scan_walls=False, scan_ceiling=False, scan_floor=False, scan_windows=True,
        window_density_factor=0.5,
    )
    plan = PathPlanner(params).plan_room(
        0, ROOM_RECT, window_polygons=[win_poly],
    )
    win_wps = [w for w in plan.waypoints if w.face_kind == FACE_WINDOW]
    assert len(win_wps) > 0
    # 창호 속도 상한 0.25 m/s
    assert all(w.speed_mps <= 0.25 + 1e-6 for w in win_wps)


def test_plan_room_unique_cell_indices_across_faces():
    """면 코드로 cell_z 인코딩 — 모든 셀 cell_idx 유니크."""
    params = PlanParams(scan_walls=True, scan_ceiling=True, scan_floor=True)
    plan = PathPlanner(params).plan_room(0, ROOM_RECT)
    keys = [w.cell_idx for w in plan.waypoints if w.purpose != "discrepancy"]
    assert len(keys) == len(set(keys)), "셀 cell_idx 가 면 간 충돌"


def test_replan_uncaptured_filters_captured():
    params = PlanParams(scan_walls=True, scan_ceiling=False, scan_floor=False)
    p = PathPlanner(params)
    plan = p.plan_room(0, ROOM_RECT)
    half = set(w.cell_idx for w in plan.waypoints[: len(plan.waypoints) // 2])
    new = p.replan_uncaptured(plan, half)
    assert all(w.cell_idx not in half for w in new.waypoints)
    assert len(new.waypoints) == len(plan.waypoints) - len(half)


def test_discrepancy_inserts_extra_dense_wp():
    """차이영역 안에 들어가는 WP 가 추가 'discrepancy' WP 와 함께 등장."""
    # 룸 중앙에 가상 차이영역
    disc = [[(2.0, 1.5), (3.0, 1.5), (3.0, 2.5), (2.0, 2.5)]]
    params = PlanParams(scan_walls=False, scan_ceiling=False, scan_floor=True)
    plan = PathPlanner(params).plan_mission(
        topology_nodes=[{"idx": 0, "polygon": [list(p) for p in ROOM_RECT]}],
        discrepancy_regions=[{"polygon": disc[0], "kind": "added", "area_m2": 1.0}],
    )
    room = plan.rooms[0]
    in_disc_purpose = [w for w in room.waypoints if w.purpose == "discrepancy"]
    assert len(in_disc_purpose) > 0, "차이영역 보조 WP 가 생성되지 않음"
