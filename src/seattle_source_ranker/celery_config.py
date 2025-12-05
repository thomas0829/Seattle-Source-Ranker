"""
Celery configuration for distributed task processing
"""
import os
from celery import Celery
from kombu import Queue

# Redis connection
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = os.getenv("REDIS_PORT", "6379")
REDIS_DB = os.getenv("REDIS_DB", "0")
REDIS_URL = f"redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}"

# Create Celery app
celery_app = Celery(
    "ssr_workers",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=[
        "workers.collection_worker"
    ]
)

# Configuration
celery_app.conf.update(
    # Task routing
    task_routes={
        "workers.collection_worker.*": {"queue": "default"},
    },

    # Task queues
    task_queues=(
        Queue("fetch", routing_key="fetch"),
        Queue("score", routing_key="score"),
        Queue("pypi", routing_key="pypi"),
        Queue("default", routing_key="default"),
    ),

    # Task execution
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,

    # Task timeouts - increased to handle rate limit waits (up to 1 hour)
    task_soft_time_limit=3300,  # 55 minutes (warn before hard limit)
    task_time_limit=3600,  # 60 minutes (allow for full rate limit wait)

    # Task retries
    task_acks_late=True,
    task_reject_on_worker_lost=True,

    # Worker settings
    worker_prefetch_multiplier=4,
    worker_max_tasks_per_child=1000,

    # Result backend - store full results for recovery
    result_expires=86400,  # 24 hours (keep results for a day)
    result_extended=True,  # Store full task result in backend
    result_backend_transport_options={
        "master_name": "mymaster"
    },

    # Monitoring
    worker_send_task_events=True,
    task_send_sent_event=True,
)


if __name__ == "__main__":
    celery_app.start()
