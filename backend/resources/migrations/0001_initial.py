import django.core.validators
from django.db import migrations, models
import resources.models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Resource",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=180)),
                ("description", models.TextField(blank=True)),
                (
                    "category",
                    models.CharField(
                        choices=[("checklist", "Volunteer Checklist"), ("educational", "Educational Resource")],
                        max_length=20,
                    ),
                ),
                (
                    "pdf_file",
                    models.FileField(
                        upload_to="resources/pdfs/",
                        validators=[
                            django.core.validators.FileExtensionValidator(["pdf", "docx"]),
                            resources.models.validate_resource_file,
                        ],
                        verbose_name="resource file",
                    ),
                ),
                ("uploaded_at", models.DateTimeField(auto_now_add=True)),
                ("is_active", models.BooleanField(default=True)),
            ],
            options={"ordering": ["category", "title"]},
        ),
    ]
