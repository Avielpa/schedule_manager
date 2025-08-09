# schedule_manage/celery.py
# Celery configuration for async task processing

import os
from celery import Celery
from django.conf import settings

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'schedule_manage.settings')

app = Celery('schedule_manage')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps.
app.autodiscover_tasks()

# Celery beat schedule for periodic tasks
app.conf.beat_schedule = {
    'cleanup-old-assignments': {
        'task': 'schedule.tasks.cleanup_old_assignments',
        'schedule': 86400.0,  # Run daily (24 hours)
        'args': (30,)  # Clean assignments older than 30 days
    },
    'validate-schedule-consistency': {
        'task': 'schedule.tasks.validate_schedule_consistency',
        'schedule': 3600.0,  # Run hourly
    },
}

app.conf.timezone = 'UTC'

# Queue configuration
app.conf.task_routes = {
    'schedule.tasks.run_scheduling_algorithm_async': {'queue': 'scheduling'},
    'schedule.tasks.cleanup_old_assignments': {'queue': 'cleanup'},
    'schedule.tasks.validate_schedule_consistency': {'queue': 'validation'},
}

# Task priority settings
app.conf.task_annotations = {
    'schedule.tasks.run_scheduling_algorithm_async': {'priority': 9},
    'schedule.tasks.cleanup_old_assignments': {'priority': 1},
    'schedule.tasks.validate_schedule_consistency': {'priority': 5},
}

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')