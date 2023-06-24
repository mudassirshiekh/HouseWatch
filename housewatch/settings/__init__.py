"""
Django settings for housewatch project.

Generated by 'django-admin startproject' using Django 4.1.1.

For more information on this file, see
https://docs.djangoproject.com/en/4.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.1/ref/settings/
"""

import os
import sys
from datetime import timedelta
from pathlib import Path
from typing import Any, Callable, Optional
import dj_database_url

from django.core.exceptions import ImproperlyConfigured
from kombu import Exchange, Queue

from housewatch.utils import str_to_bool

# TODO: Figure out why things dont work on cloud without debug
DEBUG = os.getenv("DEBUG", "false").lower() in ["true", "1"]

if "mypy" in sys.modules:
    DEBUG = True


def get_from_env(key: str, default: Any = None, *, optional: bool = False, type_cast: Optional[Callable] = None) -> Any:
    value = os.getenv(key)
    if value is None or value == "":
        if optional:
            return None
        if default is not None:
            return default
        else:
            if not DEBUG:
                raise ImproperlyConfigured(f'The environment variable "{key}" is required to run HouseWatch!')
    if type_cast is not None:
        return type_cast(value)
    return value


# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
TEST = False

if "pytest" in sys.modules or "mypy" in sys.modules:
    TEST = True

# this is ok for now as we don't have auth, crypto, or anything that uses the secret key
SECRET_KEY = get_from_env("SECRET_KEY", "not-so-secret")

if DEBUG:
    print("WARNING: Running debug mode!")

is_development = DEBUG and not TEST


SECURE_SSL_REDIRECT = False
if not DEBUG and not TEST:
    USE_X_FORWARDED_HOST = True
    USE_X_FORWARDED_PORT = True
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")


CSRF_TRUSTED_ORIGINS = ["https://*.posthog.dev", "https://*.posthog.com"]


APPEND_SLASH = False


# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "housewatch.apps.HouseWatchConfig",
    "rest_framework",
    "corsheaders",
]


MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "housewatch.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

ALLOWED_HOSTS = ["*"]

CORS_ORIGIN_ALLOW_ALL = True

WSGI_APPLICATION = "housewatch.wsgi.application"


DATABASE_URL = get_from_env("DATABASE_URL", "")


if DATABASE_URL:
    DATABASES = {"default": dj_database_url.config(default=DATABASE_URL, conn_max_age=600)}
else:
    raise ImproperlyConfigured("DATABASE_URL environment variable not set!")


# Password validation
# https://docs.djangoproject.com/en/4.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# Internationalization
# https://docs.djangoproject.com/en/4.1/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.1/howto/static-files/

STATIC_URL = "/static/"
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# Django REST Framework
# https://github.com/encode/django-rest-framework/

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        # "rest_framework.authentication.BasicAuthentication",
        # "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.LimitOffsetPagination",
    "DEFAULT_PERMISSION_CLASSES": [],
    "DEFAULT_RENDERER_CLASSES": ["rest_framework.renderers.JSONRenderer"],
    "PAGE_SIZE": 100,
    "EXCEPTION_HANDLER": "exceptions_hog.exception_handler",
    "TEST_REQUEST_DEFAULT_FORMAT": "json",
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}

# See https://docs.djangoproject.com/en/3.2/ref/settings/#std:setting-DATABASE-DISABLE_SERVER_SIDE_CURSORS
DEFAULT_AUTO_FIELD = "django.db.models.AutoField"

# DRF Exceptions Hog
# https://github.com/PostHog/drf-exceptions-hog#readme
# EXCEPTIONS_HOG = {
#     "EXCEPTION_REPORTING": "housewatch.utils.exception_reporter",
# }

EVENT_USAGE_CACHING_TTL = get_from_env("EVENT_USAGE_CACHING_TTL", 12 * 60 * 60, type_cast=int)


if TEST or DEBUG:
    REDIS_URL = get_from_env("REDIS_URL", "redis://localhost:6379")
else:
    REDIS_URL = get_from_env("REDIS_URL")


CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": REDIS_URL,
        "OPTIONS": {"CLIENT_CLASS": "django_redis.client.DefaultClient"},
        "KEY_PREFIX": "housewatch",
    }
}


# Only listen to the default queue "celery", unless overridden via the CLI
CELERY_QUEUES = (Queue("celery", Exchange("celery"), "celery"),)
CELERY_DEFAULT_QUEUE = "celery"
CELERY_IMPORTS = []  # type: ignore
CELERY_BROKER_URL = REDIS_URL  # celery connects to redis
CELERY_BEAT_MAX_LOOP_INTERVAL = 30  # sleep max 30sec before checking for new periodic events
CELERY_RESULT_BACKEND = REDIS_URL  # stores results for lookup when processing
CELERY_IGNORE_RESULT = True  # only applies to delay(), must do @shared_task(ignore_result=True) for apply_async
CELERY_RESULT_EXPIRES = timedelta(days=4)  # expire tasks after 4 days instead of the default 1
REDBEAT_LOCK_TIMEOUT = 45  # keep distributed beat lock for 45sec

if TEST:
    import celery

    celery.current_app.conf.task_always_eager = True
    celery.current_app.conf.task_eager_propagates = True


POSTHOG_PROJECT_API_KEY = get_from_env("POSTHOG_PROJECT_API_KEY", "123456789")


# ClickHouse

CLICKHOUSE_HOST = get_from_env("CLICKHOUSE_HOST", "localhost")
CLICKHOUSE_VERIFY = str_to_bool(get_from_env("CLICKHOUSE_VERIFY", "True"))
CLICKHOUSE_CA = get_from_env("CLICKHOUSE_CA", "")
CLICKHOUSE_SECURE = str_to_bool(get_from_env("CLICKHOUSE_SECURE", "True"))
CLICKHOUSE_DATABASE = get_from_env("CLICKHOUSE_DATABASE", "defaul")
CLICKHOUSE_USER = get_from_env("CLICKHOUSE_USER", "default")
CLICKHOUSE_PASSWORD = get_from_env("CLICKHOUSE_PASSWORD", "")
