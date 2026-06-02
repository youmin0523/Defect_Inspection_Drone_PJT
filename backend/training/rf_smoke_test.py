"""
Roboflow 보조모델 end-to-end 스모크 테스트 (rfenv py3.12, CPU).
목적: (1) 가중치 실제 다운로드/로드 성공? (2) 추론 동작? (3) 예측 객체 속성명 확인
      → 어댑터 CLASS_MAP가 무음 drop 안 하도록 실제 class_name 출력.
실행: backend/rfenv/Scripts/python.exe rf_smoke_test.py
"""
import sys, glob, time, traceback
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from inference import get_model

KEY = "nuC9Lxr51Ds7c1IwN4Gy"

# 채택/후보 모델 — 로드+추론 실측
MODELS = [
    "crack-bphdr/2",                 # M1 균열 (채택)
    "glass-defect-detection-fvbcu/2",# M3 유리 (채택)
    "wall-ceiling-floor-m6bao/1",    # M4 context (채택)
    "windows-instance-segmentation/5",# M5 창호 (채택)
    "thermal-images-in-building-inspection/3", # thermal (채택)
    "wall-defects/2",                # M2 표면 (신규 후보, CC BY 4.0)
]

# 스모크용 테스트 이미지(아무거나 — 로드/추론 확인 목적)
imgs = sorted(glob.glob(
    "test_external/ext_surface/test/images/*.jpg"))[:3]
if not imgs:
    imgs = sorted(glob.glob("uploads/chat/*.jpg"))[:3]
print(f"[smoke] test imgs: {len(imgs)}", flush=True)
for i in imgs:
    print("   ", i, flush=True)

results = {}
for mid in MODELS:
    print(f"\n=== {mid} ===", flush=True)
    t0 = time.time()
    try:
        m = get_model(model_id=mid, api_key=KEY)
        print(f"  LOADED in {time.time()-t0:.1f}s", flush=True)
    except Exception as e:
        print(f"  LOAD FAIL: {str(e)[:200]}", flush=True)
        traceback.print_exc()
        results[mid] = "LOAD_FAIL"
        continue
    if not imgs:
        results[mid] = "LOADED(no img)"
        continue
    try:
        t1 = time.time()
        res = m.infer(imgs[0], confidence=0.05)
        preds = res[0].predictions
        print(f"  INFER {time.time()-t1:.2f}s, {len(preds)} preds", flush=True)
        for p in preds[:5]:
            cn = getattr(p, "class_name", None)
            cl = getattr(p, "class", None)
            print(f"    class_name={cn!r} class={cl!r} conf={getattr(p,'confidence',None):.3f} "
                  f"x={getattr(p,'x',None):.0f} y={getattr(p,'y',None):.0f}", flush=True)
        results[mid] = f"OK({len(preds)} preds)"
    except Exception as e:
        print(f"  INFER FAIL: {str(e)[:200]}", flush=True)
        traceback.print_exc()
        results[mid] = "INFER_FAIL"

print("\n===== SMOKE SUMMARY =====", flush=True)
for k, v in results.items():
    print(f"  {k}: {v}", flush=True)
