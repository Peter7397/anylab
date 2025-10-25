import json, os
def _expand_paths(cfg):
    paths = cfg.get("paths", {})
    root = paths.get("root", "C:\\ProgramData\\SysMon")
    for k, v in list(paths.items()):
        if isinstance(v, str) and "{root}" in v:
            paths[k] = v.replace("{root}", root)
    cfg["paths"] = paths
    return cfg

def load_config(global_default_path: str, local_path: str) -> dict:
    with open(global_default_path, "r", encoding="utf-8") as f:
        base = json.load(f)
    cfg = base
    if os.path.exists(local_path):
        with open(local_path, "r", encoding="utf-8") as f:
            override = json.load(f)
        def merge(a, b):
            for k, v in b.items():
                if isinstance(v, dict) and isinstance(a.get(k), dict):
                    a[k] = {**a[k], **v}
                else:
                    a[k] = v
            return a
        cfg = merge(cfg, override)
    return _expand_paths(cfg)
