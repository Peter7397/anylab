import json, logging, logging.handlers, os, sys
from datetime import datetime

def _ensure_dir(p):
    os.makedirs(p, exist_ok=True)

class JsonFormatter(logging.Formatter):
    def format(self, record):
        base = {
            "ts": datetime.utcnow().isoformat() + "Z",
            "lvl": record.levelname,
            "msg": record.getMessage(),
            "logger": record.name
        }
        if record.exc_info:
            base["exc"] = self.formatException(record.exc_info)
        return json.dumps(base, ensure_ascii=False)

def setup_logger(log_dir: str, name="sysmon", level=logging.INFO):
    _ensure_dir(log_dir)
    log_path = os.path.join(log_dir, f"{name}.log")
    handler = logging.handlers.TimedRotatingFileHandler(log_path, when="midnight", backupCount=14, encoding="utf-8")
    handler.setFormatter(JsonFormatter())
    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.handlers = [handler]
    if sys.stdout and sys.stdout.isatty():
        sh = logging.StreamHandler(sys.stdout)
        sh.setFormatter(JsonFormatter())
        logger.addHandler(sh)
    return logger
