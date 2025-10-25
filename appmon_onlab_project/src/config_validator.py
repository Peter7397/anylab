class ConfigValidator:
    def __init__(self):
        self.errors = []
        self.warnings = []

    def validate_config(self, cfg: dict):
        self.errors = []; self.warnings = []
        self.validate_required_fields(cfg)
        self.validate_paths(cfg.get("paths", {}))
        self.validate_alert_server(cfg.get("alert_server", {}))
        self.validate_sources(cfg.get("sources", []))
        self.validate_onlab_integration(cfg.get("onlab_integration", {}))
        return len(self.errors) == 0

    def validate_required_fields(self, cfg):
        for key in ["scan_interval_sec","paths","alert_server","sources"]:
            if key not in cfg: self.errors.append(f"Missing required config key: {key}")

    def validate_paths(self, paths):
        if not isinstance(paths, dict): self.errors.append("paths must be a dict"); return
        for k in ["root","logs","state","queue","temp"]:
            if k not in paths: self.errors.append(f"paths.{k} missing")

    def validate_alert_server(self, alert_server):
        if not isinstance(alert_server, dict): self.errors.append("alert_server must be dict"); return
        if "base_url" not in alert_server: self.errors.append("alert_server.base_url missing")
        if "api_key" not in alert_server: self.warnings.append("alert_server.api_key missing or default")

    def validate_sources(self, sources):
        if not isinstance(sources, list) or not sources:
            self.errors.append("sources must be a non-empty list"); return
        for i, s in enumerate(sources):
            if "name" not in s: self.errors.append(f"sources[{i}].name missing")
            if "files" not in s or not isinstance(s["files"], list) or not s["files"]:
                self.errors.append(f"sources[{i}].files must be a non-empty list")
            if "patterns" not in s or not isinstance(s["patterns"], list) or not s["patterns"]:
                self.errors.append(f"sources[{i}].patterns must be a non-empty list")
            else:
                for j, p in enumerate(s["patterns"]):
                    if "name" not in p or "regex" not in p or "severity" not in p:
                        self.errors.append(f"sources[{i}].patterns[{j}] missing name/regex/severity")

    def validate_onlab_integration(self, integ):
        if not isinstance(integ, dict): return
        if integ.get("upload_metrics") and integ.get("metrics_interval_sec", None) is None:
            self.warnings.append("onlab_integration.upload_metrics is true but metrics_interval_sec not set; using default 60")
