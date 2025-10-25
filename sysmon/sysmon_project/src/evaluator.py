from statistics import mean
class RollingAvg:
    def __init__(self, window_sec: int):
        self.window_sec = window_sec
        self.points = []

    def add(self, ts: float, value: float):
        self.points.append((ts, value)); self._trim(ts)

    def _trim(self, now_ts: float):
        cutoff = now_ts - self.window_sec
        while self.points and self.points[0][0] < cutoff:
            self.points.pop(0)

    def avg(self) -> float:
        if not self.points: return 0.0
        return mean(v for _, v in self.points)

def eval_sys_thresholds(now_ts, metrics, cfg_thresholds, state):
    breaches = []
    # CPU total
    cpu_total = metrics["cpu"]["cpu_total_pct"]
    w_cpu = state.setdefault("w_cpu", RollingAvg(cfg_thresholds["cpu_total"]["warn_window_sec"]))
    c_cpu = state.setdefault("c_cpu", RollingAvg(cfg_thresholds["cpu_total"]["crit_window_sec"]))
    w_cpu.add(now_ts, cpu_total); c_cpu.add(now_ts, cpu_total)
    if w_cpu.avg() > cfg_thresholds["cpu_total"]["warn_pct"]:
        breaches.append({"metric":"CPU Total","severity":"warning","value":round(w_cpu.avg(),1),
                         "threshold":cfg_thresholds["cpu_total"]["warn_pct"]})
    if c_cpu.avg() > cfg_thresholds["cpu_total"]["crit_pct"]:
        breaches.append({"metric":"CPU Total","severity":"critical","value":round(c_cpu.avg(),1),
                         "threshold":cfg_thresholds["cpu_total"]["crit_pct"]})
    # CPU per-process
    top_n = cfg_thresholds["cpu_per_process"].get("top_n", 10)
    warn_pp = cfg_thresholds["cpu_per_process"]["warn_pct"]
    crit_pp = cfg_thresholds["cpu_per_process"]["crit_pct"]
    warn_win = cfg_thresholds["cpu_per_process"]["warn_window_sec"]
    crit_win = cfg_thresholds["cpu_per_process"]["crit_window_sec"]
    pp_state = state.setdefault("perproc", {})
    for p in metrics["cpu"]["top_procs"][:50]:
        pid = p["pid"]; val = p["cpu_pct"]
        rolls = pp_state.setdefault(pid, {
            "warn": RollingAvg(warn_win),
            "crit": RollingAvg(crit_win),
            "name": p.get("name","")
        })
        rolls["warn"].add(now_ts, val); rolls["crit"].add(now_ts, val)
        if rolls["warn"].avg() > warn_pp:
            breaches.append({"metric":"CPU Per-Process","severity":"warning","value":round(rolls["warn"].avg(),1),
                             "threshold":warn_pp,"dimensions":{"pid":pid,"proc":rolls["name"]}})
        if rolls["crit"].avg() > crit_pp:
            breaches.append({"metric":"CPU Per-Process","severity":"critical","value":round(rolls["crit"].avg(),1),
                             "threshold":crit_pp,"dimensions":{"pid":pid,"proc":rolls["name"]}})
    # Memory
    ram = metrics["mem"]
    if ram["ram_used_pct"] > cfg_thresholds["ram"]["warn_pct"]:
        breaches.append({"metric":"RAM Usage","severity":"warning","value":ram["ram_used_pct"],
                         "threshold":cfg_thresholds["ram"]["warn_pct"]})
    if ram["ram_used_pct"] > cfg_thresholds["ram"]["crit_pct"]:
        breaches.append({"metric":"RAM Usage","severity":"critical","value":ram["ram_used_pct"],
                         "threshold":cfg_thresholds["ram"]["crit_pct"]})
    if ram["ram_available_mb"] < cfg_thresholds["ram"]["avail_warn_mb"]:
        breaches.append({"metric":"Available RAM (MB)","severity":"warning","value":ram["ram_available_mb"],
                         "threshold":cfg_thresholds["ram"]["avail_warn_mb"]})
    if ram["ram_available_mb"] < cfg_thresholds["ram"]["avail_crit_mb"]:
        breaches.append({"metric":"Available RAM (MB)","severity":"critical","value":ram["ram_available_mb"],
                         "threshold":cfg_thresholds["ram"]["avail_crit_mb"]})
    if ram["pagefile_used_pct"] > cfg_thresholds["ram"]["pagefile_warn_pct"]:
        breaches.append({"metric":"Pagefile Usage","severity":"warning","value":ram["pagefile_used_pct"],
                         "threshold":cfg_thresholds["ram"]["pagefile_warn_pct"]})
    if ram["pagefile_used_pct"] > cfg_thresholds["ram"]["pagefile_crit_pct"]:
        breaches.append({"metric":"Pagefile Usage","severity":"critical","value":ram["pagefile_used_pct"],
                         "threshold":cfg_thresholds["ram"]["pagefile_crit_pct"]})
    # Disk Free
    for d in metrics["disk"]["disks"]:
        mount = d["mount"]; free_pct = d["free_pct"]; free_gb = d["free_gb"]
        rule = None
        for r in cfg_thresholds["disk_free"]:
            if r["drive"] == "*" or r["drive"].rstrip("\\") == mount.rstrip("\\"):
                rule = r; break
        if rule:
            if free_pct < rule["warn_pct"]:
                breaches.append({"metric":"Disk Free","severity":"warning","value":free_pct,
                                 "threshold":rule["warn_pct"],"dimensions":{"drive":mount,"free_gb":free_gb}})
            if free_pct < rule["crit_pct"]:
                crit_min_gb = rule.get("crit_min_gb", None)
                sev = "critical" if (crit_min_gb is None or free_gb <= crit_min_gb) else "warning"
                breaches.append({"metric":"Disk Free","severity":sev,"value":free_pct,
                                 "threshold":rule["crit_pct"],"dimensions":{"drive":mount,"free_gb":free_gb}})
    # Network errors/drops
    for nic, s in metrics["net"]["stats"].items():
        if s["errors_per_s"] > 0:
            breaches.append({"metric":"NIC Errors","severity":"warning","value":s["errors_per_s"],
                             "threshold":0,"dimensions":{"nic":nic}})
        if s["drops_per_s"] > 0:
            breaches.append({"metric":"NIC Drops","severity":"warning","value":s["drops_per_s"],
                             "threshold":0,"dimensions":{"nic":nic}})
    return breaches
