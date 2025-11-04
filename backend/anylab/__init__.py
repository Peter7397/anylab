from .celery import app as celery_app

__all__ = ('celery_app',)

# Run startup checks when Django starts (only in development)
import os
import time
if os.getenv('RUN_MAIN') == 'true':  # Only run once per Django process
    try:
        from .startup_checks import check_all_services
        import logging
        import threading
        logger = logging.getLogger(__name__)
        
        # Run checks in background (non-blocking)
        def run_checks():
            time.sleep(2)  # Wait for Django to fully initialize
            check_all_services()
        
        threading.Thread(target=run_checks, daemon=True).start()
    except Exception as e:
        # Don't fail startup if checks fail
        pass
