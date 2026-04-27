# =============================================
# train_m1_yolo_structural.py
# M1-Stage1: YOLOv8m 구조·방수 하자 검출 학습
# 클래스: crack(균열), caulking_defect(코킹불량), waterproof_defect(방수/누수)
# 출력: models_weights/m1_yolo_structural.onnx
#
# 사용법:
#   cd backend/training
#   python train_m1_yolo_structural.py
# =============================================

from __future__ import annotations

import shutil
from pathlib import Path

from ultralytics import YOLO


# ── 하이퍼파라미터 ────���───────────────────────
EPOCHS_PHASE1 = 10          # backbone freeze
EPOCHS_PHASE2 = 190         # full unfreeze
BATCH = 16
IMGSZ = 640
PATIENCE = 30
LR0 = 1e-4
LRF = 0.01                 # cosine 최종 LR 비율
WARMUP_EPOCHS = 5
CLOSE_MOSAIC = 20           # 마지막 20 epoch에서 mosaic 끔
CONF = 0.15                 # 검출 임계값 (높은 재현율)

DATA_YAML = "configs/structural.yaml"
PROJECT = "runs/m1_structural"
WEIGHTS_DIR = Path("../models_weights")
OUTPUT_NAME = "m1_yolo_structural"


def train():
    """2-Phase 학습: backbone freeze → full unfreeze."""
    print("=" * 60)
    print("[M1-YOLO] Phase 1: Backbone Freeze (10 epochs)")
    print("=" * 60)

    model = YOLO("yolov8m.pt")
    model.train(
        data=DATA_YAML,
        epochs=EPOCHS_PHASE1,
        batch=BATCH,
        imgsz=IMGSZ,
        freeze=10,
        optimizer="AdamW",
        lr0=LR0,
        project=PROJECT,
        name="phase1_freeze",
        exist_ok=True,
    )

    print("=" * 60)
    print("[M1-YOLO] Phase 2: Full Unfreeze (190 epochs)")
    print("=" * 60)

    model = YOLO(f"{PROJECT}/phase1_freeze/weights/last.pt")
    model.train(
        data=DATA_YAML,
        epochs=EPOCHS_PHASE2,
        batch=BATCH,
        imgsz=IMGSZ,
        optimizer="AdamW",
        lr0=LR0 * 0.1,
        lrf=LRF,
        patience=PATIENCE,
        warmup_epochs=WARMUP_EPOCHS,
        close_mosaic=CLOSE_MOSAIC,
        # 증강
        hsv_h=0.015,
        hsv_s=0.5,
        hsv_v=0.4,
        degrees=5.0,
        translate=0.1,
        scale=0.5,
        shear=2.0,
        perspective=0.001,
        flipud=0.0,
        fliplr=0.5,
        mosaic=1.0,
        mixup=0.1,
        erasing=0.3,
        project=PROJECT,
        name="phase2_full",
        exist_ok=True,
    )

    print("=" * 60)
    print("[M1-YOLO] ONNX 변환")
    print("=" * 60)

    best_path = f"{PROJECT}/phase2_full/weights/best.pt"
    export_to_onnx(best_path)


def export_to_onnx(pt_path: str):
    """학습된 .pt → ONNX 변환 후 models_weights/로 복사."""
    model = YOLO(pt_path)
    model.export(
        format="onnx",
        opset=17,
        dynamic=True,
        simplify=True,
        half=False,      # FP32 (FP16은 배포 시 별도 양자화)
    )

    onnx_src = pt_path.replace(".pt", ".onnx")
    onnx_dst = WEIGHTS_DIR / f"{OUTPUT_NAME}.onnx"
    WEIGHTS_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copy2(onnx_src, onnx_dst)
    print(f"[M1-YOLO] ONNX 저장 완료: {onnx_dst}")


if __name__ == "__main__":
    train()
