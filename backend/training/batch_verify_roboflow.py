"""
Roboflow 학습모델 일괄 검증 (단일 프로세스 순차, CPU 전용).
각 모델을 우리 test 이미지로 추론해 검출률(Recall proxy)·클래스 분포 측정.
결과: backend/training/roboflow_verify_results.md
실행: backend/rfenv/Scripts/python.exe batch_verify_roboflow.py
"""
import sys, glob
from datetime import datetime
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from inference import get_model

KEY = "nuC9Lxr51Ds7c1IwN4Gy"
N = 40
CONF = 0.05

JOBS = [
    ("thermal-idt-6cls(thermalval)", "thermal-images-in-building-inspection/3",
     "datasets/thermal_yolo/images/val/*.jpg"),
    ("M1-building-defect(crack)", "building-defect-on-walls/4",
     "test_external/ext_crack/test/images/*.jpg"),
    ("M1-crack-seg(crack)", "crack-bphdr/2",
     "test_external/ext_crack/test/images/*.jpg"),
    ("M3-glass-capjamesg(glass)", "glass-defect-detection-fvbcu/3",
     "test_external/ext_glass/test/images/*.jpg"),
    ("M4-room-detection(surface)", "room-detection-tfaxd/1",
     "test_external/ext_surface/test/images/*.jpg"),
    ("M4-wall-ceiling-floor(surface)", "wall-ceiling-floor-m6bao/1",
     "test_external/ext_surface/test/images/*.jpg"),
    ("M5-walls-door(surface)", "walls-door-detection/1",
     "test_external/ext_surface/test/images/*.jpg"),
]

OUT = "roboflow_verify_results.md"


def run_job(label, mid, pattern):
    imgs = glob.glob(pattern)[:N]
    if not imgs:
        return f"| {label} | {mid} | 0 | - | 이미지없음 |"
    try:
        model = get_model(model_id=mid, api_key=KEY)
    except Exception as e:
        return f"| {label} | {mid} | - | LOAD FAIL | {str(e)[:50]} |"
    hit, total = 0, 0
    cls = {}
    for p in imgs:
        try:
            res = model.infer(p, confidence=CONF)
            preds = res[0].predictions
            if preds:
                hit += 1
            total += len(preds)
            for pr in preds:
                c = getattr(pr, "class_name", None) or getattr(pr, "class", "?")
                cls[c] = cls.get(c, 0) + 1
        except Exception:
            pass
    rate = 100.0 * hit / len(imgs)
    top = sorted(cls.items(), key=lambda x: -x[1])[:4]
    clsstr = ", ".join(f"{k}:{v}" for k, v in top)
    line = f"| {label} | {mid} | {len(imgs)} | {hit}({rate:.0f}%)/{total} | {clsstr} |"
    print(line, flush=True)
    return line


def main():
    print(f"=== batch verify start {datetime.now():%H:%M:%S} conf={CONF} ===", flush=True)
    rows = []
    for label, mid, pat in JOBS:
        print(f"[run] {label} ...", flush=True)
        rows.append(run_job(label, mid, pat))
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(f"# Roboflow 학습모델 검증 (CPU, conf={CONF}, {datetime.now():%Y-%m-%d %H:%M})\n\n")
        f.write("검출률 = test 이미지 중 1건+ 검출 비율(Recall proxy). 우리 모델과 ensemble 보조 기여 가늠용.\n\n")
        f.write("| 모델 | model_id | N | 검출(장%)/건 | 상위클래스 |\n|---|---|---|---|---|\n")
        for r in rows:
            f.write(r + "\n")
    print(f"=== done {datetime.now():%H:%M:%S} -> {OUT} ===", flush=True)


if __name__ == "__main__":
    main()
