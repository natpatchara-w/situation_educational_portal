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
- The backend uses `backend/db.sqlite3` unless `DJANGO_DATABASE_URL` or `DATABASE_URL` is set.
- The frontend calls `http://<current-host>:8000` during Vite development unless `VITE_API_BASE_URL` is set.

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
DJANGO_DATABASE_URL=postgres://portal:<password>@db.example.org:5432/volunteer_portal?sslmode=require
CELERY_BROKER_URL=rediss://:<password>@redis.example.org:6379/0
CELERY_RESULT_BACKEND=rediss://:<password>@redis.example.org:6379/0
```

`DJANGO_ENV=production` rejects missing database URLs and unsafe SQLite production use by default. Keep SQLite for local development only. A PostgreSQL URL can also be supplied through the common `DATABASE_URL` variable.

Optional database tuning:

```bash
DJANGO_DB_CONN_MAX_AGE=60
DJANGO_DB_CONN_HEALTH_CHECKS=true
DJANGO_DATABASE_SSL_REQUIRED=true
```

For multiple frontend origins, provide comma-separated exact origins:

```bash
DJANGO_FRONTEND_ORIGINS=https://portal.example.org,https://staging-portal.example.org
DJANGO_CSRF_TRUSTED_ORIGINS=https://portal.example.org,https://staging-portal.example.org
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

Local development defaults to eager mode so checklist generation works without a Redis/Celery worker. Set eager mode explicitly when you want to force synchronous task execution in another isolated debugging environment:

```bash
CELERY_TASK_ALWAYS_EAGER=true
```

Production Redis/Celery broker URLs must be explicit, authenticated, and non-localhost unless a documented override is set. Keep Redis on private networks and prefer TLS-capable `rediss://` URLs when your provider supports them.

Recommended TLS/proxy variables when Django is behind a trusted HTTPS proxy:

```bash
DJANGO_USE_X_FORWARDED_PROTO=true
DJANGO_SECURE_SSL_REDIRECT=true
DJANGO_SESSION_COOKIE_SECURE=true
DJANGO_CSRF_COOKIE_SECURE=true
```

If Django sits behind a trusted reverse proxy and you want rate limits keyed by the original client IP, configure the exact proxy IPs:

