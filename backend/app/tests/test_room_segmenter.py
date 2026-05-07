# =============================================
# test_room_segmenter.py
# synthetic occupancy grid 에서 룸 분리 + 도어웨이 검출 회귀 테스트
# =============================================
from __future__ import annotations

import numpy as np
import pytest

from app.services.room_segmenter import RoomSegmenter, SegmenterParams


def _make_two_rooms_with_doorway() -> np.ndarray:
    """
    격자 200x300 픽셀 (10m x 15m, 0.05m/px). 두 룸이 폭 0.85m 통로(픽셀 17)로 연결.
    벽=1(점유), 자유공간=0, 외부=1.
    """
    grid = np.ones((200, 300), dtype=np.int8)
    # 룸 A: row 30~170, col 30~140
    grid[30:170, 30:140] = 0
    # 룸 B: row 30~170, col 160~270
    grid[30:170, 160:270] = 0
    # 도어웨이: 두 룸 사이 폭 0.85m → 17픽셀 (col 140~160 사이의 좁은 통로)
    grid[91:108, 140:160] = 0     # 17픽셀 폭 → 0.85m
    return grid


def test_segment_finds_two_rooms():
    grid = _make_two_rooms_with_doorway()
    seg = RoomSegmenter(SegmenterParams(
        resolution_m_per_px=0.05, drone_radius_m=0.185,
        doorway_min_m=0.70, doorway_max_m=1.00,
        min_room_area_m2=1.0,
    ))
    topo = seg.segment(grid)
    assert len(topo.nodes) == 2, f"룸 2개 검출 기대, 실제 {len(topo.nodes)}"


def test_segment_finds_doorway_edge():
    grid = _make_two_rooms_with_doorway()
    seg = RoomSegmenter(SegmenterParams(
        resolution_m_per_px=0.05, drone_radius_m=0.185,
        doorway_min_m=0.70, doorway_max_m=1.00,
    ))
    topo = seg.segment(grid)
    assert len(topo.edges) >= 1, "도어웨이 엣지 미검출"
    edge = topo.edges[0]
    assert 0.70 <= edge.width_m <= 1.05, f"도어웨이 폭 임계 위반: {edge.width_m}"


def test_segment_too_small_rooms_filtered():
    """min_room_area_m2 미만 자유공간은 룸으로 채택되지 않음."""
    grid = np.ones((50, 50), dtype=np.int8)
    grid[20:25, 20:25] = 0   # 0.25m × 0.25m = 0.0625㎡ — min 1.5㎡ 미달
    seg = RoomSegmenter(SegmenterParams(
        resolution_m_per_px=0.05, min_room_area_m2=1.5,
    ))
    topo = seg.segment(grid)
    assert len(topo.nodes) == 0


def test_empty_input_safe():
    seg = RoomSegmenter()
    topo = seg.segment(np.zeros((0, 0), dtype=np.int8))
    assert topo.nodes == [] and topo.edges == []


def test_to_jsonable_shape():
    grid = _make_two_rooms_with_doorway()
    seg = RoomSegmenter(SegmenterParams(resolution_m_per_px=0.05))
    topo = seg.segment(grid)
    j = topo.to_jsonable()
    assert "nodes" in j and "edges" in j
    if j["nodes"]:
        n = j["nodes"][0]
        for k in ("idx", "name", "polygon", "area", "centroid"):
            assert k in n
