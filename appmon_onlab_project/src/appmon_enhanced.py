import os, re, io, time, glob, json, hashlib, argparse, socket
from datetime import datetime, timezone
from collections import deque, defaultdict

from structured_logger import build_logger, StructuredLogger, utcnow_iso
from performance_tracker import PerformanceTracker
from config_validator import ConfigValidator
from uploader import Uploader

def sha256_hex(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8","ignore")).hexdigest()

def expand_paths(cfg):
    paths = cfg.get("paths", {}); root = paths.get("root","C:\\\\ProgramData\\\\AppMon")
    for k, v in list(paths.items()):
        if isinstance(v, str) and "{root}" in v: paths[k]=v.replace("{root}", root)
    cfg["paths"]=paths; return cfg

class AppMonService:
    def __init__(self, cfg):
        self.cfg = expand_paths(cfg)
        self.paths = self.cfg["paths"]
        os.makedirs(self.paths["logs"], exist_ok=True)
        os.makedirs(self.paths["state"], exist_ok=True)
        os.makedirs(self.paths["queue"], exist_ok=True)
        os.makedirs(self.paths["temp"], exist_ok=True)

        self.host = self.cfg.get("hostname_alias") or os.getenv("COMPUTERNAME") or socket.gethostname() or "unknown-host"
        self.interval = int(self.cfg.get("scan_interval_sec", 30))
        self.metrics_interval = int(self.cfg.get("metrics_interval_sec", 60))

        self.logger = StructuredLogger(build_logger(self.paths["logs"], "AppMonSvc"))
        self.validator = ConfigValidator()
        self.perf = PerformanceTracker(max_history=200)

        dcfg = self.cfg.get("dedup", {})
        self.cache_ttl = int(dcfg.get("cache_ttl_sec", 300))
        self.max_cache_size = int(dcfg.get("max_cache_size", 2000))
        self.alert_cache = {}
        self.alert_stats = {"total_alerts":0,"duplicate_alerts":0,"unique_alerts":0,"cache_hits":0,"cache_misses":0}

        self.stats = {"scan_cycles":0,"files_scanned":0,"bytes_scanned":0,"last_scan_duration":0.0,"errors_count":0,"last_error_time":None}

        as_cfg = self.cfg["alert_server"]
        self.uploader = Uploader(
            base_dir=os.path.dirname(self.paths["queue"]),
            base_url=as_cfg.get("base_url",""),
            api_key=as_cfg.get("api_key",""),
            connect_timeout=as_cfg.get("connect_timeout_sec",5),
            read_timeout=as_cfg.get("read_timeout_sec",20),
            tls_verify=as_cfg.get("tls",{}).get("verify", True),
            ca_bundle=as_cfg.get("tls",{}).get("ca_bundle_path")
        )

        self.context_buffers = defaultdict(lambda: deque(maxlen=20))

        if not self.validator.validate_config(self.cfg):
            self.logger.warn("config_validation_failed", errors=self.validator.errors, warnings=self.validator.warnings)

    def get_all_monitored_files(self):
        files=set()
        for src in self.cfg.get("sources", []):
            for pattern in src.get("files", []):
                for fp in glob.glob(pattern):
                    files.add(fp)
        return sorted(files)

    def get_total_log_size_mb(self):
        total=0
        for fp in self.get_all_monitored_files():
            try: total+= os.path.getsize(fp)
            except: pass
        return round(total/ (1024*1024), 3)

    def get_largest_file_mb(self):
        sizes=[(os.path.getsize(f), f) for f in self.get_all_monitored_files() if os.path.exists(f)]
        return round((max(sizes)[0]/(1024*1024)) if sizes else 0, 3)

    def get_total_patterns(self):
        return sum(len(s.get("patterns", [])) for s in self.cfg.get("sources", []))

    def get_cache_hit_rate(self):
        hits=self.alert_stats["cache_hits"]; misses=self.alert_stats["cache_misses"]
        denom=hits+misses
        return round((hits/denom)*100,2) if denom else 0.0

    def categorize_application(self, name):
        return self.cfg.get("onlab_integration",{}).get("application_mapping",{}).get(name, "unknown")

    def state_path(self, file_path):
        h = sha256_hex(file_path)
        return os.path.join(self.paths["state"], f"{h}.offset")

    def read_offset(self, file_path):
        sp = self.state_path(file_path)
        try:
            with open(sp,"r",encoding="utf-8") as f: return int(f.read().strip())
        except: return 0

    def write_offset(self, file_path, offset):
        sp = self.state_path(file_path)
        with open(sp,"w",encoding="utf-8") as f: f.write(str(offset))

    def clean_alert_cache(self, now):
        expired = [k for k, t in self.alert_cache.items() if now - t >= self.cache_ttl]
        for k in expired: self.alert_cache.pop(k, None)
        if len(self.alert_cache) > self.max_cache_size:
            drop = int(0.1 * len(self.alert_cache)) or 1
            for k in sorted(self.alert_cache, key=self.alert_cache.get)[:drop]:
                self.alert_cache.pop(k, None)

    def is_duplicate_alert(self, alert_key):
        now = time.time()
        self.clean_alert_cache(now)
        if alert_key in self.alert_cache:
            if now - self.alert_cache[alert_key] < self.cache_ttl:
                self.alert_stats["duplicate_alerts"] += 1
                self.alert_stats["cache_hits"] += 1
                return True
            else:
                self.alert_cache.pop(alert_key, None)
        self.alert_cache[alert_key] = now
        self.alert_stats["unique_alerts"] += 1
        self.alert_stats["cache_misses"] += 1
        return False

    def get_application_metrics(self):
        apps = {}
        for s in self.cfg.get("sources", []):
            apps[s.get("name","unknown")] = {
                "patterns": len(s.get("patterns", [])),
                "files_globs": len(s.get("files", []))
            }
        return apps

    def get_average_scan_duration(self):
        return round(self.perf.get_performance_summary()["scan_performance"]["avg_scan_duration_ms"],2)

    def collect_application_metrics(self):
        metrics = {
            "host": self.host,
            "service": "AppMonSvc",
            "timestamp_utc": utcnow_iso(),
            "version": "2.0.0",
            "metrics": {
                "files_monitored": len(self.get_all_monitored_files()),
                "total_log_size_mb": self.get_total_log_size_mb(),
                "largest_file_mb": self.get_largest_file_mb(),
                "total_alerts_sent": self.alert_stats["total_alerts"],
                "unique_alerts_sent": self.alert_stats["unique_alerts"],
                "duplicate_alerts_suppressed": self.alert_stats["duplicate_alerts"],
                "last_scan_duration_ms": self.stats.get("last_scan_duration", 0)*1000,
                "average_scan_duration_ms": self.get_average_scan_duration(),
                "scan_frequency_per_minute": 60.0 / max(1,self.interval),
                "active_sources": len(self.cfg.get("sources", [])),
                "total_patterns": self.get_total_patterns(),
                "errors_last_hour": self.stats.get("errors_count", 0),
                "last_error_time": self.stats.get("last_error_time"),
                "alert_cache_size": len(self.alert_cache),
                "cache_hit_rate": self.get_cache_hit_rate()
            },
            "performance": self.perf.get_performance_summary(),
            "applications": self.get_application_metrics()
        }
        return metrics

    def normalize_for_fingerprint(self, s):
        s = re.sub(r"\\d+", "<num>", s)
        s = re.sub(r"\\s+", " ", s).strip()
        return s[:512]

    def scan_once(self):
        t0 = time.time()
        files_scanned = 0; bytes_scanned = 0; alerts_found = 0
        errors = []
        sources_processed = 0

        for source in self.cfg.get("sources", []):
            sources_processed += 1
            for pattern_glob in source.get("files", []):
                for fp in glob.glob(pattern_glob):
                    files_scanned += 1
                    try:
                        try:
                            file_size = os.path.getsize(fp); file_mtime = os.path.getmtime(fp)
                        except Exception:
                            file_size = 0; file_mtime = 0
                        offset = self.read_offset(fp)
                        with open(fp, "r", encoding=source.get("encoding","utf-8"), errors="ignore") as f:
                            f.seek(0, os.SEEK_END); end = f.tell()
                            if offset > end: offset = 0
                            f.seek(offset)
                            line_no = 0
                            for line in f:
                                line_no += 1
                                bytes_scanned += len(line.encode("utf-8","ignore"))
                                self.context_buffers[fp].append(line.rstrip("\\n"))
                                for pat in source.get("patterns", []):
                                    if re.search(pat["regex"], line):
                                        context_before = list(self.context_buffers[fp])[-int(pat.get("context_before",2))-1:-1]
                                        context_after = []
                                        pos_before = f.tell()
                                        for _ in range(int(pat.get("context_after",2))):
                                            nxt = f.readline()
                                            if not nxt: break
                                            context_after.append(nxt.rstrip("\\n"))
                                        f.seek(pos_before)
                                        hit = {
                                            "line_no": line_no,
                                            "severity": pat.get("severity","info"),
                                            "line": line.rstrip("\\n"),
                                            "context": context_before + context_after
                                        }
                                        base = f"{source.get('name','unknown')}|{pat['name']}|{self.normalize_for_fingerprint(line)}"
                                        fingerprint = sha256_hex(base)
                                        alert_key = fingerprint
                                        if self.is_duplicate_alert(alert_key):
                                            continue
                                        file_modified = datetime.fromtimestamp(file_mtime, tz=timezone.utc).isoformat() if file_mtime else None
                                        alert = {
                                            "host": self.host,
                                            "service": "AppMonSvc",
                                            "timestamp_utc": utcnow_iso(),
                                            "source": source.get("name","unknown"),
                                            "file": fp,
                                            "line_no": hit["line_no"],
                                            "severity": hit["severity"],
                                            "message": hit["line"][:2000],
                                            "type": "log_match",
                                            "context": hit.get("context", []),
                                            "fingerprint": fingerprint,
                                            "version": "2.0.0",
                                            "application_name": source.get("name","unknown"),
                                            "log_level": hit["severity"],
                                            "file_size_bytes": file_size,
                                            "file_modified_time": file_modified,
                                            "pattern_matched": pat.get("name"),
                                            "application_category": self.categorize_application(source.get("name")),
                                            "alert_id": f"appmon_{fingerprint[:16]}",
                                            "metadata": {
                                                "scan_cycle": self.stats.get("scan_cycles", 0),
                                                "total_files_scanned": self.stats.get("files_scanned", 0),
                                                "source_patterns_count": len(source.get("patterns", [])),
                                                "file_encoding": source.get("encoding","utf-8")
                                            }
                                        }
                                        alerts_found += 1; self.alert_stats["total_alerts"] += 1
                                        self.uploader.send_alert(alert, self.logger)
                        self.write_offset(fp, os.path.getsize(fp))
                    except Exception as e:
                        errors.append(str(e))
                        self.stats["errors_count"] += 1
                        self.stats["last_error_time"] = utcnow_iso()

        duration = time.time() - t0
        self.stats["scan_cycles"] += 1
        self.stats["files_scanned"] += files_scanned
        self.stats["bytes_scanned"] += bytes_scanned
        self.stats["last_scan_duration"] = duration
        self.perf.record_scan(duration, files_scanned, bytes_scanned, alerts_found, len(errors))
        self.logger.log_scan_summary(
            {"sources_processed": sources_processed, "files_scanned": files_scanned, "total_alerts": alerts_found},
            duration, errors=errors if errors else None
        )
        return duration, files_scanned, bytes_scanned, alerts_found, errors

    def maybe_send_metrics(self, last_metrics_ts):
        integ = self.cfg.get("onlab_integration",{})
        upload = integ.get("upload_metrics", True)
        if not upload: return last_metrics_ts
        now = time.time()
        if now - last_metrics_ts >= max(5, self.metrics_interval):
            metrics = self.collect_application_metrics()
            self.uploader.send_metrics(metrics, self.logger)
            return now
        return last_metrics_ts

    def run(self, once=False):
        last_metrics_ts = 0
        self.logger.info("AppMonSvc starting", host=self.host, version="2.0.0")
        try:
            while True:
                self.scan_once()
                last_metrics_ts = self.maybe_send_metrics(last_metrics_ts)
                self.uploader.retry_queue(self.logger, max_items=5)
                if once: break
                time.sleep(max(0.1, self.interval))
        except KeyboardInterrupt:
            self.logger.info("AppMonSvc stopping (keyboard)")
        except Exception as e:
            self.logger.exception("AppMonSvc fatal error", error=str(e))
            raise

def load_config(global_path, local_path):
    with open(global_path,"r",encoding="utf-8") as f: base=json.load(f)
    cfg = base
    if local_path and os.path.exists(local_path):
        with open(local_path,"r",encoding="utf-8") as f: ov=json.load(f)
        def merge(a,b):
            for k,v in b.items():
                if isinstance(v, dict) and isinstance(a.get(k), dict):
                    a[k] = merge(a[k], v)
                else:
                    a[k]=v
            return a
        cfg = merge(cfg, ov)
    return cfg

def main():
    ap = argparse.ArgumentParser(description="Application Monitoring Service (AppMonSvc) — AnyLab Enhanced")
    ap.add_argument("--global", dest="global_cfg", default=os.path.join("config","global.default.json"))
    ap.add_argument("--local", dest="local_cfg", default=os.path.join("config","appmon.anylab.json"))
    ap.add_argument("--once", action="store_true")
    args = ap.parse_args()
    cfg = load_config(args.global_cfg, args.local_cfg)
    AppMonService(cfg).run(once=args.once)

if __name__ == "__main__":
    main()
