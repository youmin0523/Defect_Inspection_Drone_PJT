"""
Roboflow 학습된 모델 검증 하니스 (CPU 전용 — GPU 학습 무충돌).
확정된 model_id를 받아 로드 + test 이미지 추론 + 검출률(Recall proxy) 출력.

사용:
  backend/rfenv/Scripts/python.exe verify_roboflow_model.py <model_id> [이미지glob]
예:
  ... verify_roboflow_model.py thermal-images-in-building-inspection/3 "datasets/thermal_yolo/images/val/*.jpg"
"""
import sys, glob
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from inference import get_model

KEY = "nuC9Lxr51Ds7c1IwN4Gy"

def main():
    if len(sys.argv) < 2:
        print("usage: verify_roboflow_model.py <model_id> [image_glob]")
        return
    mid = sys.argv[1]
    pattern = sys.argv[2] if len(sys.argv) > 2 else "datasets/thermal_yolo/images/val/*.jpg"

    print(f"[load] get_model('{mid}') CPU ...", flush=True)
    model = get_model(model_id=mid, api_key=KEY)
    print("[load] OK", flush=True)

    imgs = glob.glob(pattern)[:60]
    if not imgs:
        print(f"[warn] 이미지 없음: {pattern}", flush=True)
        return
    hit, total_pred = 0, 0
    cls_count = {}
    for p in imgs:
        try:
            res = model.infer(p)
            preds = res[0].predictions
            n = len(preds)
            total_pred += n
            if n > 0:
                hit += 1
            for pr in preds:
                c = getattr(pr, "class_name", None) or getattr(pr, "class", "?")
                cls_count[c] = cls_count.get(c, 0) + 1
        except Exception as e:
            print(f"  infer fail {p}: {str(e)[:80]}", flush=True)
    rate = 100.0 * hit / len(imgs) if imgs else 0
    print(f"[result] {mid}: {len(imgs)}장 중 {hit}장 검출(={rate:.1f}%), 총 예측 {total_pred}건", flush=True)
    print(f"[classes] {cls_count}", flush=True)

if __name__ == "__main__":
    main()
