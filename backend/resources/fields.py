import base64
import hashlib

from cryptography.fernet import Fernet, InvalidToken
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.db import models


ENCRYPTED_PREFIX = "fernet$"


def _fernet():
    key = getattr(settings, "FIELD_ENCRYPTION_KEY", "")
    if not key:
        if getattr(settings, "IS_PRODUCTION", False):
            raise ImproperlyConfigured("DJANGO_FIELD_ENCRYPTION_KEY is required to encrypt stored secrets.")
        digest = hashlib.sha256(settings.SECRET_KEY.encode("utf-8")).digest()
        key = base64.urlsafe_b64encode(digest)
    if isinstance(key, str):
        key = key.encode("utf-8")
    return Fernet(key)


class EncryptedTextField(models.TextField):
    description = "Text encrypted at rest with Fernet"

    def from_db_value(self, value, expression, connection):
        return self.to_python(value)

    def to_python(self, value):
        if not isinstance(value, str) or not value.startswith(ENCRYPTED_PREFIX):
            return value
        token = value[len(ENCRYPTED_PREFIX) :].encode("utf-8")
        try:
            return _fernet().decrypt(token).decode("utf-8")
        except InvalidToken as exc:
            raise ImproperlyConfigured("Encrypted secret could not be decrypted with the configured key.") from exc

    def get_prep_value(self, value):
        value = super().get_prep_value(value)
        if not value or (isinstance(value, str) and value.startswith(ENCRYPTED_PREFIX)):
            return value
        token = _fernet().encrypt(str(value).encode("utf-8")).decode("utf-8")
        return f"{ENCRYPTED_PREFIX}{token}"
