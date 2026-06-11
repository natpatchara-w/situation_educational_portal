import hashlib

from django.db import transaction
from django.utils import timezone

from .models import ThrottleRecord


def throttle_key(*parts):
    normalized = ":".join(str(part or "").strip().lower() for part in parts)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def client_ip(request):
    return request.META.get("REMOTE_ADDR", "")


def is_throttled(scope, key_hash, limit, window_seconds):
    now = timezone.now()
    window_start = now - timezone.timedelta(seconds=window_seconds)
    with transaction.atomic():
        record, _created = ThrottleRecord.objects.select_for_update().get_or_create(
            scope=scope,
            key_hash=key_hash,
            defaults={"attempts": 0, "first_attempt_at": now},
        )
        if record.first_attempt_at <= window_start:
            record.attempts = 0
            record.first_attempt_at = now
        if record.attempts >= limit:
            record.save(update_fields=["attempts", "first_attempt_at", "updated_at"])
            return True
        record.attempts += 1
        record.save(update_fields=["attempts", "first_attempt_at", "updated_at"])
        return False


def reset_throttle(scope, key_hash):
    ThrottleRecord.objects.filter(scope=scope, key_hash=key_hash).delete()
