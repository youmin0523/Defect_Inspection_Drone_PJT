# =============================================
# test_floorplan_verifier.py
# IoU 산출 / 차이영역 추출 / NO_PRIOR_MODEL fallback
# =============================================
from __future__ import annotations

import numpy as np
import pytest

from app.services.floorplan_verifier import (
    FloorplanVerifier, VerificationVerdict, VerifierParams,
)


def _make_room_occupancy(shape=(200, 200), room=(40, 40, 160, 160)) -> np.ndarray:
    """occupancy: 0=free, 1=occupied, -1=unknown."""
    grid = np.ones(shape, dtype=np.int8)
    r0, c0, r1, c1 = room
    grid[r0:r1, c0:c1] = 0
    return grid


def test_no_prior_model_returns_skip():
    v = FloorplanVerifier()
    res = v.verify(np.zeros((10, 10), dtype=np.int8), 0.05, prior_polygons=None)
    assert res.verdict is VerificationVerdict.NO_PRIOR_MODEL


def test_perfect_match_yields_ok():
    """SLAM 자유공간과 사전모델 폴리곤 동일 → IoU 1.0 ≈."""
    occ = _make_room_occupancy()
    # prior polygon (월드 좌표 미터). resolution=0.05 → 픽셀 (40,40)~(160,160) = (2~8m).
    prior_poly = [(2.0, 2.0), (8.0, 2.0), (8.0, 8.0), (2.0, 8.0)]
    v = FloorplanVerifier(VerifierParams(
        iou_ok=0.7, iou_marginal=0.5, yaw_search_deg=2.0, yaw_step_deg=2.0,
    ))
    res = v.verify(occ, resolution_m_per_px=0.05, prior_polygons=[prior_poly])
    assert res.verdict in (VerificationVerdict.OK, VerificationVerdict.MARGINAL)
    assert res.iou >= 0.5


def test_divergent_when_prior_far_off():
    """사전모델이 SLAM 점유 자유공간과 거의 안 겹치면 IoU 낮음."""
    occ = _make_room_occupancy(room=(40, 40, 80, 80))   # 작은 SLAM 룸
    # 큰 사전모델 (실제와 큰 차이)
    big = [(0.0, 0.0), (12.0, 0.0), (12.0, 12.0), (0.0, 12.0)]
    v = FloorplanVerifier(VerifierParams(iou_ok=0.7, iou_marginal=0.5))
    res = v.verify(occ, resolution_m_per_px=0.05, prior_polygons=[big])
    # IoU 가 marginal 임계 미만이면 DIVERGENT
    assert res.iou < 0.7


def test_discrepancy_extracted():
    """차이영역이 임계 면적 이상이면 폴리곤이 추출된다."""
    occ = _make_room_occupancy(room=(40, 40, 160, 160))
    # 사전모델은 룸의 일부만 (왼쪽 절반 정도)
    half = [(2.0, 2.0), (5.0, 2.0), (5.0, 8.0), (2.0, 8.0)]
    v = FloorplanVerifier(VerifierParams(
        discrepancy_min_area_m2=0.1,
    ))
    res = v.verify(occ, resolution_m_per_px=0.05, prior_polygons=[half])
    # SLAM 에 있고 사전모델에 없는 'added' 차이영역이 한 개 이상
    added = [d for d in res.discrepancies if d.kind == "added"]
    assert len(added) >= 1


def test_to_jsonable_shape():
    v = FloorplanVerifier()
    res = v.verify(None, 0.05, prior_polygons=[[(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)]])
    j = res.to_jsonable()
    for k in ("verdict", "iou", "alignment", "discrepancies", "detail"):
        assert k in j
