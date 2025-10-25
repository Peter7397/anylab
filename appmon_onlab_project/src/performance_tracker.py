import time, psutil
from collections import deque

class PerformanceTracker:
    def __init__(self, max_history=100):
        self.scan_durations = deque(maxlen=max_history)
        self.files_scanned = deque(maxlen=max_history)
        self.bytes_scanned = deque(maxlen=max_history)
        self.alerts_found = deque(maxlen=max_history)
        self.errors_count = deque(maxlen=max_history)
        self.cpu_usage = deque(maxlen=max_history)
        self.memory_usage = deque(maxlen=max_history)
        self.start_time = time.time()

    def record_scan(self, duration, files, bytes_, alerts, errors):
        self.scan_durations.append(duration)
        self.files_scanned.append(files)
        self.bytes_scanned.append(bytes_)
        self.alerts_found.append(alerts)
        self.errors_count.append(errors)
        try:
            self.cpu_usage.append(psutil.cpu_percent(interval=None))
            self.memory_usage.append(psutil.virtual_memory().percent)
        except Exception:
            pass

    def avg(self, seq):
        return (sum(seq)/len(seq)) if seq else 0.0

    def get_performance_summary(self):
        uptime = time.time() - self.start_time
        return {
            "uptime_seconds": uptime,
            "scan_performance": {
                "avg_scan_duration_ms": round(self.avg(self.scan_durations)*1000,2),
                "avg_files_per_scan": round(self.avg(self.files_scanned),2),
                "avg_bytes_per_scan": round(self.avg(self.bytes_scanned),2),
                "avg_alerts_per_scan": round(self.avg(self.alerts_found),2),
                "avg_errors_per_scan": round(self.avg(self.errors_count),2),
            },
            "system_performance": {
                "avg_cpu_percent": round(self.avg(self.cpu_usage),2),
                "avg_mem_percent": round(self.avg(self.memory_usage),2)
            }
        }
