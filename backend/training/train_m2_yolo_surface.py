# =============================================
# train_m2_yolo_surface.py
# M2-Stage1: YOLOv8m 마감·표면 하자 검출 학습
# 클래스: surface_defect_wall(벽/천장 표면), baseboard_defect(걸레받이)
# 출력: models_weights/m2_yolo_surface.onnx
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
DATA_YAML = "configs/surface.yaml"
PROJECT = "runs/m2_surface"
WEIGHTS_DIR = Path("../models_weights")
OUTPUT_NAME = "m2_yolo_surface"


def train():
    # Phase 1: freeze
    model = YOLO("yolov8m.pt")
    model.train(
        data=DATA_YAML, epochs=EPOCHS_PHASE1, batch=BATCH, imgsz=IMGSZ,
        freeze=10, optimizer="AdamW", lr0=LR0,
        project=PROJECT, name="phase1_freeze", exist_ok=True,
    )

    # Phase 2: unfreeze — 표면 하자 특화 증강
    model = YOLO(f"{PROJECT}/phase1_freeze/weights/last.pt")
    model.train(
        data=DATA_YAML, epochs=EPOCHS_PHASE2, batch=BATCH, imgsz=IMGSZ,
        optimizer="AdamW", lr0=LR0 * 0.1, lrf=0.01,
        patience=PATIENCE, warmup_epochs=5, close_mosaic=20,
        # 마감·표면 특화 증강 (강한 색상 변형)
        hsv_h=0.02, hsv_s=0.6, hsv_v=0.5,
        degrees=5.0, translate=0.1, scale=0.5,
        shear=2.0, perspective=0.001,
        flipud=0.0, fliplr=0.5,
        mosaic=1.0, mixup=0.15, erasing=0.3,
        project=PROJECT, name="phase2_full", exist_ok=True,
    )

    # ONNX 변환
    best = YOLO(f"{PROJECT}/phase2_full/weights/best.pt")
    best.export(format="onnx", opset=17, dynamic=True, simplify=True)
    onnx_src = f"{PROJECT}/phase2_full/weights/best.onnx"
    onnx_dst = WEIGHTS_DIR / f"{OUTPUT_NAME}.onnx"
    WEIGHTS_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copy2(onnx_src, onnx_dst)
    print(f"[M2-YOLO] ONNX 저장 완료: {onnx_dst}")


if __name__ == "__main__":
    train()
