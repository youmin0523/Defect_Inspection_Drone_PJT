"""
Roboflow Universe 대체 데이터셋 export 다운로드 검증.
각 후보의 project meta(versions/classes/license) 확인 후, 각 버전의 yolov8 export link를
실제로 GET 하여 ZIP(PK 헤더) 여부 판정. ZIP_OK 만 채택.
실행: backend/rfenv/Scripts/python.exe training/verify_alt_export.py
"""
import sys, requests, json
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

KEY = "nuC9Lxr51Ds7c1IwN4Gy"
API = "https://api.roboflow.com"

# (label, workspace, project)
CANDS = [
    # M4 context: wall/ceiling/floor
    ("M4", "wallceilingfloor", "wall-ceiling-floor-m6bao"),
    ("M4", "x-aqdd1", "wall-floor-bjbya"),
    ("M4", "part2val", "wall-floor-hzf1m"),
    ("M4", "part1-3dlw1", "wall-floor-vc6qx"),
    ("M4", "test-3vtzt", "mit-indoor-semantic-segmentation"),
    ("M4", "celebal-technologies", "walls-floor-detection"),
    ("M4", "celebal-henxz", "wall-ceiling"),
    ("M4", "park-jong-il-k1lxw", "wall-floor-ceiling-recognition"),
    # furniture: built-in furniture / cabinet / appliance / countertop
    ("furn", "ai2thor", "ai2thor-kitchen-items-actions"),
    ("furn", "cabinet-detection", "floorplan-cabinet-detection"),
    ("furn", "furniture-d9qab", "furniture-hpuyb"),
    ("furn", "furniture-pp9ke", "furniture-o6003"),
    ("furn", "projects-iucr4", "appliances"),
    ("furn", "kitchenobjectdetection", "kitchen-object-detection-acyvk"),
    # M3 floor_window: glass/window defect
    ("M3", "maruf-workspace", "glass-defect-detection-qjchk"),
    ("M3", "yolo-0avst", "scratch-fvsd0"),
    # thermal: building thermal insulation/moisture (NOT solar)
    ("thermal", "murtazakhan", "thermal-anomaly-detection-1"),
    ("thermal", "university-of-ottawa-thermal-anomaly", "thermal-anomaly-test-1"),
    ("thermal", "solveview", "thermal-defects"),
]


def get_meta(ws, proj):
    try:
        r = requests.get(f"{API}/{ws}/{proj}", params={"api_key": KEY}, timeout=30)
        if r.status_code != 200:
            return None, f"meta {r.status_code}"
        return r.json(), None
    except Exception as e:
        return None, f"meta err {str(e)[:40]}"


def check_export(ws, proj, ver):
    try:
        r = requests.get(f"{API}/{ws}/{proj}/{ver}/yolov8",
                         params={"api_key": KEY}, timeout=40)
        if r.status_code != 200:
            return f"v{ver} HTTP {r.status_code}", None
        j = r.json()
        link = (j.get("export") or {}).get("link")
        cls = (j.get("version") or {}).get("classes") or (j.get("project") or {}).get("classes")
        if not link:
            return f"v{ver} NO_LINK", cls
        z = requests.get(link, timeout=120)
        if z.content[:2] == b"PK":
            return f"v{ver} ZIP_OK", cls
        # check 404/NoSuchKey
        head = z.content[:80].decode("utf-8", "replace")
        tag = "404" if z.status_code == 404 or "NoSuchKey" in head else f"BROKEN({z.status_code})"
        return f"v{ver} EXPORT_{tag}", cls
    except Exception as e:
        return f"v{ver} ERR {str(e)[:40]}", None


def main():
    for label, ws, proj in CANDS:
        meta, err = get_meta(ws, proj)
        if err:
            print(f"[{label}] {ws}/{proj} -> {err}", flush=True)
            continue
        proj_meta = meta.get("project", {})
        lic = proj_meta.get("license", "?")
        versions = meta.get("versions", [])
        vids = []
        for v in versions:
            vid = v.get("id", "")
            num = vid.split("/")[-1] if "/" in vid else v.get("version")
            if num:
                vids.append(str(num))
        if not vids:
            vids = ["1", "2", "3"]
        pcls = proj_meta.get("classes")
        ptype = proj_meta.get("type", "?")
        print(f"\n[{label}] {ws}/{proj} | type={ptype} | license={lic} | versions={vids} | classes={pcls}", flush=True)
        # test up to last 2 versions (most recent usually has working export)
        tested = vids[-2:] if len(vids) >= 2 else vids
        for ver in tested:
            res, cls = check_export(ws, proj, ver)
            print(f"    {res} | classes={cls}", flush=True)


if __name__ == "__main__":
    main()
