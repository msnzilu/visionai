# backend/app/workers/celery_app.py
"""
Celery configuration for background tasks
"""

from celery import Celery
from celery.schedules import crontab
from app.core.config import settings

celery_app = Celery(
    "job_platform",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        'app.workers.job_scraper',
        'app.workers.email_sender'
    ]
)

celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,
    task_soft_time_limit=25 * 60,
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
)

celery_app.conf.beat_schedule = {
    'scrape-tech-jobs': {
        'task': 'app.workers.job_scraper.scrape_jobs_task',
        'schedule': crontab(hour='*/6'),
        'args': ('software engineer', 'San Francisco, CA')
    },
    'scrape-data-science-jobs': {
        'task': 'app.workers.job_scraper.scrape_jobs_task',
        'schedule': crontab(hour='*/6', minute=15),
        'args': ('data scientist', 'New York, NY')
    },
    'expire-old-jobs': {
        'task': 'app.workers.job_scraper.expire_old_jobs_task',
        'schedule': crontab(hour=2, minute=0),
        'args': ()
    },
    'clean-expired-cache': {
        'task': 'app.workers.job_scraper.clean_cache_task',
        'schedule': crontab(hour=3, minute=0),
        'args': ()
    },
}