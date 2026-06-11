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
DJANGO_ALLOWED_HOSTS=api.example.org
DJANGO_FRONTEND_ORIGINS=https://portal.example.org
DJANGO_CSRF_TRUSTED_ORIGINS=https://portal.example.org
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

Deployment verification:

```bash
uv run python backend/manage.py check --deploy
uv run python backend/manage.py test resources
cd frontend && npm run build
```
