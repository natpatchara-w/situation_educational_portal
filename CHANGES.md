# Changes

## Revised security report remediation

- Added environment-driven database configuration through `DJANGO_DATABASE_URL` or `DATABASE_URL`, with local SQLite defaults and production fail-closed behavior unless an explicit override allows SQLite.
- Added PostgreSQL driver support through `psycopg[binary]` and refreshed `uv.lock`.
- Tightened production guards for `DJANGO_ENV=production`, debug mode, secure cookies, frontend origins, and authenticated/non-local Celery broker configuration.
- Added proxy-aware client IP handling through `DJANGO_TRUSTED_PROXY_IPS` and `DJANGO_CLIENT_IP_HEADER`.
- Added per-resource access levels for all authenticated users, checklist generators, and staff-only resources, enforced in list and download endpoints.
- Added AI checklist generation disablement and required user acknowledgement before concept notes are sent for AI processing.
- Added configurable prompt-size bounds, upload malware-scanning hooks, search length validation, Celery beat cleanup scheduling, and structured security audit logs.
- Added static frontend security header artifacts for common static hosts.
- Added CI security automation covering tests, migration drift, Django deploy checks, Python dependency audit, frontend build, and npm audit.
- Updated `CONFIGURE.md` with the new database, broker, proxy, scanning, AI, cleanup, and CI configuration requirements.

Verification:

- `uv lock`
- `uv run python backend/manage.py test resources`
- `uv run python backend/manage.py makemigrations --check --dry-run`
- `uv run python backend/manage.py check`
- production-like `uv run python backend/manage.py check --deploy`
- `uv export --format requirements-txt --no-hashes --output-file /tmp/datakind-requirements-audit.txt`
- `uv tool run pip-audit -r /tmp/datakind-requirements-audit.txt`
- `npm run build`
- `npm audit --json`

## SEC-12: Backend dependency locking

- Added `pyproject.toml` and `uv.lock` as the authoritative Python dependency workflow.
- Removed the unused top-level Streamlit requirement and broad pip requirements from the documented install path.
- Updated setup guidance to use `uv sync` and `uv run`.

Verification:

- `uv lock`

## SEC-02: Supported Django release

- Upgraded the backend dependency target from unsupported Django 4.2 to Django 5.2 LTS.
- Refreshed `uv.lock` so deployments resolve a supported Django version.

Verification:

- `uv lock`
- `uv run python backend/manage.py test resources`

## SEC-04: Private storage and checklist retention cleanup

- Moved uploaded resource files, checklist concept notes, and generated PDFs to private file storage under `DJANGO_PRIVATE_MEDIA_ROOT`.
- Added cleanup helpers, a Celery cleanup task, and a `cleanup_checklist_jobs` management command to delete expired checklist files and rows.
- Added `migrate_private_media` to copy legacy files from public media into private storage without deleting originals.
- Ignored local private media in git and documented private media deployment requirements.

Verification:

- `uv run python backend/manage.py test resources`

## SEC-11: AI data handling controls

- Added redaction for obvious emails, phone-like values, and common secret/token patterns before sending concept notes to OpenAI.
- Added OpenAI request timeout configuration.
- Added stricter checklist payload normalization limits for titles, notes, sections, and section items.
- Expanded deployment guidance for AI data handling and user/admin review.

Verification:

- `uv run python backend/manage.py test resources`
- `npm run build`

## SEC-10: UUID public identifiers

- Added UUID public identifiers for resources and checklist jobs.
- Switched API payload IDs and download/preview URLs from integer IDs to UUIDs.
- Kept integer primary keys internal for database relations and background tasks.

Verification:

- `uv run python backend/manage.py test resources`

## SEC-08: CSP and security header controls

- Added configurable CSP middleware for Django responses with production-enabled defaults.
- Added report-only support for CSP rollout.
- Documented a frontend static-host CSP that supports API calls and blob-based PDF previews without `unsafe-eval`.

Verification:

- `uv run python backend/manage.py test resources`

## SEC-09: Strict configured CORS

- Replaced the local-dev CORS middleware naming with explicit configured-origin CORS behavior.
- Kept credentialed CORS restricted to exact `DJANGO_FRONTEND_ORIGINS` matches.
- Added tests for allowed and blocked origins.

Verification:

- `uv run python backend/manage.py test resources`

## SEC-07: Database-backed throttling

- Added hashed database throttle records for API login, admin login, and checklist job creation.
- Added environment-tunable throttle limits and windows.
- Reset API login throttles after successful authentication.

Verification:

- `uv run python backend/manage.py test resources`

## SEC-05: Upload size and DOCX safety limits

- Added shared upload validation for file size, DOCX structure, zip entry count, uncompressed size, and compression ratio.
- Applied the checks to admin resource uploads and checklist concept-note uploads.
- Added environment-tunable upload limits for local and production deployments.

Verification:

- `uv run python backend/manage.py test resources`

## SEC-06: Asynchronous checklist generation

- Added Celery and Redis dependencies plus a Django Celery app.
- Changed checklist job creation to enqueue a background generation task and return `202 Accepted`.
- Moved OpenAI calls and PDF rendering into the Celery task so web requests no longer perform expensive generation work.
- Deprecated the synchronous checklist generation endpoint with an explicit queued-endpoint response.
- Added worker configuration guidance.

Verification:

- `uv lock`
- `uv run python backend/manage.py test resources`

## SEC-01: Environment-driven deployment settings

- Replaced hard-coded Django debug and secret settings with local/prod environment handling.
- Added production cookie, HTTPS, proxy, host, CSRF trusted-origin, and security-header settings.
- Added frontend `VITE_API_BASE_URL` support so split-origin production deployments do not hard-code HTTP localhost.
- Started `CONFIGURE.md` with safe local and production configuration guidance.

Verification:

- `uv run python backend/manage.py test resources`

## SEC-03: Encrypted OpenAI API key storage

- Added an encrypted model field for the OpenAI API key using Fernet encryption at rest.
- Updated Django admin so stored keys are masked and only replaced when a new key is submitted.
- Added a migration that encrypts existing plaintext key values on upgrade.
- Added configuration guidance for `DJANGO_FIELD_ENCRYPTION_KEY`.

Verification:

- `uv lock`
- `uv run python backend/manage.py test resources`
