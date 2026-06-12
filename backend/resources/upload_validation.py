import shlex
import subprocess
import tempfile
from zipfile import BadZipFile, ZipFile

from django.conf import settings
from django.core.exceptions import ValidationError


def uploaded_file_size(uploaded_file):
    size = getattr(uploaded_file, "size", None)
    if size is not None:
        return size
    position = uploaded_file.tell()
    uploaded_file.seek(0, 2)
    size = uploaded_file.tell()
    uploaded_file.seek(position)
    return size


def validate_file_size(uploaded_file, max_bytes, label):
    if uploaded_file_size(uploaded_file) > max_bytes:
        raise ValidationError(f"{label} must be {max_bytes // (1024 * 1024)} MB or smaller.")


def scan_uploaded_file(uploaded_file, label):
    command = getattr(settings, "UPLOAD_SCAN_COMMAND", "")
    if not command:
        if getattr(settings, "UPLOAD_SCANNING_REQUIRED", False):
            raise ValidationError(f"{label} could not be accepted because upload scanning is not configured.")
        return

    position = uploaded_file.tell()
    uploaded_file.seek(0)
    try:
        with tempfile.NamedTemporaryFile(prefix="upload-scan-", suffix=".bin") as temporary_file:
            for chunk in iter(lambda: uploaded_file.read(1024 * 1024), b""):
                temporary_file.write(chunk)
            temporary_file.flush()
            result = subprocess.run(
                [*shlex.split(command), temporary_file.name],
                capture_output=True,
                check=False,
                text=True,
                timeout=getattr(settings, "UPLOAD_SCAN_TIMEOUT_SECONDS", 30),
            )
    except subprocess.TimeoutExpired as exc:
        raise ValidationError(f"{label} scan timed out.") from exc
    finally:
        uploaded_file.seek(position)

    if result.returncode != 0:
        raise ValidationError(f"{label} failed security scanning.")


def validate_docx_archive(uploaded_file):
    position = uploaded_file.tell()
    uploaded_file.seek(0)
    try:
        try:
            with ZipFile(uploaded_file) as archive:
                entries = archive.infolist()
        except BadZipFile as exc:
            raise ValidationError("Upload a valid DOCX file.") from exc

        names = {entry.filename for entry in entries}
        if "[Content_Types].xml" not in names or "word/document.xml" not in names:
            raise ValidationError("Upload a valid DOCX file.")

        if len(entries) > settings.DOCX_MAX_ZIP_ENTRIES:
            raise ValidationError("DOCX file has too many internal files.")

        total_uncompressed = sum(entry.file_size for entry in entries)
        if total_uncompressed > settings.DOCX_MAX_UNCOMPRESSED_BYTES:
            raise ValidationError("DOCX file expands to too much data.")

        total_compressed = max(sum(entry.compress_size for entry in entries), 1)
        if total_uncompressed / total_compressed > settings.DOCX_MAX_COMPRESSION_RATIO:
            raise ValidationError("DOCX file compression ratio is too high.")
    finally:
        uploaded_file.seek(position)
