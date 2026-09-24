"""
Celery Task Worker Configuration
================================
Celery application instance configured with Redis broker and result backend.
Includes automatic eager synchronous fallback when running in local or CI environments.
"""

import os
from celery import Celery

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
CELERY_EAGER = os.getenv("CELERY_TASK_ALWAYS_EAGER", "True").lower() in ("true", "1", "yes")

celery_app = Celery(
    "market_ripple_tasks",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=["backend.app.tasks.scoring_tasks"]
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_always_eager=CELERY_EAGER,
    task_eager_propagates=True,
    task_track_started=True,
)
