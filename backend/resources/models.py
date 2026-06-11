from pathlib import Path

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
from django.db import models

from .fields import EncryptedTextField
from .upload_validation import validate_docx_archive, validate_file_size


def validate_resource_file(uploaded_file):
    extension = Path(uploaded_file.name).suffix.lower()
    position = uploaded_file.tell()
    uploaded_file.seek(0)

    try:
        validate_file_size(uploaded_file, settings.RESOURCE_MAX_UPLOAD_BYTES, "Resource file")
        if extension == ".pdf":
            if uploaded_file.read(5) != b"%PDF-":
                raise ValidationError("Upload a valid PDF file.")
        elif extension == ".docx":
            validate_docx_archive(uploaded_file)
        else:
            raise ValidationError("Upload a PDF or DOCX file.")
    finally:
        uploaded_file.seek(position)


class Resource(models.Model):
    class Category(models.TextChoices):
        CHECKLIST = "checklist", "Volunteer Checklist"
        EDUCATIONAL = "educational", "Educational Resource"

    title = models.CharField(max_length=180)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=20, choices=Category.choices)
    pdf_file = models.FileField(
        "resource file",
        upload_to="resources/files/",
        validators=[FileExtensionValidator(["pdf", "docx"]), validate_resource_file],
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["category", "title"]

    def __str__(self):
        return self.title


class OpenAISettings(models.Model):
    api_key = EncryptedTextField("OpenAI API key", blank=True)
    checklist_queue_timeout_minutes = models.PositiveIntegerField(
        "checklist queue timeout in minutes",
        default=120,
        help_text="Completed and failed checklist jobs disappear from each user's queue after this many minutes.",
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "OpenAI settings"
        verbose_name_plural = "OpenAI settings"

    def __str__(self):
        return "OpenAI settings"

    @classmethod
    def get_solo(cls):
        settings, _created = cls.objects.get_or_create(pk=1)
        return settings


class ChecklistJob(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        PROCESSING = "processing", "Processing"
        DONE = "done", "Done"
        ERROR = "error", "Error"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="checklist_jobs")
    input_filename = models.CharField(max_length=255)
    output_filename = models.CharField(max_length=255, blank=True)
    concept_note = models.FileField(upload_to="checklist_jobs/concept_notes/")
    generated_pdf = models.FileField(upload_to="checklist_jobs/pdfs/", blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    expires_at = models.DateTimeField()

    class Meta:
        ordering = ["-created_at"]
        permissions = [
            ("can_generate_checklist", "Can generate checklist"),
        ]

    def __str__(self):
        return self.input_filename
