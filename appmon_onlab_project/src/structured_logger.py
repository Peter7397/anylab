import json, logging, logging.handlers, os, sys
from datetime import datetime, timezone

def utcnow_iso(): return datetime.now(timezone.utc).isoformat()

class JsonFormatter(logging.Formatter):
    def format(self, record):
        payload = {
            "ts": utcnow_iso(),
            "lvl": record.levelname,
            "logger": record.name,
            "msg": record.getMessage()
        }
        if record.exc_info:
            payload["exc"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False)

def build_logger(log_dir: str, name="AppMonSvc"):
    os.makedirs(log_dir, exist_ok=True)
    log_path = os.path.join(log_dir, f"{name}.log")
    handler = logging.handlers.TimedRotatingFileHandler(log_path, when="midnight", backupCount=14, encoding="utf-8")
    handler.setFormatter(JsonFormatter())
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    logger.handlers = [handler]
    if sys.stdout and hasattr(sys.stdout, "isatty") and sys.stdout.isatty():
        sh = logging.StreamHandler(sys.stdout)
        sh.setFormatter(JsonFormatter())
        logger.addHandler(sh)
    return logger

class StructuredLogger:
    def __init__(self, logger):
        self.logger = logger

    def info(self, msg, **kv): self.logger.info(json.dumps({"event":"info","message":msg, **kv}))
    def warn(self, msg, **kv): self.logger.warning(json.dumps({"event":"warn","message":msg, **kv}))
    def error(self, msg, **kv): self.logger.error(json.dumps({"event":"error","message":msg, **kv}))
    def exception(self, msg, **kv): self.logger.exception(json.dumps({"event":"exception","message":msg, **kv}))

    def log_scan_summary(self, cycle_stats, duration, errors=None):
        summary = {
            "event_type": "scan_summary",
            "timestamp": utcnow_iso(),
            "duration_seconds": round(duration, 3),
            "sources_processed": cycle_stats.get("sources_processed", 0),
            "files_scanned": cycle_stats.get("files_scanned", 0),
            "alerts_found": cycle_stats.get("total_alerts", 0),
            "errors_count": len(errors) if errors else 0,
            "status": "success" if not errors else "partial_failure"
        }
        if errors: summary["errors"] = errors
        self.logger.info(json.dumps(summary))
