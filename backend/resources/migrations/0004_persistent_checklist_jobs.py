from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("resources", "0003_openaisettings"),
    ]

    operations = [
        migrations.AddField(
            model_name="openaisettings",
            name="checklist_queue_timeout_minutes",
            field=models.PositiveIntegerField(
                default=120,
                help_text="Completed and failed checklist jobs disappear from each user's queue after this many minutes.",
                verbose_name="checklist queue timeout in minutes",
            ),
        ),
        migrations.CreateModel(
            name="ChecklistJob",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("input_filename", models.CharField(max_length=255)),
                ("output_filename", models.CharField(blank=True, max_length=255)),
                ("concept_note", models.FileField(upload_to="checklist_jobs/concept_notes/")),
                ("generated_pdf", models.FileField(blank=True, upload_to="checklist_jobs/pdfs/")),
                (
                    "status",
                    models.CharField(
                        choices=[("processing", "Processing"), ("done", "Done"), ("error", "Error")],
                        default="processing",
                        max_length=20,
                    ),
                ),
                ("error_message", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("expires_at", models.DateTimeField()),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="checklist_jobs",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "ordering": ["-created_at"],
            },
        ),
    ]
