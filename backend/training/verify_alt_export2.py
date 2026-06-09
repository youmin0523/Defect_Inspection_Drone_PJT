"""
2차: HTTP 202(생성중) 재시도 + 신규 thermal/damp 후보 검증.
실행: backend/rfenv/Scripts/python.exe training/verify_alt_export2.py
"""
import sys, requests, time
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
KEY = "nuC9Lxr51Ds7c1IwN4Gy"
API = "https://api.roboflow.com"

# (label, ws, proj, version)  -- 특정 버전 직접 지정
JOBS = [
    # retry 202 thermal
    ("thermal", "murtazakhan", "thermal-anomaly-detection-1", "2"),
    ("thermal", "university-of-ottawa-thermal-anomaly", "thermal-anomaly-test-1", "1"),
    ("thermal", "solveview", "thermal-defects", "9"),
    # new damp/moisture/defect candidates
    ("thermal", "iit-m-7qnrz", "defect-sjree", "1"),
    ("thermal", "iit-m-7qnrz", "defect-sjree", "2"),
]


def meta(ws, proj):
    try:
        r = requests.get(f"{API}/{ws}/{proj}", params={"api_key": KEY}, timeout=30)
        if r.status_code != 200:
            return None
        return r.json()
    except Exception:
        return None


def check(ws, proj, ver, retries=4):
    cls = None
    for attempt in range(retries):
        try:
            r = requests.get(f"{API}/{ws}/{proj}/{ver}/yolov8",
                             params={"api_key": KEY}, timeout=60)
            if r.status_code == 202:
                time.sleep(15)
                continue
            if r.status_code != 200:
                return f"HTTP {r.status_code}", cls
            j = r.json()
            cls = (j.get("version") or {}).get("classes") or (j.get("project") or {}).get("classes")
            link = (j.get("export") or {}).get("link")
            if not link:
                time.sleep(10)
                continue
            z = requests.get(link, timeout=120)
            if z.content[:2] == b"PK":
                return "ZIP_OK", cls
            head = z.content[:80].decode("utf-8", "replace")
            tag = "404" if (z.status_code == 404 or "NoSuchKey" in head) else f"BROKEN({z.status_code})"
            return f"EXPORT_{tag}", cls
        except Exception as e:
            return f"ERR {str(e)[:40]}", cls
    return "STILL_202", cls


for label, ws, proj, ver in JOBS:
    m = meta(ws, proj)
    lic = (m or {}).get("project", {}).get("license", "?")
    ptype = (m or {}).get("project", {}).get("type", "?")
    res, cls = check(ws, proj, ver)
    cstr = str(cls)[:160] if cls else "None"
    print(f"[{label}] {ws}/{proj} v{ver} | type={ptype} | lic={lic} | {res} | classes={cstr}", flush=True)
