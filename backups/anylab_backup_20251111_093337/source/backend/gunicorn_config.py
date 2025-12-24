# Gunicorn Configuration - Optimized for Resource-Constrained Production
# AnyLab Backend - Minimal Production Setup

import multiprocessing
import os

# Server socket
bind = "0.0.0.0:8001"
backlog = 64  # Reduced from default 2048

# Worker processes - MINIMAL for memory efficiency
workers = 1  # Single worker process - minimal memory footprint
worker_class = "gthread"  # Use threading for concurrency instead of multiple processes
threads = 6  # 6 threads per worker = handle 6 concurrent requests efficiently
worker_connections = 50  # Reduced from default 1000

# Timeouts
timeout = 120  # Request timeout (2 minutes)
keepalive = 5  # Keep-alive connections
graceful_timeout = 30  # Graceful shutdown timeout

# Memory management - Automatic worker recycling
max_requests = 500  # Restart worker after 500 requests (prevent memory leaks)
max_requests_jitter = 50  # Add randomness: 450-550 requests

# Logging
accesslog = "/Volumes/Orico/Anylab103/logs/gunicorn-access.log"
errorlog = "/Volumes/Orico/Anylab103/logs/gunicorn-error.log"
loglevel = "warning"  # Only log warnings/errors (reduce I/O)
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Process naming
proc_name = "anylab_backend"

# Server mechanics
daemon = False  # Don't daemonize - launchd will manage this
pidfile = None  # launchd manages the process
umask = 0
user = None
group = None
tmp_upload_dir = None

# Performance
preload_app = True  # Load application before forking (saves memory)
reuse_port = False  # Not needed for single worker

# SSL (if needed in future)
# keyfile = None
# certfile = None

def on_starting(server):
    """Called just before the master process is initialized."""
    server.log.info("=" * 60)
    server.log.info("AnyLab Backend Starting (Production Mode)")
    server.log.info("=" * 60)
    server.log.info(f"Workers: {workers}")
    server.log.info(f"Threads per worker: {threads}")
    server.log.info(f"Binding: {bind}")
    server.log.info(f"Worker class: {worker_class}")
    server.log.info("=" * 60)

def on_reload(server):
    """Called when configuration is reloaded."""
    server.log.info("Configuration reloaded")

def when_ready(server):
    """Called just after the server is started."""
    server.log.info("Server is ready. Spawning workers")

def worker_int(worker):
    """Called when a worker receives the SIGINT or SIGQUIT signal."""
    worker.log.info("Worker received INT or QUIT signal")

def worker_abort(worker):
    """Called when a worker receives the SIGABRT signal."""
    worker.log.info("Worker received SIGABRT signal")

