import os, time, socket, argparse, json
from logutil import setup_logger
from config import load_config
from util import utcnow_iso, expand_globs, sha256_hex
from tailer import TailState, tail_new_lines
from patterns import PatternMatcher
from artifacts import package_logs
from uploader import Uploader

class AppMonService:
    def __init__(self, config):
        self.config = config
        self.host = config.get("hostname_alias") or socket.gethostname()
        self.interval = int(config.get("scan_interval_sec", 30))
        self.uploader = Uploader(
            base_dir=os.path.dirname(config["paths"]["queue"]),
            base_url=config["alert_server"].get("base_url",""),
            api_key=config["alert_server"].get("api_key",""),
            connect_timeout=config["alert_server"].get("connect_timeout_sec",5),
            read_timeout=config["alert_server"].get("read_timeout_sec",20),
            tls_verify=config["alert_server"].get("tls",{}).get("verify", True),
            ca_bundle=config["alert_server"].get("tls",{}).get("ca_bundle_path")
        )
        
        # Enhanced state management
        state_dir = os.path.join(config["paths"]["state"], "tails")
        os.makedirs(state_dir, exist_ok=True)
        self.tstate = TailState(state_dir)
        
        # Performance tracking
        self.stats = {
            "files_scanned": 0,
            "alerts_sent": 0,
            "artifacts_created": 0,
            "last_scan_time": None
        }
        
        # Deduplication for alerts
        self.alert_cache = {}
        self.cache_ttl = 300  # 5 minutes

    def scan_source(self, source):
        """Enhanced source scanning with better error handling"""
        try:
            matcher = PatternMatcher(source.get("patterns", []))
            enc = source.get("encoding","utf-8")
            max_mb = source.get("max_file_mb", 500)
            files = expand_globs(source.get("paths", []))
            
            source_stats = {"files_processed": 0, "alerts_found": 0}
            
            for fp in files:
                try:
                    if not os.path.isfile(fp): 
                        continue
                    
                    # File size check
                    file_size = os.path.getsize(fp)
                    if (file_size/1024/1024) > max_mb: 
                        continue
                    
                    source_stats["files_processed"] += 1
                    self.stats["files_scanned"] += 1
                    
                    # Load state and scan
                    st = self.tstate.load(fp)
                    lines, new_pos = tail_new_lines(fp, st.get("pos",0), encoding=enc, max_bytes=5*1024*1024)
                    
                    if not lines: 
                        self.tstate.save(fp, new_pos)
                        continue
                    
                    # Pattern matching
                    hits = matcher.scan_lines(lines)
                    if hits:
                        source_stats["alerts_found"] += len(hits)
                        self.process_hits(hits, source, fp)
                    
                    self.tstate.save(fp, new_pos)
                    
                except Exception as fe:
                    self.logger.error(f"File scan error for {fp}: {fe}")
                    
            return source_stats
            
        except Exception as se:
            self.logger.error(f"Source scan failed: {source.get('name')}: {se}")
            return {"files_processed": 0, "alerts_found": 0}

    def process_hits(self, hits, source, file_path):
        """Process pattern hits with deduplication and enhanced alerting"""
        for hit in hits:
            # Create alert fingerprint for deduplication
            alert_key = f"{self.host}:{source.get('name')}:{hit['severity']}:{sha256_hex(hit['line'][:100])}"
            
            # Check if we've seen this alert recently
            if self.is_duplicate_alert(alert_key):
                continue
            
            # Create enhanced alert
            alert = {
                "host": self.host,
                "service": "AppMonSvc",
                "timestamp_utc": utcnow_iso(),
                "source": source.get("name","unknown"),
                "file": file_path,
                "line_no": hit["line_no"],
                "severity": hit["severity"],
                "message": hit["line"][:2000],
                "type": "log_match",
                "context": hit.get("context", []),
                "fingerprint": alert_key,
                "version": "2.0.0"
            }
            
            # Send alert
            self.uploader.post_alert(alert, self.logger)
            self.stats["alerts_sent"] += 1
            
            # Mark as sent
            self.alert_cache[alert_key] = time.time()
            
            # Create artifacts for critical alerts
            if hit["severity"] in ["critical", "error"]:
                self.create_artifact(source, file_path, hits)
    
    def is_duplicate_alert(self, alert_key):
        """Check if alert is a duplicate within TTL window"""
        now = time.time()
        if alert_key in self.alert_cache:
            if now - self.alert_cache[alert_key] < self.cache_ttl:
                return True
            else:
                del self.alert_cache[alert_key]
        return False
    
    def create_artifact(self, source, file_path, hits):
        """Create artifact package for critical alerts"""
        try:
            meta = {
                "host": self.host,
                "service": "AppMonSvc", 
                "timestamp_utc": utcnow_iso(),
                "source": source.get("name","unknown"),
                "file": file_path,
                "matches": hits[:50],
                "trigger_severity": "critical"
            }
            
            zip_path = package_logs(
                self.config["paths"]["temp"], 
                self.host, 
                source.get("name","unknown"),
                source.get("artifact",{}).get("include_globs", source.get("paths", [])),
                int(source.get("artifact",{}).get("tail_bytes_each", 2*1024*1024)),
                meta
            )
            
            self.uploader.post_zip_with_meta(meta, zip_path, self.logger)
            self.stats["artifacts_created"] += 1
            
        except Exception as e:
            self.logger.error(f"Artifact creation failed: {e}")

    def run_scan_cycle(self):
        """Run one complete scan cycle"""
        cycle_start = time.time()
        cycle_stats = {"sources_processed": 0, "total_alerts": 0}
        
        for source in self.config.get("sources", []):
            try:
                source_stats = self.scan_source(source)
                cycle_stats["sources_processed"] += 1
                cycle_stats["total_alerts"] += source_stats["alerts_found"]
                
            except Exception as e:
                self.logger.error(f"Source processing failed: {source.get('name')}: {e}")
        
        # Update stats
        self.stats["last_scan_time"] = cycle_start
        cycle_duration = time.time() - cycle_start
        
        # Log cycle summary
        self.logger.info(f"Scan cycle completed: {cycle_stats['sources_processed']} sources, "
                        f"{cycle_stats['total_alerts']} alerts, {cycle_duration:.2f}s")
        
        return cycle_stats

    def run(self, once=False):
        """Main service loop"""
        self.logger.info(f"AppMonSvc starting on {self.host}")
        
        try:
            while True:
                cycle_stats = self.run_scan_cycle()
                
                # Retry failed uploads
                self.uploader.retry_queue(self.logger, max_items=10)
                
                if once:
                    break
                
                # Adaptive sleep based on scan duration
                sleep_time = max(0.1, self.interval - (time.time() - self.stats["last_scan_time"]))
                time.sleep(sleep_time)
                
        except KeyboardInterrupt:
            self.logger.info("AppMonSvc stopping (keyboard)")
        except Exception as e:
            self.logger.exception(f"AppMonSvc fatal error: {e}")
            raise

def main():
    ap = argparse.ArgumentParser(description="Enhanced Application Monitoring Service (AppMonSvc)")
    ap.add_argument("--global", dest="global_cfg", default=os.path.join("config","global.default.json"))
    ap.add_argument("--local", dest="local_cfg", default=os.path.join("config","appmon.local.json"))
    ap.add_argument("--once", action="store_true", help="Scan once and exit")
    ap.add_argument("--upload-metrics", action="store_true", help="Upload metrics to AnyLab")
    args = ap.parse_args()

    cfg = load_config(args.global_cfg, args.local_cfg)
    paths = cfg["paths"]
    logger = setup_logger(paths["logs"], name="appmon_enhanced")
    
    # Create service instance
    service = AppMonService(cfg)
    service.logger = logger
    
    # Run service
    service.run(once=args.once)

if __name__ == "__main__":
    main()
