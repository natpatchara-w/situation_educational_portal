from pathlib import Path
from zipfile import BadZipFile, ZipFile

from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
from django.db import models


def validate_resource_file(uploaded_file):
    extension = Path(uploaded_file.name).suffix.lower()
    position = uploaded_file.tell()
    uploaded_file.seek(0)

    try:
        if extension == ".pdf":
            if uploaded_file.read(5) != b"%PDF-":
                raise ValidationError("Upload a valid PDF file.")
        elif extension == ".docx":
            try:
                with ZipFile(uploaded_file) as archive:
                    names = set(archive.namelist())
            except BadZipFile as exc:
                raise ValidationError("Upload a valid DOCX file.") from exc

            if "[Content_Types].xml" not in names or "word/document.xml" not in names:
                raise ValidationError("Upload a valid DOCX file.")
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
    api_key = models.CharField("OpenAI API key", max_length=255, blank=True)
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
