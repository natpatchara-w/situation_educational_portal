from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

from django.core.exceptions import ImproperlyConfigured


def env_bool(environ, name, default=False):
    value = environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def env_int(environ, name, default):
    value = environ.get(name)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError as exc:
        raise ImproperlyConfigured(f"{name} must be an integer.") from exc


def build_database_config(environ, base_dir, is_production):
    url = environ.get("DJANGO_DATABASE_URL") or environ.get("DATABASE_URL")
    if not url:
        if is_production and not env_bool(environ, "DJANGO_ALLOW_SQLITE_IN_PRODUCTION", False):
            raise ImproperlyConfigured("DJANGO_DATABASE_URL or DATABASE_URL is required when DJANGO_ENV=production.")
        return _with_connection_options(
            {
                "ENGINE": "django.db.backends.sqlite3",
                "NAME": Path(base_dir) / "db.sqlite3",
            },
            environ,
            is_production,
        )

    config = database_config_from_url(url, base_dir)
    if is_production and database_uses_sqlite(config) and not env_bool(environ, "DJANGO_ALLOW_SQLITE_IN_PRODUCTION", False):
        raise ImproperlyConfigured("SQLite is disabled in production unless DJANGO_ALLOW_SQLITE_IN_PRODUCTION=true.")
    if (
        is_production
        and config["ENGINE"] == "django.db.backends.postgresql"
        and env_bool(environ, "DJANGO_DATABASE_SSL_REQUIRED", True)
    ):
        config.setdefault("OPTIONS", {}).setdefault("sslmode", "require")
    return _with_connection_options(config, environ, is_production)


def database_config_from_url(url, base_dir):
    parsed = urlparse(url)
    scheme = parsed.scheme.lower()
    query = parse_qs(parsed.query)

    if scheme in {"sqlite", "sqlite3"}:
        return _sqlite_config(url, parsed, base_dir)
    if scheme in {"postgres", "postgresql"}:
        return _network_database_config("django.db.backends.postgresql", parsed, query)
    if scheme in {"mysql", "mysql2"}:
        return _network_database_config("django.db.backends.mysql", parsed, query)

    raise ImproperlyConfigured("DJANGO_DATABASE_URL must use sqlite, postgres, postgresql, mysql, or mysql2.")


def database_uses_sqlite(config):
    return config.get("ENGINE") == "django.db.backends.sqlite3"


def _sqlite_config(url, parsed, base_dir):
    path = unquote(parsed.path or "")
    if path in {"", "/", "/:memory:", ":memory:"}:
        name = ":memory:" if "memory" in url else Path(base_dir) / "db.sqlite3"
    elif url.startswith(f"{parsed.scheme}:////"):
        name = Path(path)
    else:
        name = Path(base_dir) / path.lstrip("/")
    return {"ENGINE": "django.db.backends.sqlite3", "NAME": name}


def _network_database_config(engine, parsed, query):
    name = unquote(parsed.path.lstrip("/"))
    if not name:
        raise ImproperlyConfigured("Database URL must include a database name.")

    config = {
        "ENGINE": engine,
        "NAME": name,
        "USER": unquote(parsed.username or ""),
        "PASSWORD": unquote(parsed.password or ""),
        "HOST": parsed.hostname or "",
        "PORT": str(parsed.port or ""),
    }
    sslmode = _first_query_value(query, "sslmode")
    if sslmode:
        config["OPTIONS"] = {"sslmode": sslmode}
    return config


def _with_connection_options(config, environ, is_production):
    config["CONN_MAX_AGE"] = env_int(environ, "DJANGO_DB_CONN_MAX_AGE", 60 if is_production else 0)
    config["CONN_HEALTH_CHECKS"] = env_bool(environ, "DJANGO_DB_CONN_HEALTH_CHECKS", is_production)
    return config


def _first_query_value(query, name):
    values = query.get(name)
    if not values:
        return ""
    return values[0]
