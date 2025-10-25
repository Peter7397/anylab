import psutil, time
from functools import lru_cache
from typing import Dict, List, Optional, Any
import threading

BYTES_IN_GB = 1024**3

# Cache for expensive operations
_process_cache = {}
_cache_lock = threading.Lock()
_cache_ttl = 5  # seconds

def _pct(a, b):
    try: return (a/b)*100.0
    except Exception: return 0.0

def _get_cached_processes():
    """Get cached process list to reduce overhead"""
    current_time = time.time()
    
    with _cache_lock:
        if current_time - _process_cache.get('timestamp', 0) < _cache_ttl:
            return _process_cache.get('processes', [])
        
        processes = []
        try:
            # Use more efficient process iteration
            for p in psutil.process_iter(['pid', 'name', 'username', 'cpu_percent'], ad_value=None):
                try:
                    processes.append({
                        'pid': p.info['pid'],
                        'name': p.info['name'],
                        'username': p.info['username'],
                        'cpu_pct': p.info['cpu_percent']
                    })
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue
        except Exception:
            pass
        
        _process_cache['processes'] = processes
        _process_cache['timestamp'] = current_time
        return processes

def collect_cpu():
    """Collect CPU metrics with optimized process monitoring"""
    total = psutil.cpu_percent(interval=None)
    
    # Get cached processes and filter by CPU usage
    processes = _get_cached_processes()
    high_cpu_procs = [p for p in processes if p.get('cpu_pct', 0) > 0.1]  # Only processes with >0.1% CPU
    high_cpu_procs.sort(key=lambda x: x.get('cpu_pct', 0), reverse=True)
    
    return {
        "cpu_total_pct": total, 
        "top_procs": high_cpu_procs[:50],
        "process_count": len(processes),
        "high_cpu_count": len(high_cpu_procs)
    }

def collect_memory():
    """Collect memory metrics with additional details"""
    vm = psutil.virtual_memory()
    sm = psutil.swap_memory()
    
    return {
        "ram_total_mb": int(vm.total/1024/1024),
        "ram_used_pct": vm.percent,
        "ram_available_mb": int(vm.available/1024/1024),
        "ram_used_mb": int(vm.used/1024/1024),
        "ram_free_mb": int(vm.free/1024/1024),
        "pagefile_used_pct": sm.percent,
        "pagefile_total_mb": int(sm.total/1024/1024),
        "pagefile_used_mb": int(sm.used/1024/1024)
    }

def collect_disks(prev_disk_io=None):
    """Collect disk metrics with performance optimization"""
    disks = []
    disk_io_stats = {}
    
    # Collect disk usage
    for part in psutil.disk_partitions(all=False):
        if "cdrom" in part.opts or part.fstype == "":
            continue
        try:
            usage = psutil.disk_usage(part.mountpoint)
            disks.append({
                "device": part.device,
                "mount": part.mountpoint,
                "fstype": part.fstype,
                "total_gb": round(usage.total/BYTES_IN_GB, 2),
                "free_gb": round(usage.free/BYTES_IN_GB, 2),
                "used_gb": round(usage.used/BYTES_IN_GB, 2),
                "free_pct": round(_pct(usage.free, usage.total), 2),
                "used_pct": round(_pct(usage.used, usage.total), 2)
            })
        except (PermissionError, OSError):
            continue
    
    # Collect disk I/O with error handling
    now = time.time()
    try:
        cur = psutil.disk_io_counters(perdisk=True)
        io = {}
        if prev_disk_io and cur:
            dt = max(0.001, now - prev_disk_io["ts"])
            for name, s2 in cur.items():
                s1 = prev_disk_io["data"].get(name)
                if s1:
                    rps = (s2.read_count - s1.read_count)/dt
                    wps = (s2.write_count - s1.write_count)/dt
                    rBps = (s2.read_bytes - s1.read_bytes)/dt
                    wBps = (s2.write_bytes - s1.write_bytes)/dt
                    io[name] = {
                        "rps": round(rps, 2), 
                        "wps": round(wps, 2), 
                        "rBps": round(rBps, 2), 
                        "wBps": round(wBps, 2)
                    }
        snapshot = {"ts": now, "data": cur}
    except Exception:
        snapshot = {"ts": now, "data": {}}
        io = {}
    
    return {
        "disks": disks, 
        "io": io, 
        "_snapshot": snapshot,
        "total_disks": len(disks)
    }

def collect_network(prev_net=None):
    """Collect network metrics with enhanced error handling"""
    now = time.time()
    stats = {}
    
    try:
        cur = psutil.net_io_counters(pernic=True)
        if prev_net and cur:
            dt = max(0.001, now - prev_net["ts"])
            for nic, s2 in cur.items():
                s1 = prev_net["data"].get(nic)
                if s1:
                    rx = (s2.bytes_recv - s1.bytes_recv)/dt
                    tx = (s2.bytes_sent - s1.bytes_sent)/dt
                    err = (s2.errin - s1.errin + s2.errout - s1.errout)/dt
                    drop = (s2.dropin - s1.dropin + s2.dropout - s1.dropout)/dt
                    stats[nic] = {
                        "rx_Bps": round(rx, 2), 
                        "tx_Bps": round(tx, 2), 
                        "errors_per_s": round(err, 2), 
                        "drops_per_s": round(drop, 2)
                    }
        snapshot = {"ts": now, "data": cur}
    except Exception:
        snapshot = {"ts": now, "data": {}}
        cur = {}
    
    return {
        "nics": list(cur.keys()), 
        "stats": stats, 
        "_snapshot": snapshot,
        "active_nics": len([nic for nic, stat in stats.items() if stat.get('rx_Bps', 0) > 0 or stat.get('tx_Bps', 0) > 0])
    }

def collect_system_info():
    """Collect additional system information"""
    try:
        boot_time = psutil.boot_time()
        uptime = time.time() - boot_time
        
        return {
            "boot_time": boot_time,
            "uptime_seconds": int(uptime),
            "uptime_hours": round(uptime / 3600, 2),
            "uptime_days": round(uptime / 86400, 2)
        }
    except Exception:
        return {
            "boot_time": 0,
            "uptime_seconds": 0,
            "uptime_hours": 0,
            "uptime_days": 0
        }
