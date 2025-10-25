import hashlib, time
from datetime import datetime, timezone

def utcnow_iso():
    return datetime.now(timezone.utc).isoformat()

def sha256_hex(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()

class Deduper:
    def __init__(self, suppress_sec: int):
        self.suppress_sec = suppress_sec
        self._last = {}

    def should_alert(self, fingerprint: str, now_ts: float | None = None) -> bool:
        now_ts = now_ts or time.time()
        last = self._last.get(fingerprint)
        if last is None or (now_ts - last) > self.suppress_sec:
            self._last[fingerprint] = now_ts
            return True
        return False
