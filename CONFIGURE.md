# Configuration Guide

This project is a split-origin application: the React frontend is served as a static app, and Django serves the authenticated API.

## Local Development

Install Python dependencies from the locked `uv` environment:

```bash
uv sync
```

Run Django locally:

```bash
uv run python backend/manage.py migrate
uv run python backend/manage.py createsuperuser
uv run python backend/manage.py runserver 8000
```

Run the frontend locally:

```bash
cd frontend
npm install
npm run dev
```

The local defaults are intentionally HTTP-friendly:

- `DJANGO_ENV=local` is implied.
- `DJANGO_DEBUG=true` is implied.
- `DJANGO_SECRET_KEY` is optional locally.
- The frontend calls `http://<current-host>:8000` unless `VITE_API_BASE_URL` is set.

## Production Baseline

Set production configuration through environment variables or a secret manager. Do not commit production secrets.

Required Django variables:

```bash
DJANGO_ENV=production
DJANGO_DEBUG=false
DJANGO_SECRET_KEY=<long-random-secret>
DJANGO_FIELD_ENCRYPTION_KEY=<fernet-key>
DJANGO_ALLOWED_HOSTS=api.example.org
DJANGO_FRONTEND_ORIGINS=https://portal.example.org
DJANGO_CSRF_TRUSTED_ORIGINS=https://portal.example.org
CELERY_BROKER_URL=redis://redis.example.org:6379/0
CELERY_RESULT_BACKEND=redis://redis.example.org:6379/0
```

Generate an encryption key for encrypted application secrets:

```bash
uv run python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Keep `DJANGO_FIELD_ENCRYPTION_KEY` stable for the lifetime of encrypted database values. Rotate it only with a planned re-encryption migration.

Run a Celery worker anywhere checklist generation should execute:

```bash
uv run celery -A volunteer_portal worker --workdir backend --loglevel INFO
```

For local development with Redis on localhost:

```bash
redis-server
uv run celery -A volunteer_portal worker --workdir backend --loglevel INFO
```

Use eager mode only for tests or isolated debugging:

```bash
CELERY_TASK_ALWAYS_EAGER=true
```

Recommended TLS/proxy variables when Django is behind a trusted HTTPS proxy:

```bash
DJANGO_USE_X_FORWARDED_PROTO=true
DJANGO_SECURE_SSL_REDIRECT=true
DJANGO_SESSION_COOKIE_SECURE=true
DJANGO_CSRF_COOKIE_SECURE=true
```

Only enable HSTS after confirming HTTPS and proxy behavior in production:

```bash
DJANGO_SECURE_HSTS_SECONDS=3600
```

Increase the HSTS value gradually after validation. Misconfigured HSTS can lock users out for the configured duration.

Frontend production build:

```bash
cd frontend
VITE_API_BASE_URL=https://api.example.org npm run build
```

Upload safety defaults can be tuned with these variables:

```bash
DJANGO_DATA_UPLOAD_MAX_MEMORY_SIZE=20971520
DJANGO_FILE_UPLOAD_MAX_MEMORY_SIZE=10485760
DJANGO_RESOURCE_MAX_UPLOAD_BYTES=20971520
DJANGO_CHECKLIST_MAX_UPLOAD_BYTES=10485760
DJANGO_DOCX_MAX_ZIP_ENTRIES=400
DJANGO_DOCX_MAX_UNCOMPRESSED_BYTES=20971520
DJANGO_DOCX_MAX_COMPRESSION_RATIO=1000
```

Private uploaded files are stored outside public media:

```bash
DJANGO_PRIVATE_MEDIA_ROOT=/srv/volunteer-portal/private-media
```

Do not serve `DJANGO_PRIVATE_MEDIA_ROOT` directly through a web server or CDN. Files should be downloaded only through authenticated Django API views.

For deployments with legacy files under `MEDIA_ROOT`, copy them into private storage before switching traffic:

```bash
uv run python backend/manage.py migrate_private_media --dry-run
uv run python backend/manage.py migrate_private_media
```

Schedule expired checklist cleanup with either Celery or cron:

```bash
uv run celery -A volunteer_portal call resources.tasks.cleanup_expired_checklist_jobs --workdir backend
uv run python backend/manage.py cleanup_checklist_jobs
```

Throttle defaults can be tuned per deployment:

```bash
DJANGO_LOGIN_THROTTLE_LIMIT=5
DJANGO_LOGIN_THROTTLE_WINDOW_SECONDS=300
DJANGO_ADMIN_LOGIN_THROTTLE_LIMIT=5
DJANGO_ADMIN_LOGIN_THROTTLE_WINDOW_SECONDS=300
DJANGO_CHECKLIST_JOB_THROTTLE_LIMIT=10
DJANGO_CHECKLIST_JOB_THROTTLE_WINDOW_SECONDS=3600
```

Deployment verification:

```bash
uv run python backend/manage.py check --deploy
uv run python backend/manage.py test resources
cd frontend && npm run build
```
