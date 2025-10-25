import os, json, time, requests

class Uploader:
    def __init__(self, base_dir: str, base_url: str, api_key: str,
                 connect_timeout=5, read_timeout=20, tls_verify=True, ca_bundle=None):
        self.queue_dir = os.path.join(base_dir, "queue"); os.makedirs(self.queue_dir, exist_ok=True)
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = (connect_timeout, read_timeout)
        self.verify = ca_bundle if tls_verify and ca_bundle else tls_verify

    def _headers(self):
        return {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}

    def post(self, endpoint, payload, logger):
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        try:
            r = requests.post(url, json=payload, headers=self._headers(), timeout=self.timeout, verify=self.verify)
            if r.status_code >= 300:
                raise RuntimeError(f"HTTP {r.status_code}: {r.text[:200]}")
            return True
        except Exception as e:
            logger.error("upload_failed", endpoint=endpoint, error=str(e))
            self._enqueue_json({"endpoint": endpoint, "payload": payload, "ts": int(time.time())})
            return False

    def send_alert(self, alert, logger):
        return self.post("/alerts/", alert, logger)

    def send_metrics(self, metrics, logger):
        return self.post("/metrics/", metrics, logger)

    def retry_queue(self, logger, max_items=10):
        names = sorted(os.listdir(self.queue_dir))[:max_items]
        for n in names:
            path = os.path.join(self.queue_dir, n)
            try:
                with open(path, "r", encoding="utf-8") as f:
                    item = json.load(f)
                if self.post(item["endpoint"], item["payload"], logger):
                    os.remove(path)
            except Exception as e:
                logger.error("queue_retry_failed", file=n, error=str(e))

    def _enqueue_json(self, obj: dict):
        path = os.path.join(self.queue_dir, f"q_{int(time.time())}.json")
        with open(path, "w", encoding="utf-8") as f: json.dump(obj, f, ensure_ascii=False)
