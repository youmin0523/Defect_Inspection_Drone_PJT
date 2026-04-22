# =============================================
# app/services/temporal_filter.py
# 역할: 프레임 간 검출 추적 + 일시적 오탐 제거
#       - 시간 일관성: 연속 N프레임 중 M회 이상 검출 시 보고
#       - 즉시 보고: 고신뢰(conf > threshold) 검출은 즉시
#       - 공간 중복 억제: 동일 LiDAR 좌표 중복 보고 방지
# =============================================

from __future__ import annotations

import time
from collections import defaultdict
from typing import Dict, List, Optional


class TemporalFilter:
    """
    스트리밍 환경에서 시간 일관성 기반 필터링.

    규칙:
    - 연속 window_size 프레임 중 min_detections 이상 검출 시 보고
    - 단일 프레임이라도 conf > instant_threshold면 즉시 보고
    - 동일 3D 위치(LiDAR) 중복 보고 억제
    """

    def __init__(
        self,
        window_size: int = 5,
        min_detections: int = 2,
        instant_threshold: float = 0.85,
        spatial_dedup_radius: float = 0.3,
    ):
        self.window_size = window_size
        self.min_detections = min_detections
        self.instant_threshold = instant_threshold
        self.spatial_dedup_radius = spatial_dedup_radius

        # class → [{frame_id, bbox, conf, timestamp, det}]
        self._buffer: Dict[str, list] = defaultdict(list)
        # 보고된 하자 위치: [(class, x, y, z)]
        self._reported: List[tuple] = []

    # ── 공개 API ─────────────────────────────
    def update(
        self,
        detections: List[dict],
        frame_id: int,
        lidar_pos: Optional[dict] = None,
    ) -> List[dict]:
        """
        새 프레임 검출 결과 → 필터링 → 보고 대상만 반환.

        Args:
            detections: [{class, conf, bbox_xyxy, ...}]
            frame_id: 현재 비디오 프레임 번호
            lidar_pos: {x, y, z} 드론 LiDAR 3D 좌표 (선택)

        Returns:
            보고할 검출 리스트
        """
        approved: List[dict] = []

        for det in detections:
            cls = det["class"]

            # 즉시 보고 (고신뢰)
            if det["conf"] >= self.instant_threshold:
                if not self._is_spatial_duplicate(cls, lidar_pos):
                    approved.append(det)
                    self._record_position(cls, lidar_pos)
                continue

            # 버퍼에 추가
            self._buffer[cls].append({
                "frame_id": frame_id,
                "conf": det["conf"],
                "det": det,
            })

            # 윈도우 밖 항목 제거
            self._buffer[cls] = [
                item for item in self._buffer[cls]
                if frame_id - item["frame_id"] < self.window_size
            ]

            # 윈도우 내 충분한 검출 → 보고
            if len(self._buffer[cls]) >= self.min_detections:
                best = max(self._buffer[cls], key=lambda x: x["conf"])
                if not self._is_spatial_duplicate(cls, lidar_pos):
                    approved.append(best["det"])
                    self._record_position(cls, lidar_pos)
                self._buffer[cls] = []

        return approved

    def reset(self):
        """필터 상태 초기화 (새 세션 시작 시)."""
        self._buffer.clear()
        self._reported.clear()

    # ── 내부 ─────────────────────────────────
    def _is_spatial_duplicate(self, cls: str, pos: Optional[dict]) -> bool:
        if pos is None:
            return False
        px = pos.get("x", 0.0)
        py = pos.get("y", 0.0)
        pz = pos.get("z", 0.0)
        for rcls, rx, ry, rz in self._reported:
            if rcls != cls:
                continue
            dist = ((px - rx) ** 2 + (py - ry) ** 2 + (pz - rz) ** 2) ** 0.5
            if dist < self.spatial_dedup_radius:
                return True
        return False

    def _record_position(self, cls: str, pos: Optional[dict]):
        if pos is not None:
            self._reported.append(
                (cls, pos.get("x", 0.0), pos.get("y", 0.0), pos.get("z", 0.0))
            )
