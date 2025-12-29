from celery import Celery
import os

celery_app = Celery(
    'app',
    broker=os.environ.get('REDIS_URL', 'redis://redis:6379/0'),
    backend=os.environ.get('REDIS_URL', 'redis://redis:6379/0'),
    include=['app.tasks']  # Tell Celery where to find tasks
)

celery_app.conf.update(
    # Serialization
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',

    # Timezone
    timezone='UTC',
    enable_utc=True,

    # Task execution limits (reliability)
    task_time_limit=3600,           # Hard limit: 1 hour - task killed after this
    task_soft_time_limit=3300,      # Soft limit: 55 min - raises SoftTimeLimitExceeded

    # Task acknowledgment (prevent task loss on worker crash)
    task_acks_late=True,            # Acknowledge task after completion, not on receipt
    task_reject_on_worker_lost=True,  # Re-queue task if worker dies

    # Worker configuration
    worker_prefetch_multiplier=1,   # Don't prefetch - ensures fair distribution
    worker_concurrency=2,           # Limit concurrent tasks per worker

    # Result backend
    result_expires=86400,           # Results expire after 24 hours

    # Task retry defaults
    task_default_retry_delay=60,    # Wait 60 seconds before retry
    task_max_retries=3,             # Maximum 3 retries

    # Prevent memory leaks
    worker_max_tasks_per_child=50,  # Restart worker after 50 tasks
)
