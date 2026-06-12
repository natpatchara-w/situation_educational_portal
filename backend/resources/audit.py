import logging


security_logger = logging.getLogger("resources.security")


def audit_event(event, request=None, user=None, **fields):
    user = user or getattr(request, "user", None)
    payload = {
        "event": event,
        "user_id": getattr(user, "id", None),
        "username": getattr(user, "get_username", lambda: "")(),
        "path": getattr(request, "path", ""),
        "remote_addr": getattr(request, "META", {}).get("REMOTE_ADDR", "") if request else "",
        **fields,
    }
    safe_payload = " ".join(f"{key}={value}" for key, value in payload.items() if value not in {None, ""})
    security_logger.info(safe_payload)
