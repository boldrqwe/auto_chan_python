# celery_app.py
from celery import Celery

app = Celery(
    'tasks',
    broker='redis://localhost:6379/0',
    backend='redis://localhost:6379/0'
)

# Настройка периодических задач
app.conf.beat_schedule = {
    'collect-media-every-minute': {
        'task': 'tasks.job_collect_media',
        'schedule': 60.0,  # каждые 60 секунд
        'args': ('@your_channel_name', 10)  # передаем параметры
    },
}
app.conf.timezone = 'UTC'
