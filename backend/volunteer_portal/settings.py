import os
from pathlib import Path
from urllib.parse import urlparse

from django.core.exceptions import ImproperlyConfigured

from .database import build_database_config


BASE_DIR = Path(__file__).resolve().parent.parent


def env_bool(name, default=False):
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def env_int(name, default):
    value = os.environ.get(name)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError as exc:
        raise ImproperlyConfigured(f"{name} must be an integer.") from exc


def env_list(name, default=None):
    value = os.environ.get(name)
    if value is None:
        return list(default or [])
    return [item.strip() for item in value.split(",") if item.strip()]


DJANGO_ENV = os.environ.get("DJANGO_ENV", "local").strip().lower()
if DJANGO_ENV not in {"local", "test", "production"}:
    raise ImproperlyConfigured("DJANGO_ENV must be local, test, or production.")
IS_PRODUCTION = DJANGO_ENV == "production"

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY")
if not SECRET_KEY:
    if IS_PRODUCTION:
        raise ImproperlyConfigured("DJANGO_SECRET_KEY is required when DJANGO_ENV=production.")
    SECRET_KEY = "local-dev-only-volunteer-resource-portal-secret-key-change-in-prod"

DEBUG = env_bool("DJANGO_DEBUG", not IS_PRODUCTION)
if IS_PRODUCTION and DEBUG:
    raise ImproperlyConfigured("DJANGO_DEBUG must be false when DJANGO_ENV=production.")

ALLOWED_HOSTS = env_list(
    "DJANGO_ALLOWED_HOSTS",
    ["localhost", "127.0.0.1"] if DEBUG else [],
)
if not DEBUG and not ALLOWED_HOSTS:
    raise ImproperlyConfigured("DJANGO_ALLOWED_HOSTS is required when DEBUG is false.")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "resources",
]

MIDDLEWARE = [
    "resources.middleware.ConfiguredCorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "resources.middleware.SecurityHeadersMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "resources.middleware.DatabaseLoginThrottleMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "volunteer_portal.urls"

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

WSGI_APPLICATION = "volunteer_portal.wsgi.application"

DATABASES = {"default": build_database_config(os.environ, BASE_DIR, IS_PRODUCTION)}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_STORAGE_BACKEND = (
    "whitenoise.storage.CompressedManifestStaticFilesStorage"
    if IS_PRODUCTION
    else "django.contrib.staticfiles.storage.StaticFilesStorage"
)
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": STATICFILES_STORAGE_BACKEND,
    },
}
MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"
PRIVATE_MEDIA_ROOT = Path(os.environ.get("DJANGO_PRIVATE_MEDIA_ROOT", BASE_DIR / "private_media"))

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
DATA_UPLOAD_MAX_MEMORY_SIZE = env_int("DJANGO_DATA_UPLOAD_MAX_MEMORY_SIZE", 20 * 1024 * 1024)
FILE_UPLOAD_MAX_MEMORY_SIZE = env_int("DJANGO_FILE_UPLOAD_MAX_MEMORY_SIZE", 10 * 1024 * 1024)
RESOURCE_MAX_UPLOAD_BYTES = env_int("DJANGO_RESOURCE_MAX_UPLOAD_BYTES", 100 * 1024 * 1024)
CHECKLIST_MAX_UPLOAD_BYTES = env_int("DJANGO_CHECKLIST_MAX_UPLOAD_BYTES", 10 * 1024 * 1024)
DOCX_MAX_ZIP_ENTRIES = env_int("DJANGO_DOCX_MAX_ZIP_ENTRIES", 400)
DOCX_MAX_UNCOMPRESSED_BYTES = env_int("DJANGO_DOCX_MAX_UNCOMPRESSED_BYTES", 20 * 1024 * 1024)
DOCX_MAX_COMPRESSION_RATIO = env_int("DJANGO_DOCX_MAX_COMPRESSION_RATIO", 1000)

