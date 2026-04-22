# =============================================
# eval/evaluate_all.py
# 20종 하자 검출 통합 평가 스크립트
# ONNX 모델 기준으로 모든 모델 성능 측정
#
# 사용법:
#   cd backend/training
#   python eval/evaluate_all.py
#   python eval/evaluate_all.py --model m1    # 특정 모델만
# =============================================

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import cv2
import numpy as np

# 상위 디렉토리의 app 모듈 사용
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from app.services.onnx_inference import ONNXResNetClassifier, ONNXYoloDetector


WEIGHTS_DIR = Path("../models_weights")

# ── 평가 목표 (Pass/Fail 기준) ──
TARGETS = {
    "M1-YOLO": {"metric": "recall", "threshold": 0.95},
    "M1-ResNet": {"metric": "accuracy", "threshold": 0.90},
    "M2-YOLO": {"metric": "recall", "threshold": 0.93},
    "M2-ResNet": {"metric": "accuracy", "threshold": 0.88},
    "M3-YOLO": {"metric": "recall", "threshold": 0.93},
    "M3-ResNet": {"metric": "accuracy", "threshold": 0.88},
}


def evaluate_yolo_model(
    onnx_path: str,
    test_images_dir: str,
    test_labels_dir: str,
    class_names: list,
    conf: float = 0.25,
) -> dict:
    """YOLO ONNX 모델 평가: mAP, Recall, Precision."""
    detector = ONNXYoloDetector(onnx_path, class_names)

    total_gt = 0
    total_tp = 0
    total_fp = 0

    images_dir = Path(test_images_dir)
    labels_dir = Path(test_labels_dir)

    for img_path in sorted(images_dir.glob("*.jpg")):
        label_path = labels_dir / img_path.with_suffix(".txt").name
        if not label_path.exists():
            continue

        img = cv2.imread(str(img_path))
        if img is None:
            continue

        # Ground Truth 로드 (YOLO 포맷)
        gt_labels = []
        for line in label_path.read_text().strip().split("\n"):
            if not line.strip():
                continue
            parts = line.strip().split()
            gt_labels.append(int(parts[0]))
        total_gt += len(gt_labels)

        # 예측
        dets = detector.predict(img, conf=conf)
        pred_classes = [d["class_id"] for d in dets]

        # 단순 매칭 (클래스 기반, IoU 생략 — 빠른 평가용)
        matched = set()
        for pc in pred_classes:
            if pc in gt_labels and pc not in matched:
                total_tp += 1
                matched.add(pc)
            else:
                total_fp += 1

    recall = total_tp / (total_gt + 1e-6)
    precision = total_tp / (total_tp + total_fp + 1e-6)
    f1 = 2 * precision * recall / (precision + recall + 1e-6)

    return {
        "total_gt": total_gt,
        "total_tp": total_tp,
        "total_fp": total_fp,
        "recall": round(recall, 4),
        "precision": round(precision, 4),
        "f1": round(f1, 4),
    }


def evaluate_resnet_model(
    onnx_path: str,
    test_dir: str,
    class_names: list,
) -> dict:
    """ResNet ONNX 분류기 평가: Accuracy, Per-class accuracy."""
    classifier = ONNXResNetClassifier(onnx_path, class_names)

    correct = 0
    total = 0
    per_class_correct = {c: 0 for c in class_names}
    per_class_total = {c: 0 for c in class_names}

    for cls_name in class_names:
        cls_dir = Path(test_dir) / cls_name
        if not cls_dir.exists():
            continue
        for img_path in cls_dir.glob("*.jpg"):
            img = cv2.imread(str(img_path))
            if img is None:
                continue
            pred_cls, pred_conf, _ = classifier.classify(img)
            total += 1
            per_class_total[cls_name] += 1
            if pred_cls == cls_name:
                correct += 1
                per_class_correct[cls_name] += 1

    accuracy = correct / (total + 1e-6)
    per_class_acc = {
        c: round(per_class_correct[c] / (per_class_total[c] + 1e-6), 4)
        for c in class_names
    }

    return {
        "total": total,
        "correct": correct,
        "accuracy": round(accuracy, 4),
        "per_class_accuracy": per_class_acc,
    }


def run_evaluation(model_filter: str = None):
    """전체 평가 실행."""
    results = {}

    evaluations = [
        ("M1-YOLO", "m1_yolo_structural.onnx",
         "datasets/structural/images/test", "datasets/structural/labels/test",
         ["crack", "caulking_defect", "waterproof_defect"], "yolo"),
        ("M1-ResNet", "m1_resnet_crack_classifier.onnx",
         "datasets/structural_crops/test", None,
         ["crack_structural", "crack_finishing"], "resnet"),
        ("M2-YOLO", "m2_yolo_surface.onnx",
         "datasets/surface/images/test", "datasets/surface/labels/test",
         ["surface_defect_wall", "baseboard_defect"], "yolo"),
        ("M2-ResNet", "m2_resnet_surface_classifier.onnx",
         "datasets/surface_crops/test", None,
         ["wallpaper_seam", "wallpaper_bubble", "paint_stain", "scratch", "baseboard_damage"], "resnet"),
        ("M3-YOLO", "m3_yolo_floor_window.onnx",
         "datasets/floor_window/images/test", "datasets/floor_window/labels/test",
         ["floor_defect", "glass_defect", "frame_defect"], "yolo"),
        ("M3-ResNet", "m3_resnet_floor_window_classifier.onnx",
         "datasets/floor_window_crops/test", None,
         ["floor_stain", "grout_defect", "glass_scratch", "frame_paint_defect"], "resnet"),
    ]

    for name, weight_file, test_path, label_path, classes, model_type in evaluations:
        if model_filter and not name.lower().startswith(model_filter.lower()):
            continue

        onnx_path = WEIGHTS_DIR / weight_file
        if not onnx_path.exists():
            print(f"  [{name}] SKIP — {onnx_path} 없음")
            continue

        print(f"\n평가 중: {name}")
        if model_type == "yolo":
            result = evaluate_yolo_model(str(onnx_path), test_path, label_path, classes)
        else:
            result = evaluate_resnet_model(str(onnx_path), test_path, classes)

        results[name] = result

        # Pass/Fail 판정
        target = TARGETS.get(name, {})
        metric_name = target.get("metric", "recall")
        threshold = target.get("threshold", 0.9)
        actual = result.get(metric_name, 0.0)
        status = "PASS" if actual >= threshold else "FAIL"
        print(f"  {metric_name}={actual:.4f} (목표>={threshold}) [{status}]")

    # 결과 저장
    out_path = Path("eval/evaluation_results.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"\n결과 저장: {out_path}")

    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="20종 하자 모델 통합 평가")
    parser.add_argument("--model", type=str, default=None, help="특정 모델만 (예: m1, m2)")
    args = parser.parse_args()
    run_evaluation(args.model)
