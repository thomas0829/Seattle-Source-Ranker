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
        "workers.fetch_worker",
        "workers.score_worker",
        "workers.pypi_worker"
    ]
)

# Configuration
celery_app.conf.update(
    # Task routing
    task_routes={
        "workers.fetch_worker.*": {"queue": "fetch"},
        "workers.score_worker.*": {"queue": "score"},
        "workers.pypi_worker.*": {"queue": "pypi"},
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
    
    # Task timeouts
    task_soft_time_limit=300,  # 5 minutes
    task_time_limit=600,  # 10 minutes
    
    # Task retries
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    
    # Worker settings
    worker_prefetch_multiplier=4,
    worker_max_tasks_per_child=1000,
    
    # Result backend
    result_expires=3600,  # 1 hour
    result_backend_transport_options={
        "master_name": "mymaster"
    },
    
    # Monitoring
    worker_send_task_events=True,
    task_send_sent_event=True,
)


if __name__ == "__main__":
    celery_app.start()
