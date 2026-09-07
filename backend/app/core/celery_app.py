import os
import sys
from celery import Celery
from celery.schedules import crontab

# Ensure app is in path when celery runs standalone
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

# Connect to the Redis container specified in BRAIN.md step 0
redis_url = os.environ.get('CELERY_BROKER_URL', 'redis://localhost:6379/0')

celery_app = Celery(
    "dfir_worker",
    broker=redis_url,
    backend=redis_url
)

celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
)

# Daily retention task
celery_app.conf.beat_schedule = {
    'purge-old-cases-daily': {
        'task': 'app.core.celery_app.run_retention_purge',
        'schedule': crontab(hour=0, minute=0), # Run daily at midnight
    },
}

@celery_app.task
def run_retention_purge():
    try:
        from app.models.database import purge_old_cases
        count = purge_old_cases()
        print(f"[Retention Policy] Successfully purged {count} old cases.")
        return count
    except Exception as e:
        print(f"[Retention Policy] Error purging cases: {e}")
        return 0
