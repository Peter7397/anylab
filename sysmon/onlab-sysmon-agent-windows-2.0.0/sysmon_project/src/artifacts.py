import os, json, zipfile
from datetime import datetime
def _ensure_dir(p): os.makedirs(p, exist_ok=True)
def write_json(path, obj):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
def package_sys_context(temp_dir: str, metrics: dict, breach: dict, host: str) -> str:
    _ensure_dir(temp_dir)
    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    root = os.path.join(temp_dir, f"sysctx_{ts}")
    os.makedirs(root, exist_ok=True)
    write_json(os.path.join(root, "metrics_snapshot.json"), metrics)
    write_json(os.path.join(root, "breach.json"), breach)
    zip_path = os.path.join(temp_dir, f"SysDiag_{host}_{ts}.zip")
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        for dp, _, files in os.walk(root):
            for fn in files:
                ap = os.path.join(dp, fn)
                z.write(ap, arcname=os.path.relpath(ap, root))
    return zip_path