```bash
DJANGO_TRUSTED_PROXY_IPS=10.0.0.10,10.0.0.11
DJANGO_CLIENT_IP_HEADER=HTTP_X_FORWARDED_FOR
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

If `VITE_API_BASE_URL` is omitted in a production build, the frontend falls back to the current site origin instead of an HTTP development API.

Upload safety defaults can be tuned with these variables:

```bash
DJANGO_DATA_UPLOAD_MAX_MEMORY_SIZE=20971520
DJANGO_FILE_UPLOAD_MAX_MEMORY_SIZE=10485760
DJANGO_RESOURCE_MAX_UPLOAD_BYTES=20971520
DJANGO_CHECKLIST_MAX_UPLOAD_BYTES=10485760
DJANGO_DOCX_MAX_ZIP_ENTRIES=400
DJANGO_DOCX_MAX_UNCOMPRESSED_BYTES=20971520
DJANGO_DOCX_MAX_COMPRESSION_RATIO=1000
DJANGO_UPLOAD_SCANNING_REQUIRED=true
DJANGO_UPLOAD_SCAN_COMMAND=clamscan --no-summary
DJANGO_UPLOAD_SCAN_TIMEOUT_SECONDS=30
```

Production defaults require upload scanning. `DJANGO_UPLOAD_SCAN_COMMAND` is split into arguments and executed without a shell, with the temporary uploaded-file path appended as the final argument.

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

Expired checklist cleanup is registered in Celery beat by default:

```bash
DJANGO_CHECKLIST_JOB_CLEANUP_INTERVAL_SECONDS=3600
uv run celery -A volunteer_portal beat --workdir backend --loglevel INFO
```

You can also run cleanup manually or through cron:

```bash
uv run celery -A volunteer_portal call resources.tasks.cleanup_expired_checklist_jobs --workdir backend
uv run python backend/manage.py cleanup_checklist_jobs
```

Resource access levels are configured per resource in Django admin:

- `All authenticated users`
- `Checklist generators`
- `Staff only`

The API enforces the same visibility rules for both listing and downloading resources.

Throttle defaults can be tuned per deployment:

```bash
DJANGO_LOGIN_THROTTLE_LIMIT=5
DJANGO_LOGIN_THROTTLE_WINDOW_SECONDS=300
DJANGO_ADMIN_LOGIN_THROTTLE_LIMIT=5
DJANGO_ADMIN_LOGIN_THROTTLE_WINDOW_SECONDS=300
DJANGO_CHECKLIST_JOB_THROTTLE_LIMIT=10
DJANGO_CHECKLIST_JOB_THROTTLE_WINDOW_SECONDS=3600
```

Django can emit CSP headers for API/admin responses:

```bash
DJANGO_CSP_ENABLED=true
DJANGO_CSP_REPORT_ONLY=false
DJANGO_CSP_POLICY="default-src 'self'; object-src 'none'; base-uri 'self'; frame-ancestors 'none'"
```

For the static React frontend host, configure CSP at the CDN/static server. A production starting point:

```text
default-src 'self';
script-src 'self';
style-src 'self';
img-src 'self' data: https://images.unsplash.com;
connect-src https://api.example.org;
frame-src blob:;
object-src 'none';
base-uri 'self';
frame-ancestors 'none'
```

Start with `Content-Security-Policy-Report-Only` if your hosting provider supports report-only rollout, then enforce after verifying login, resource downloads, and PDF previews.

AI checklist generation sends redacted concept-note text to OpenAI. Configure timeout and output limits:

```bash
DJANGO_AI_CHECKLIST_GENERATION_ENABLED=true
OPENAI_REQUEST_TIMEOUT_SECONDS=60
OPENAI_CHECKLIST_MODEL=gpt-5.4-mini
OPENAI_CHECKLIST_REASONING_EFFORT=low
OPENAI_CHECKLIST_TIMEOUT_SECONDS=180
DJANGO_CHECKLIST_MAX_CONCEPT_NOTE_CHARS=40000
DJANGO_CHECKLIST_MAX_SECTIONS=20
DJANGO_CHECKLIST_MAX_ITEMS_PER_SECTION=40
```

The volunteer education chat uses LangChain + LangGraph with the stored OpenAI API key. By default it uses medium reasoning with `gpt-5.4-mini`, and grounds answers on visible educational resources, staff-approved website sources from the in-app Settings page, linked source documents, and built-in portal glossary entries for core disaster education terms. Retrieval uses bilingual query expansion plus hybrid vector/string ranking so English questions can still match Indonesian source text such as `gempa bumi` and `gempabumi`:

```bash
OPENAI_CHAT_MODEL=gpt-5.4-mini
OPENAI_CHAT_REASONING_EFFORT=medium
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
DJANGO_CHAT_MAX_MESSAGE_CHARS=3000
DJANGO_CHAT_MAX_GROUNDING_SOURCES=8
DJANGO_CHAT_MAX_LINKED_SOURCES_PER_WEBSITE=8
DJANGO_CHAT_SOURCE_FETCH_TIMEOUT_SECONDS=8
DJANGO_CHAT_VECTOR_SEARCH_ENABLED=true
DJANGO_CHAT_VECTOR_MAX_CANDIDATES=64
DJANGO_CHAT_HYBRID_STRING_WEIGHT=55
DJANGO_CHAT_HYBRID_VECTOR_WEIGHT=45
DJANGO_CHAT_HYBRID_RRF_K=60
```

Staff users can add public `http` or `https` website sources in Settings. The chat fetches active website sources at answer time, searches linked HTML/text/PDF/DOCX sources discovered from those pages, and skips localhost, private IP, redirects, and non-web URLs.

Before production use:

- Inform admins and authorized checklist generators that concept notes are processed by OpenAI.
- Inform volunteers that education chat questions are processed by OpenAI and grounded on portal resources plus configured websites.
- The API requires an `ai_processing_acknowledged=true` form field before queueing a checklist job.
- Avoid uploading secrets, credentials, or unnecessary personal data.
- Keep provider project spend limits and monitoring enabled.
- Review generated PDFs before sharing them with volunteers.

Deployment verification:

```bash
uv run python backend/manage.py check --deploy
uv run python backend/manage.py test resources
cd frontend && npm run build
```

The repository includes `.github/workflows/security.yml` for these checks, frontend auditing, and Python dependency auditing. Keep the workflow active on deployment branches.
