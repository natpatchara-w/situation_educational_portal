# Changes

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

## SEC-01: Environment-driven deployment settings

- Replaced hard-coded Django debug and secret settings with local/prod environment handling.
- Added production cookie, HTTPS, proxy, host, CSRF trusted-origin, and security-header settings.
- Added frontend `VITE_API_BASE_URL` support so split-origin production deployments do not hard-code HTTP localhost.
- Started `CONFIGURE.md` with safe local and production configuration guidance.

Verification:

- `uv run python backend/manage.py test resources`
