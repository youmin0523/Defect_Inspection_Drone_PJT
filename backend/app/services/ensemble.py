# =============================================
# app/services/ensemble.py
# 역할: 크로스 모델 NMS + PatchCore 앙상블 + 신뢰도 교정
#       - cross_model_nms: 서로 다른 모델 간 중복 검출 제거
#       - ensemble_with_patchcore: PatchCore로 YOLO/ResNet 저신뢰 검출 승격
#       - compute_combined_confidence: 독립 사건 결합 신뢰도
# =============================================

from __future__ import annotations

from typing import List, Optional

import numpy as np


def _iou(box_a: List[float], box_b: List[float]) -> float:
    """두 xyxy bbox의 IoU 계산."""
    x1 = max(box_a[0], box_b[0])
    y1 = max(box_a[1], box_b[1])
    x2 = min(box_a[2], box_b[2])
    y2 = min(box_a[3], box_b[3])
    inter = max(0, x2 - x1) * max(0, y2 - y1)
    area_a = (box_a[2] - box_a[0]) * (box_a[3] - box_a[1])
    area_b = (box_b[2] - box_b[0]) * (box_b[3] - box_b[1])
    return inter / (area_a + area_b - inter + 1e-6)


def cross_model_nms(
    detections: List[dict],
    iou_threshold: float = 0.5,
) -> List[dict]:
    """
    서로 다른 모델의 검출 결과 간 중복 제거.

    규칙:
    1. 동일 class 중복 → 높은 confidence 유지
    2. 다른 class 겹침 → 둘 다 보고 (복합 하자 가능)
    """
    if len(detections) <= 1:
        return detections

    # 동일 class끼리 그룹핑
    by_class: dict = {}
    for det in detections:
        by_class.setdefault(det["class"], []).append(det)

    result: List[dict] = []
    for cls, dets in by_class.items():
        if len(dets) <= 1:
            result.extend(dets)
            continue

        # 같은 class 내에서 NMS
        sorted_dets = sorted(dets, key=lambda d: d["conf"], reverse=True)
        keep: List[dict] = []
        for det in sorted_dets:
            is_dup = False
            for kept in keep:
                if _iou(det["bbox_xyxy"], kept["bbox_xyxy"]) >= iou_threshold:
                    is_dup = True
                    break
            if not is_dup:
                keep.append(det)
        result.extend(keep)

    return result


def ensemble_with_patchcore(
    detections: List[dict],
    anomaly_mask: Optional[np.ndarray],
    anomaly_score: float,
    low_conf_threshold: float = 0.35,
) -> List[dict]:
    """
    PatchCore 이상 탐지와 교차 검증.

    저신뢰 검출(conf < low_conf_threshold)이지만 PatchCore가
    동일 영역을 이상으로 판정 → confidence 승격.
    """
    if anomaly_mask is None:
        return detections

    h, w = anomaly_mask.shape[:2]

    for det in detections:
        if det["conf"] >= low_conf_threshold:
            continue

        x1, y1, x2, y2 = [int(v) for v in det["bbox_xyxy"]]
        x1, y1 = max(0, x1), max(0, y1)
        x2, y2 = min(w, x2), min(h, y2)

        if x2 <= x1 or y2 <= y1:
            continue

        roi_score = anomaly_mask[y1:y2, x1:x2].mean() / 255.0
        if roi_score > 0.5:
            # 독립 사건 결합
            combined = 1.0 - (1.0 - det["conf"]) * (1.0 - roi_score)
            det["conf"] = min(1.0, combined)
            det["ensemble_boosted"] = True

    return detections


def compute_combined_confidence(conf1: float, conf2: float) -> float:
    """두 독립 검출의 결합 신뢰도."""
    return 1.0 - (1.0 - conf1) * (1.0 - conf2)
