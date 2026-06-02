"""대체 후보 검증 (LOAD FAIL/매핑불가 모델 교체용). CPU 전용."""
import sys, glob
from datetime import datetime
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from inference import get_model
KEY="nuC9Lxr51Ds7c1IwN4Gy"
N=30; CONF=0.05
JOBS=[
    # M3 glass 대체 (capjamesg LOAD FAIL 대체)
    ("M3-glass-maruf","glass-defect-detection-qjchk/1","test_external/ext_glass/test/images/*.jpg"),
    ("M3-glass-airlab","glass-xqjx8/1","test_external/ext_glass/test/images/*.jpg"),
    # M5 frame/window-door 대체 (walls-door 클래스명 깨짐 대체)
    ("M5-windows-inst","windows-instance-segmentation/5","test_external/ext_surface/test/images/*.jpg"),
    ("M5-window-seg","window-segmentation/1","test_external/ext_surface/test/images/*.jpg"),
    ("M5-smart-window","window-detection-tzxgz/1","test_external/ext_surface/test/images/*.jpg"),
    ("M5-door-window-dylan","door-window-detection-pipvh/1","test_external/ext_surface/test/images/*.jpg"),
    # M1 crack 추가후보
    ("M1-crack-wongkinyiu","crack-bphdr-g9koq/1","test_external/ext_crack/test/images/*.jpg"),
    ("M1-crack-marieam","crack-bphdr-bl00w/1","test_external/ext_crack/test/images/*.jpg"),
    # M2 surface 후보
    ("M2-paint-pintura","defects-on-surfaces-paint/1","test_external/ext_surface/test/images/*.jpg"),
]
OUT="roboflow_verify_alt.md"
def run(label,mid,pat):
    imgs=glob.glob(pat)[:N]
    if not imgs: return f"| {label} | {mid} | 0 | - | 이미지없음 |"
    try: model=get_model(model_id=mid,api_key=KEY)
    except Exception as e: return f"| {label} | {mid} | - | LOAD FAIL | {str(e)[:45]} |"
    hit=total=0; cls={}
    for p in imgs:
        try:
            preds=model.infer(p,confidence=CONF)[0].predictions
            if preds: hit+=1
            total+=len(preds)
            for pr in preds:
                c=getattr(pr,"class_name",None) or getattr(pr,"class","?")
                cls[c]=cls.get(c,0)+1
        except Exception: pass
    rate=100.0*hit/len(imgs)
    top=", ".join(f"{k}:{v}" for k,v in sorted(cls.items(),key=lambda x:-x[1])[:4])
    line=f"| {label} | {mid} | {len(imgs)} | {hit}({rate:.0f}%)/{total} | {top} |"
    print(line,flush=True); return line
print(f"=== alt verify start {datetime.now():%H:%M:%S} ===",flush=True)
rows=[run(l,m,p) for l,m,p in JOBS]
with open(OUT,"w",encoding="utf-8") as f:
    f.write(f"# Roboflow 대체후보 검증 (CPU conf={CONF}, {datetime.now():%Y-%m-%d %H:%M})\n\n")
    f.write("| 모델 | model_id | N | 검출(장%)/건 | 상위클래스 |\n|---|---|---|---|---|\n")
    for r in rows: f.write(r+"\n")
print(f"=== done {datetime.now():%H:%M:%S} -> {OUT} ===",flush=True)
