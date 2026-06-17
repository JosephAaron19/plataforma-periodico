import os
from celery import Celery

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('config')

# Configure Celery using settings from Django settings module.
# Using 'CELERY_' prefix means all celery config keys should be prefixed with 'CELERY_'.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django app configs.
app.autodiscover_tasks()

@app.task(name='health_check_task')
def health_check_task():
    """
    A simple technical check task that returns a success message
    without performing any database mutations.
    """
    return {"status": "ok", "message": "Celery task execution succeeded"}
