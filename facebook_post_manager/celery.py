from __future__ import absolute_import, unicode_literals
import os
from celery import Celery
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'facebook_post_manager.settings.production')

app = Celery('facebook_post_manager')
app.conf.timezone = 'UTC'
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()
app.log.setup(loglevel='INFO')
