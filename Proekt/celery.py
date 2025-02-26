from __future__ import absolute_import, unicode_literals
import os
from celery import Celery

# Устанавливаем default настройку для приложения Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Proekt.settings")

# Создаём объект Celery
app = Celery("Proekt")

# Используем настройки из Django settings
app.config_from_object("django.conf:settings", namespace="CELERY")

# Автоматически обнаруживаем все задачи в приложениях
app.autodiscover_tasks()

@app.task(bind=True)
def debug_task(self):
    print(f"Request: {self.request!r}")