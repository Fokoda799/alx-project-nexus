import os
import ssl
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'audioverse.settings')

app = Celery('audioverse')

# Configure broker and backend with SSL
broker_url = os.environ.get('CELERY_BROKER_URL')
backend_url = os.environ.get('CELERY_RESULT_BACKEND')

if broker_url and broker_url.startswith('rediss://'):
    # SSL configuration for secure Redis
    app.conf.broker_use_ssl = {
        'ssl_cert_reqs': ssl.CERT_NONE
    }
    app.conf.redis_backend_use_ssl = {
        'ssl_cert_reqs': ssl.CERT_NONE
    }

app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')