# =============================================
# train_m3_yolo_floor_window.py
# M3-Stage1: YOLOv8m 바닥·창호 하자 검출 학습
# 클래스: floor_defect, glass_defect, frame_defect
# 출력: models_weights/m3_yolo_floor_window.onnx
# =============================================

from __future__ import annotations

import shutil
from pathlib import Path

from ultralytics import YOLO

EPOCHS_PHASE1 = 10
EPOCHS_PHASE2 = 140
BATCH = 16
IMGSZ = 640
PATIENCE = 30
LR0 = 1e-4
DATA_YAML = "configs/floor_window.yaml"
PROJECT = "runs/m3_floor_window"
WEIGHTS_DIR = Path("../models_weights")
OUTPUT_NAME = "m3_yolo_floor_window"


def train():
    model = YOLO("yolov8m.pt")
    model.train(
        data=DATA_YAML, epochs=EPOCHS_PHASE1, batch=BATCH, imgsz=IMGSZ,
        freeze=10, optimizer="AdamW", lr0=LR0,
        project=PROJECT, name="phase1_freeze", exist_ok=True,
    )

    model = YOLO(f"{PROJECT}/phase1_freeze/weights/last.pt")
    model.train(
        data=DATA_YAML, epochs=EPOCHS_PHASE2, batch=BATCH, imgsz=IMGSZ,
        optimizer="AdamW", lr0=LR0 * 0.1, lrf=0.01,
        patience=PATIENCE, warmup_epochs=5, close_mosaic=20,
        hsv_h=0.015, hsv_s=0.5, hsv_v=0.4,
        degrees=5.0, translate=0.1, scale=0.5,
        shear=2.0, perspective=0.001,
        flipud=0.0, fliplr=0.5,
        mosaic=1.0, mixup=0.1, erasing=0.3,
        project=PROJECT, name="phase2_full", exist_ok=True,
    )

    best = YOLO(f"{PROJECT}/phase2_full/weights/best.pt")
    best.export(format="onnx", opset=17, dynamic=True, simplify=True)
    WEIGHTS_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copy2(f"{PROJECT}/phase2_full/weights/best.onnx",
                 WEIGHTS_DIR / f"{OUTPUT_NAME}.onnx")
    print(f"[M3-YOLO] ONNX 저장 완료: {WEIGHTS_DIR / OUTPUT_NAME}.onnx")


if __name__ == "__main__":
    train()
