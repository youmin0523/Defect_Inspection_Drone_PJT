# =============================================
# test_obstacle_avoider.py
# DWA 풍 후보 평가, 무특징 정책, 안전회랑 침입 케이스 검증
# =============================================
from __future__ import annotations

import numpy as np
import pytest

from app.services.obstacle_avoider import (
    AvoidParams, ObstacleAvoider, VelocityCommand,
)


def _avoider() -> ObstacleAvoider:
    return ObstacleAvoider(AvoidParams(
        voxel_size_m=0.10,
        safety_radius_m=0.35,
        speed_max_room_mps=0.5,
        horizon_sec=1.0,
        horizon_steps=10,
        slam_confidence_floor=0.4,
        candidate_grid=5,
    ))


def test_low_slam_confidence_forces_hover():
    av = _avoider()
    target = VelocityCommand(vx=0.5, vy=0.0, vz=0.0)
    ev = av.evaluate(target, current_pose_xyz=(0, 0, 1), slam_confidence=0.1)
    assert not ev.safe
    assert ev.reason == "slam_low_confidence"
    assert ev.chosen.vx == 0.0 and ev.chosen.vy == 0.0


def test_clear_corridor_passes_target():
    av = _avoider()
    target = VelocityCommand(vx=0.4, vy=0.0, vz=0.0)
    ev = av.evaluate(target, current_pose_xyz=(0, 0, 1), slam_confidence=0.9)
    assert ev.safe
    # 후보 중 목표와 가까운 속도 선택 (방향 일치 우선)
    assert ev.chosen.vx > 0.1


def test_obstacle_in_path_chooses_alternate_or_hover():
    av = _avoider()
    # 전방 1m 지점에 점군 — 5x5x5 voxel 채움
    pts = []
    for ix in range(5):
        for iy in range(5):
            for iz in range(5):
                pts.append((1.0 + ix * 0.05, iy * 0.05 - 0.1, 1.0 + iz * 0.05 - 0.1))
    av.update_pointcloud(np.array(pts))
    target = VelocityCommand(vx=0.5, vy=0.0, vz=0.0)
    ev = av.evaluate(target, current_pose_xyz=(0, 0, 1), slam_confidence=0.9)
    # 전방 직진은 위험 — 측면 이동 또는 hover. 전진 vx 가 줄어들거나 0
    assert ev.chosen.vx < target.vx


def test_speed_limit_clipped_in_doorway():
    av = _avoider()
    target = VelocityCommand(vx=1.0, vy=0.0, vz=0.0)
    ev = av.evaluate(target, current_pose_xyz=(0, 0, 1), slam_confidence=0.9, in_doorway=True)
    assert abs(ev.chosen.vx) <= av.params.speed_max_doorway_mps + 1e-6


def test_voxel_decay_removes_old_points():
    av = _avoider()
    pts = np.array([(1.0, 0.0, 1.0), (1.05, 0.0, 1.0)])
    av.update_pointcloud(pts)
    assert av.voxel_count() > 0
    # 시간 경과 후 manually decay 호출 — params.voxel_decay_sec 이상이 지났다고 가정
    av.params.voxel_decay_sec = 0.0001
    av.update_pointcloud(np.zeros((0, 3)))   # 다른 점군 (없음)
    # 이전 voxel 이 stale 로 제거됨
    assert av.voxel_count() == 0
