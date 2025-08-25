# config/celery.py
from __future__ import absolute_import, unicode_literals

import os
from datetime import timedelta

from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('config')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

app.conf.beat_schedule = {
    'clear-redis-cache': {
        'task': 'api.tasks.clear_expired_cache',  
        'schedule': timedelta(minutes=60),
    },
}
