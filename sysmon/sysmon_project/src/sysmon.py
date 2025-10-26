import os, time, socket, argparse, json
from logutil import setup_logger
from config import load_config
from util import utcnow_iso, sha256_hex, Deduper
from collectors import collect_cpu, collect_memory, collect_disks, collect_network, collect_system_info
from evaluator import eval_sys_thresholds
from artifacts import package_sys_context
from uploader import Uploader

class SysMonService:
    def __init__(self, config, logger):
        self.config = config
        self.logger = logger
        self.host = config.get("hostname_alias") or socket.gethostname()
        self.dedup = Deduper(config.get("dedup_suppress_sec", 1800))
        self.uploader = Uploader(
            base_dir=os.path.dirname(config["paths"]["queue"]),
            base_url=config["alert_server"].get("base_url",""),
            api_key=config["alert_server"].get("api_key",""),
            connect_timeout=config["alert_server"].get("connect_timeout_sec",5),
            read_timeout=config["alert_server"].get("read_timeout_sec",20),
            tls_verify=config["alert_server"].get("tls",{}).get("verify", True),
            ca_bundle=config["alert_server"].get("tls",{}).get("ca_bundle_path")
        )
        self.monitor_interval = int(config.get("monitor_interval_sec", 60))
        self.prev_disk_io = None
        self.prev_net = None
        self.stats = {
            'cycles': 0,
            'errors': 0,
            'alerts_sent': 0,
            'metrics_uploaded': 0,
            'start_time': time.time()
        }

    def collect_metrics(self):
        """Collect all system metrics with error handling"""
        try:
            t0 = time.time()
            
            # Collect basic metrics
            cpu = collect_cpu()
            mem = collect_memory()
            disk = collect_disks(self.prev_disk_io)
            net = collect_network(self.prev_net)
            sys_info = collect_system_info()
            
            # Update snapshots for next iteration
            self.prev_disk_io = disk.get("_snapshot")
            self.prev_net = net.get("_snapshot")
            
            # Calculate collection time
            collection_time = time.time() - t0
            
            metrics = {
                "cpu": cpu, 
                "mem": mem, 
                "disk": disk, 
                "net": net, 
                "system": sys_info,
                "collection_time_ms": round(collection_time * 1000, 2),
                "ts_utc": utcnow_iso()
            }
            
            self.stats['cycles'] += 1
            return metrics
            
        except Exception as e:
            self.logger.error(f"Error collecting metrics: {e}")
            self.stats['errors'] += 1
            return None

    def upload_metrics(self, metrics):
        """Upload metrics to AnyLab backend"""
        if not metrics:
            return False
            
        try:
            metrics_payload = {
                "host": self.host,
                "service": "SysMonSvc",
                "timestamp_utc": metrics["ts_utc"],
                "metrics": metrics,
                "agent_version": "2.0.0",
                "agent_stats": self.stats
            }
            
            self.uploader.post_metrics(metrics_payload, self.logger)
            self.stats['metrics_uploaded'] += 1
            return True
            
        except Exception as e:
            self.logger.error(f"Metrics upload failed: {e}")
            return False

    def process_alerts(self, metrics, t0):
        """Process threshold breaches and send alerts"""
        try:
            breaches = eval_sys_thresholds(t0, metrics, self.config["thresholds"], state={})
            
            for breach in breaches:
                fp = sha256_hex("|".join([
                    self.host, "SysMonSvc", breach["metric"], breach["severity"],
                    str(breach.get("dimensions",{})), str(round(breach["value"],1)), str(breach["threshold"])
                ]))
                
                if self.dedup.should_alert(fp, t0):
                    alert = {
                        "host": self.host, 
                        "service": "SysMonSvc", 
                        "timestamp_utc": metrics["ts_utc"],
                        "severity": breach["severity"], 
                        "metric": breach["metric"], 
                        "value": breach["value"],
                        "threshold": breach["threshold"], 
                        "dimensions": breach.get("dimensions", {}),
                        "fingerprint": fp, 
                        "version": "2.0.0",
                        "agent_stats": self.stats
                    }
                    
                    self.logger.warning(
                        f"ALERT {breach['severity']} {breach['metric']} "
                        f"val={breach['value']} thr={breach['threshold']} "
                        f"dims={breach.get('dimensions',{})}"
                    )
                    
                    self.uploader.post_alert(alert, self.logger)
                    self.stats['alerts_sent'] += 1
                    
                    # Package artifacts for critical alerts
                    if breach["severity"] == "critical":
                        try:
                            zip_path = package_sys_context(
                                self.config["paths"]["temp"], 
                                metrics, 
                                breach, 
                                self.host
                            )
                            meta = {
                                "host": self.host,
                                "service": "SysMonSvc",
                                "timestamp_utc": metrics["ts_utc"],
                                "trigger_metric": breach["metric"],
                                "severity": breach["severity"]
                            }
                            self.uploader.post_zip_with_meta(meta, zip_path, self.logger)
                        except Exception as e:
                            self.logger.error(f"Artifact packaging failed: {e}")
                            
        except Exception as e:
            self.logger.error(f"Error processing alerts: {e}")
            self.stats['errors'] += 1

    def run_cycle(self):
        """Run one monitoring cycle"""
        t0 = time.time()
        
        # Collect metrics
        metrics = self.collect_metrics()
        if not metrics:
            return False
            
        # Upload metrics if enabled
        if self.config.get("upload_metrics", False):
            self.upload_metrics(metrics)
        
        # Process alerts
        self.process_alerts(metrics, t0)
        
        # Retry failed uploads
        self.uploader.retry_queue(self.logger, max_items=5)
        
        return True

    def run(self, once=False):
        """Main service loop"""
        self.logger.info(f"SysMonSvc starting on {self.host}")
        
        try:
            while True:
                cycle_start = time.time()
                
                # Run monitoring cycle
                success = self.run_cycle()
                
                # Calculate sleep time
                cycle_time = time.time() - cycle_start
                sleep_time = max(0.1, self.monitor_interval - cycle_time)
                
                if once:
                    break
                    
                # Log periodic stats
                if self.stats['cycles'] % 10 == 0:
                    uptime = time.time() - self.stats['start_time']
                    self.logger.info(
                        f"Service stats: {self.stats['cycles']} cycles, "
                        f"{self.stats['alerts_sent']} alerts, "
                        f"{self.stats['metrics_uploaded']} metrics, "
                        f"{self.stats['errors']} errors, "
                        f"uptime: {uptime:.1f}s"
                    )
                
                time.sleep(sleep_time)
                
        except KeyboardInterrupt:
            self.logger.info("SysMonSvc stopping (keyboard)")
        except Exception as e:
            self.logger.exception(f"SysMonSvc fatal error: {e}")
            raise

def main():
    ap = argparse.ArgumentParser(description="System Monitoring Service (SysMonSvc)")
    ap.add_argument("--global", dest="global_cfg", default=os.path.join("config","global.default.json"))
    ap.add_argument("--local", dest="local_cfg", default=os.path.join("config","sysmon.local.json"))
    ap.add_argument("--once", action="store_true", help="Collect once and exit")
    ap.add_argument("--upload-metrics", action="store_true", help="Upload metrics to AnyLab")
    ap.add_argument("--version", action="version", version="SysMonSvc 2.0.0")
    args = ap.parse_args()

    # Load configuration
    cfg = load_config(args.global_cfg, args.local_cfg)
    paths = cfg["paths"]
    logger = setup_logger(paths["logs"], name="sysmon")

    # Enable metrics upload if specified
    if args.upload_metrics:
        cfg["upload_metrics"] = True

    # Create and run service
    service = SysMonService(cfg, logger)
    service.run(once=args.once)

if __name__ == "__main__":
    main()
