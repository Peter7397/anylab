import os, json, time, requests
from typing import Dict, Any, Optional
import logging

def _ensure_dir(p): 
    os.makedirs(p, exist_ok=True)

class Uploader:
    def __init__(self, base_dir: str, base_url: str, api_key: str,
                 connect_timeout=5, read_timeout=20, tls_verify=True, ca_bundle=None,
                 retry_attempts=3, retry_delay_sec=5, max_queue_size=1000):
        self.queue_dir = os.path.join(base_dir, "queue")
        _ensure_dir(self.queue_dir)
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = (connect_timeout, read_timeout)
        self.verify = ca_bundle if tls_verify and ca_bundle else tls_verify
        self.retry_attempts = retry_attempts
        self.retry_delay_sec = retry_delay_sec
        self.max_queue_size = max_queue_size
        self.logger = logging.getLogger(__name__)

    def _headers(self):
        return {
            "Authorization": f"Bearer {self.api_key}", 
            "Content-Type": "application/json",
            "User-Agent": "SysMonSvc/2.0.0"
        }

    def _make_request(self, method: str, url: str, **kwargs) -> Optional[requests.Response]:
        """Make HTTP request with retry logic"""
        for attempt in range(self.retry_attempts):
            try:
                response = requests.request(
                    method, 
                    url, 
                    timeout=self.timeout, 
                    verify=self.verify,
                    **kwargs
                )
                
                if response.status_code < 300:
                    return response
                else:
                    self.logger.warning(f"HTTP {response.status_code}: {response.text[:200]}")
                    
            except requests.exceptions.RequestException as e:
                self.logger.warning(f"Request attempt {attempt + 1} failed: {e}")
                
            if attempt < self.retry_attempts - 1:
                time.sleep(self.retry_delay_sec * (attempt + 1))  # Exponential backoff
                
        return None

    def _cleanup_old_queue_files(self, prefix: str):
        """Clean up old queue files to prevent disk space issues"""
        try:
            files = [f for f in os.listdir(self.queue_dir) if f.startswith(prefix)]
            if len(files) > self.max_queue_size:
                files.sort()  # Sort by timestamp (oldest first)
                files_to_remove = files[:-self.max_queue_size]
                for file in files_to_remove:
                    try:
                        os.remove(os.path.join(self.queue_dir, file))
                    except OSError:
                        pass
        except Exception as e:
            self.logger.warning(f"Queue cleanup failed: {e}")

    def post_alert(self, alert: dict, logger):
        """Post alert to OnLab backend with enhanced error handling"""
        if not self.base_url or self.api_key in (None, "", "CHANGE_ME"):
            logger.warning("Alert server not configured; writing alert to queue only.")
            return self._enqueue_json(alert, "alerts")
            
        url = f"{self.base_url}/alerts"
        response = self._make_request("POST", url, json=alert, headers=self._headers())
        
        if response is None:
            logger.error("Alert upload failed after all retries; enqueueing")
            self._enqueue_json(alert, "alerts")
            self._cleanup_old_queue_files("alerts_")

    def post_metrics(self, metrics: dict, logger):
        """Upload system metrics to OnLab with enhanced error handling"""
        if not self.base_url or self.api_key in (None, "", "CHANGE_ME"):
            logger.warning("Metrics server not configured; writing metrics to queue only.")
            return self._enqueue_json(metrics, "metrics")
            
        url = f"{self.base_url}/metrics"
        response = self._make_request("POST", url, json=metrics, headers=self._headers())
        
        if response is None:
            logger.error("Metrics upload failed after all retries; enqueueing")
            self._enqueue_json(metrics, "metrics")
            self._cleanup_old_queue_files("metrics_")
        else:
            logger.debug(f"Metrics uploaded successfully: {response.status_code}")

    def post_zip_with_meta(self, metadata: dict, zip_path: str, logger):
        """Upload zip file with metadata to OnLab"""
        if not os.path.isfile(zip_path): 
            logger.warning(f"Zip file not found: {zip_path}")
            return
            
        if not self.base_url or self.api_key in (None, "", "CHANGE_ME"):
            self._enqueue_json(metadata, "uploads")
            self._enqueue_file(zip_path, "uploads")
            return
            
        url = f"{self.base_url}/uploads"
        files = {
            "metadata": ("metadata.json", json.dumps(metadata), "application/json"),
            "artifact": (os.path.basename(zip_path), open(zip_path, "rb"), "application/zip")
        }
        headers = {"Authorization": f"Bearer {self.api_key}", "User-Agent": "SysMonSvc/2.0.0"}
        
        response = self._make_request("POST", url, files=files, headers=headers)
        
        if response is None:
            logger.error("Upload failed after all retries; enqueueing")
            self._enqueue_json(metadata, "uploads")
            self._enqueue_file(zip_path, "uploads")
            self._cleanup_old_queue_files("uploads_")

    def retry_queue(self, logger, max_items=10):
        """Retry failed uploads from queue with enhanced logic"""
        try:
            files = sorted([f for f in os.listdir(self.queue_dir) if f.endswith('.json')])[:max_items]
            
            for filename in files:
                file_path = os.path.join(self.queue_dir, filename)
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        payload = json.load(f)
                    
                    success = False
                    
                    if filename.startswith("alerts_"):
                        success = self._retry_alert(payload, logger)
                    elif filename.startswith("metrics_"):
                        success = self._retry_metrics(payload, logger)
                    elif filename.startswith("uploads_"):
                        success = self._retry_upload(payload, logger, filename)
                    
                    if success:
                        os.remove(file_path)
                        logger.info(f"Successfully retried: {filename}")
                        
                except Exception as e:
                    logger.warning(f"Retry failed for {filename}: {e}")
                    
        except Exception as e:
            logger.error(f"Queue retry process failed: {e}")

    def _retry_alert(self, payload: dict, logger) -> bool:
        """Retry alert upload"""
        if not self.base_url or self.api_key in (None, "", "CHANGE_ME"):
            return False
            
        url = f"{self.base_url}/alerts"
        response = self._make_request("POST", url, json=payload, headers=self._headers())
        return response is not None and response.status_code < 300

    def _retry_metrics(self, payload: dict, logger) -> bool:
        """Retry metrics upload"""
        if not self.base_url or self.api_key in (None, "", "CHANGE_ME"):
            return False
            
        url = f"{self.base_url}/metrics"
        response = self._make_request("POST", url, json=payload, headers=self._headers())
        return response is not None and response.status_code < 300

    def _retry_upload(self, metadata: dict, logger, filename: str) -> bool:
        """Retry file upload"""
        if not self.base_url or self.api_key in (None, "", "CHANGE_ME"):
            return False
            
        # Find corresponding zip file
        zip_filename = filename.replace('.json', '')
        zip_files = [f for f in os.listdir(self.queue_dir) if f.startswith(zip_filename) and f.endswith('.zip')]
        
        if not zip_files:
            logger.warning(f"No zip file found for {filename}")
            return False
            
        zip_path = os.path.join(self.queue_dir, zip_files[0])
        if not os.path.isfile(zip_path):
            logger.warning(f"Zip file not found: {zip_path}")
            return False
            
        url = f"{self.base_url}/uploads"
        files = {
            "metadata": ("metadata.json", json.dumps(metadata), "application/json"),
            "artifact": (os.path.basename(zip_path), open(zip_path, "rb"), "application/zip")
        }
        headers = {"Authorization": f"Bearer {self.api_key}", "User-Agent": "SysMonSvc/2.0.0"}
        
        response = self._make_request("POST", url, files=files, headers=headers)
        
        if response is not None and response.status_code < 300:
            # Remove both metadata and zip files
            try:
                os.remove(zip_path)
            except OSError:
                pass
            return True
            
        return False

    def _enqueue_json(self, obj: dict, prefix: str):
        """Enqueue JSON object to queue directory"""
        try:
            path = os.path.join(self.queue_dir, f"{prefix}_{int(time.time())}.json")
            with open(path, "w", encoding="utf-8") as f:
                json.dump(obj, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.logger.error(f"Failed to enqueue JSON: {e}")

    def _enqueue_file(self, file_path: str, prefix: str):
        """Enqueue file to queue directory"""
        try:
            import shutil
            dst = os.path.join(self.queue_dir, f"{prefix}_{int(time.time())}_{os.path.basename(file_path)}")
            shutil.copy(file_path, dst)
        except Exception as e:
            self.logger.error(f"Failed to enqueue file: {e}")

    def get_queue_status(self) -> Dict[str, Any]:
        """Get queue status information"""
        try:
            files = os.listdir(self.queue_dir)
            status = {
                'total_files': len(files),
                'alerts': len([f for f in files if f.startswith('alerts_')]),
                'metrics': len([f for f in files if f.startswith('metrics_')]),
                'uploads': len([f for f in files if f.startswith('uploads_')]),
                'queue_size_mb': sum(os.path.getsize(os.path.join(self.queue_dir, f)) for f in files) / (1024*1024)
            }
            return status
        except Exception as e:
            self.logger.error(f"Failed to get queue status: {e}")
            return {'error': str(e)}
