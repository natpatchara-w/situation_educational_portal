# Changes

## SEC-12: Backend dependency locking

- Added `pyproject.toml` and `uv.lock` as the authoritative Python dependency workflow.
- Removed the unused top-level Streamlit requirement and broad pip requirements from the documented install path.
- Updated setup guidance to use `uv sync` and `uv run`.

Verification:

- `uv lock`
