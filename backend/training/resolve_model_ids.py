"""
후보 workspace/project slug를 Roboflow API로 직접 조회해 실제 존재/버전 확인.
get_model 가능한 정확한 model_id를 자동 확보.
실행: backend/rfenv/Scripts/python.exe resolve_model_ids.py
"""
import sys, json, urllib.request
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

KEY = "nuC9Lxr51Ds7c1IwN4Gy"

# 리서치에서 나온 (workspace, project) 후보 — M1/M2/M3 일괄 확인
CANDS = [
    # M1 structural / waterproofing
    ("builddef2", "building-defect-on-walls"),
    ("university-bswxt", "crack-bphdr"),
    ("marieam", "crack-bphdr-bl00w"),
    ("wongkinyiu", "crack-bphdr-g9koq"),
    # M2 surface / finishing
    ("pintura", "defects-on-surfaces-paint"),
    ("gurudas-patle-lapp1", "sagging-paint-defect-error-free"),
    ("sidharth-dwh8q", "paint-defect-detection-hoo99"),
    # M3 floor / window / glass
    ("capjamesg", "glass-defect-detection-fvbcu"),
    ("maruf-workspace", "glass-defect-detection-qjchk"),
    ("airlab-fqoff", "glass-xqjx8"),
    ("dylan-vaca-aovsf", "door-window-detection-pipvh"),
    ("smart-buildings", "window-detection-tzxgz"),
]

def probe(ws, proj):
    # 프로젝트 메타 (버전 목록 포함) 시도
    url = f"https://api.roboflow.com/{ws}/{proj}?api_key={KEY}"
    try:
        with urllib.request.urlopen(url, timeout=20) as r:
            data = json.loads(r.read().decode("utf-8", "replace"))
        proj_obj = data.get("project", {})
        versions = data.get("versions", [])
        vids = []
        for v in versions:
            vid = str(v.get("id", "")).split("/")[-1]
            if vid:
                vids.append(vid)
        name = proj_obj.get("name", "?")
        classes = proj_obj.get("classes", {})
        ctype = proj_obj.get("type", "?")
        print(f"[FOUND] {ws}/{proj}  name='{name}' type={ctype} versions={vids}", flush=True)
        if classes:
            print(f"        classes={list(classes.keys())}", flush=True)
        return (ws, proj, vids[0] if vids else None)
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "replace")[:160]
        print(f"[{e.code}] {ws}/{proj}  {body}", flush=True)
    except Exception as e:
        print(f"[ERR] {ws}/{proj}  {str(e)[:120]}", flush=True)
    return None

if __name__ == "__main__":
    print("=== Roboflow 후보 slug 실조회 ===", flush=True)
    ok = []
    for ws, proj in CANDS:
        r = probe(ws, proj)
        if r and r[2]:
            ok.append(r)
    print("\n=== get_model 가능 후보 ===", flush=True)
    for ws, proj, ver in ok:
        print(f"  {proj}/{ver}   (workspace={ws})", flush=True)
    if not ok:
        print("  (없음 — slug/권한 문제. 실제 Universe 링크 필요)", flush=True)