FRONTEND_ORIGINS = env_list(
    "DJANGO_FRONTEND_ORIGINS",
    [] if IS_PRODUCTION else ["http://localhost:5173", "http://127.0.0.1:5173"],
)
if IS_PRODUCTION and not FRONTEND_ORIGINS:
    raise ImproperlyConfigured("DJANGO_FRONTEND_ORIGINS is required when DJANGO_ENV=production.")
CSRF_TRUSTED_ORIGINS = env_list("DJANGO_CSRF_TRUSTED_ORIGINS", FRONTEND_ORIGINS)
CSRF_COOKIE_SAMESITE = os.environ.get("DJANGO_CSRF_COOKIE_SAMESITE", "Lax")
SESSION_COOKIE_SAMESITE = os.environ.get("DJANGO_SESSION_COOKIE_SAMESITE", "Lax")
CSRF_COOKIE_SECURE = env_bool("DJANGO_CSRF_COOKIE_SECURE", IS_PRODUCTION)
SESSION_COOKIE_SECURE = env_bool("DJANGO_SESSION_COOKIE_SECURE", IS_PRODUCTION)
SESSION_COOKIE_HTTPONLY = True

if IS_PRODUCTION and not env_bool("DJANGO_ALLOW_INSECURE_PRODUCTION_COOKIES", False):
    if not CSRF_COOKIE_SECURE or not SESSION_COOKIE_SECURE:
        raise ImproperlyConfigured("Secure CSRF and session cookies are required in production.")

SECURE_SSL_REDIRECT = env_bool("DJANGO_SECURE_SSL_REDIRECT", IS_PRODUCTION)
SECURE_HSTS_SECONDS = env_int("DJANGO_SECURE_HSTS_SECONDS", 0)
SECURE_HSTS_INCLUDE_SUBDOMAINS = env_bool("DJANGO_SECURE_HSTS_INCLUDE_SUBDOMAINS", False)
SECURE_HSTS_PRELOAD = env_bool("DJANGO_SECURE_HSTS_PRELOAD", False)
SECURE_REFERRER_POLICY = os.environ.get("DJANGO_SECURE_REFERRER_POLICY", "same-origin")
SECURE_CONTENT_TYPE_NOSNIFF = True
CSP_ENABLED = env_bool("DJANGO_CSP_ENABLED", IS_PRODUCTION)
CSP_REPORT_ONLY = env_bool("DJANGO_CSP_REPORT_ONLY", False)
CSP_POLICY = os.environ.get(
    "DJANGO_CSP_POLICY",
    "default-src 'self'; object-src 'none'; base-uri 'self'; frame-ancestors 'none'",
)
FIELD_ENCRYPTION_KEY = os.environ.get("DJANGO_FIELD_ENCRYPTION_KEY", "")
AI_CHECKLIST_GENERATION_ENABLED = env_bool("DJANGO_AI_CHECKLIST_GENERATION_ENABLED", True)
CELERY_TASK_ALWAYS_EAGER = env_bool("CELERY_TASK_ALWAYS_EAGER", not IS_PRODUCTION)
CELERY_BROKER_URL = os.environ.get("CELERY_BROKER_URL", "" if IS_PRODUCTION else "redis://localhost:6379/0")
CELERY_RESULT_BACKEND = os.environ.get("CELERY_RESULT_BACKEND", CELERY_BROKER_URL)
if IS_PRODUCTION and AI_CHECKLIST_GENERATION_ENABLED and not CELERY_TASK_ALWAYS_EAGER:
    if not CELERY_BROKER_URL:
        raise ImproperlyConfigured("CELERY_BROKER_URL is required for production checklist generation.")
    broker = urlparse(CELERY_BROKER_URL)
    if broker.hostname in {"localhost", "127.0.0.1", "::1"} and not env_bool("DJANGO_ALLOW_LOCAL_REDIS_IN_PRODUCTION", False):
        raise ImproperlyConfigured("Production Celery broker must not use localhost.")
    if broker.scheme in {"redis", "rediss"} and not broker.password and not env_bool("DJANGO_ALLOW_UNAUTHENTICATED_REDIS", False):
        raise ImproperlyConfigured("Production Redis broker must require authentication.")
