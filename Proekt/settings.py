import os
import dj_database_url
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

# Указан ваш секретный ключ
SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', 'django-insecure-ev@)_*plpryjtb$hciq8_w8(p2aq1*ky=w6j39^#cy%as-wc(s')

DEBUG = os.getenv('DJANGO_DEBUG', 'False') == 'True'

ALLOWED_HOSTS = ['.herokuapp.com', 'localhost', '127.0.0.1']

INSTALLED_APPS = [
    'admin_interface',
    'colorfield',
    'logistics',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'dj_database_url',
    'django_celery_beat',
    'django_extensions',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
]

ROOT_URLCONF = 'Proekt.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / "logistics/templates"],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'Proekt.wsgi.application'

# Database configuration for Heroku (PostgreSQL)
DATABASES = {
    'default': dj_database_url.config(
        default='postgres://user:password@localhost/dbname'
    )
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files configuration for Heroku
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Celery configuration for Redis
CELERY_BROKER_URL = os.getenv('REDIS_URL', 'rediss://:pb63cc0bbffa3eea224e2a5c496e5898029fc1d0c36289a355ca17dcf45cbdf7f@ec2-3-213-54-76.compute-1.amazonaws.com:7800')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'

from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
    'send-payment-reminder-every-day': {
        'task': 'logistics.tasks.send_payment_reminder',  # Путь к задаче
        'schedule': crontab(hour=9, minute=0),  # Запускать задачу каждый день в 9 утра
    },
}

import os
from celery import Celery

app = Celery('Proekt')

# Используем данные из переменных окружения для подключения к Redis
broker_url = os.getenv('REDIS_URL', 'rediss://:pb63cc0bbffa3eea224e2a5c496e5898029fc1d0c36289a355ca17dcf45cbdf7f@ec2-3-213-54-76.compute-1.amazonaws.com:7800')
result_backend = os.getenv('REDIS_URL', 'rediss://:pb63cc0bbffa3eea224e2a5c496e5898029fc1d0c36289a355ca17dcf45cbdf7f@ec2-3-213-54-76.compute-1.amazonaws.com:7800')

if not broker_url or not result_backend:
    raise ValueError("REDIS_URL не установлен в переменных окружения")

app.conf.update(
    broker_url=broker_url,
    result_backend=result_backend,
    accept_content=['json'],
    task_serializer='json',
    result_serializer='json',
    timezone='UTC',
)