CELERY_TASK_TIME_LIMIT = env_int("CELERY_TASK_TIME_LIMIT", 360)
CELERY_TASK_SOFT_TIME_LIMIT = env_int("CELERY_TASK_SOFT_TIME_LIMIT", 330)
CHECKLIST_JOB_CLEANUP_BATCH_SIZE = env_int("DJANGO_CHECKLIST_JOB_CLEANUP_BATCH_SIZE", 100)
CHECKLIST_JOB_CLEANUP_INTERVAL_SECONDS = env_int("DJANGO_CHECKLIST_JOB_CLEANUP_INTERVAL_SECONDS", 3600)
CELERY_BEAT_SCHEDULE = {
    "cleanup-expired-checklist-jobs": {
        "task": "resources.tasks.cleanup_expired_checklist_jobs",
        "schedule": CHECKLIST_JOB_CLEANUP_INTERVAL_SECONDS,
    }
}
LOGIN_THROTTLE_LIMIT = env_int("DJANGO_LOGIN_THROTTLE_LIMIT", 5)
LOGIN_THROTTLE_WINDOW_SECONDS = env_int("DJANGO_LOGIN_THROTTLE_WINDOW_SECONDS", 300)
ADMIN_LOGIN_THROTTLE_LIMIT = env_int("DJANGO_ADMIN_LOGIN_THROTTLE_LIMIT", 5)
ADMIN_LOGIN_THROTTLE_WINDOW_SECONDS = env_int("DJANGO_ADMIN_LOGIN_THROTTLE_WINDOW_SECONDS", 300)
CHECKLIST_JOB_THROTTLE_LIMIT = env_int("DJANGO_CHECKLIST_JOB_THROTTLE_LIMIT", 10)
CHECKLIST_JOB_THROTTLE_WINDOW_SECONDS = env_int("DJANGO_CHECKLIST_JOB_THROTTLE_WINDOW_SECONDS", 3600)
TRUSTED_PROXY_IPS = env_list("DJANGO_TRUSTED_PROXY_IPS", [])
CLIENT_IP_HEADER = os.environ.get("DJANGO_CLIENT_IP_HEADER", "HTTP_X_FORWARDED_FOR")
OPENAI_REQUEST_TIMEOUT_SECONDS = env_int("OPENAI_REQUEST_TIMEOUT_SECONDS", 60)
OPENAI_CHAT_MODEL = os.environ.get("OPENAI_CHAT_MODEL", "gpt-5.4-mini")
OPENAI_CHAT_REASONING_EFFORT = os.environ.get("OPENAI_CHAT_REASONING_EFFORT", "low")
OPENAI_CHECKLIST_MODEL = os.environ.get("OPENAI_CHECKLIST_MODEL", "gpt-5.4-mini")
OPENAI_CHECKLIST_REASONING_EFFORT = os.environ.get("OPENAI_CHECKLIST_REASONING_EFFORT", "low")
OPENAI_CHECKLIST_TIMEOUT_SECONDS = env_int("OPENAI_CHECKLIST_TIMEOUT_SECONDS", 180)
OPENAI_EMBEDDING_MODEL = os.environ.get("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
CHECKLIST_MAX_CONCEPT_NOTE_CHARS = env_int("DJANGO_CHECKLIST_MAX_CONCEPT_NOTE_CHARS", 40000)
CHECKLIST_MAX_SECTIONS = env_int("DJANGO_CHECKLIST_MAX_SECTIONS", 20)
CHECKLIST_MAX_ITEMS_PER_SECTION = env_int("DJANGO_CHECKLIST_MAX_ITEMS_PER_SECTION", 40)
CHAT_MAX_MESSAGE_CHARS = env_int("DJANGO_CHAT_MAX_MESSAGE_CHARS", 3000)
CHAT_MAX_HISTORY_MESSAGES = env_int("DJANGO_CHAT_MAX_HISTORY_MESSAGES", 8)
CHAT_MAX_ANSWER_CHARS = env_int("DJANGO_CHAT_MAX_ANSWER_CHARS", 6000)
CHAT_MAX_GROUNDING_SOURCES = env_int("DJANGO_CHAT_MAX_GROUNDING_SOURCES", 8)
CHAT_MAX_RESOURCE_SOURCES = env_int("DJANGO_CHAT_MAX_RESOURCE_SOURCES", 24)
CHAT_MAX_WEBSITE_SOURCES = env_int("DJANGO_CHAT_MAX_WEBSITE_SOURCES", 8)
CHAT_MAX_LINKED_SOURCES_PER_WEBSITE = env_int("DJANGO_CHAT_MAX_LINKED_SOURCES_PER_WEBSITE", 8)
CHAT_SOURCE_SNIPPET_CHARS = env_int("DJANGO_CHAT_SOURCE_SNIPPET_CHARS", 1800)
CHAT_MAX_DOCX_CHARS = env_int("DJANGO_CHAT_MAX_DOCX_CHARS", 12000)
CHAT_MAX_PDF_PAGES = env_int("DJANGO_CHAT_MAX_PDF_PAGES", 6)
CHAT_SOURCE_FETCH_TIMEOUT_SECONDS = env_int("DJANGO_CHAT_SOURCE_FETCH_TIMEOUT_SECONDS", 8)
CHAT_SOURCE_FETCH_MAX_BYTES = env_int("DJANGO_CHAT_SOURCE_FETCH_MAX_BYTES", 250000)
CHAT_SOURCE_USER_AGENT = os.environ.get("DJANGO_CHAT_SOURCE_USER_AGENT", "GMLSVolunteerEducationChat/1.0")
CHAT_SOURCE_CACHE_TTL_SECONDS = env_int("DJANGO_CHAT_SOURCE_CACHE_TTL_SECONDS", 600)
CHAT_SOURCE_FAILURE_CACHE_TTL_SECONDS = env_int("DJANGO_CHAT_SOURCE_FAILURE_CACHE_TTL_SECONDS", 60)
CHAT_SOURCE_CACHE_MAX_ITEMS = env_int("DJANGO_CHAT_SOURCE_CACHE_MAX_ITEMS", 128)
CHAT_MAX_PARALLEL_MODEL_CALLS = env_int("DJANGO_CHAT_MAX_PARALLEL_MODEL_CALLS", 4)
CHAT_VECTOR_SEARCH_ENABLED = env_bool("DJANGO_CHAT_VECTOR_SEARCH_ENABLED", not IS_PRODUCTION)
CHAT_VECTOR_MAX_CANDIDATES = env_int("DJANGO_CHAT_VECTOR_MAX_CANDIDATES", 64)
CHAT_HYBRID_STRING_WEIGHT = env_int("DJANGO_CHAT_HYBRID_STRING_WEIGHT", 55)
CHAT_HYBRID_VECTOR_WEIGHT = env_int("DJANGO_CHAT_HYBRID_VECTOR_WEIGHT", 45)
CHAT_HYBRID_RRF_K = env_int("DJANGO_CHAT_HYBRID_RRF_K", 60)
RESOURCE_SEARCH_MAX_LENGTH = env_int("DJANGO_RESOURCE_SEARCH_MAX_LENGTH", 120)
UPLOAD_SCAN_COMMAND = os.environ.get("DJANGO_UPLOAD_SCAN_COMMAND", "")
UPLOAD_SCANNING_REQUIRED = env_bool("DJANGO_UPLOAD_SCANNING_REQUIRED", IS_PRODUCTION)
UPLOAD_SCAN_TIMEOUT_SECONDS = env_int("DJANGO_UPLOAD_SCAN_TIMEOUT_SECONDS", 30)

if env_bool("DJANGO_USE_X_FORWARDED_PROTO", IS_PRODUCTION):
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "security": {
            "format": "%(asctime)s %(levelname)s %(name)s %(message)s",
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "security",
        }
    },
    "loggers": {
        "resources.security": {
            "handlers": ["console"],
            "level": os.environ.get("DJANGO_SECURITY_LOG_LEVEL", "INFO"),
            "propagate": False,
        }
    },
}
