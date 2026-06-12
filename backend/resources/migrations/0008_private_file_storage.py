from django.core.validators import FileExtensionValidator
from django.db import migrations, models

import resources.models
import resources.storage


class Migration(migrations.Migration):
    dependencies = [
        ("resources", "0007_checklistjob_pending_status"),
    ]

    operations = [
        migrations.AlterField(
            model_name="checklistjob",
            name="concept_note",
            field=models.FileField(
                storage=resources.storage.PrivateMediaStorage(),
                upload_to="checklist_jobs/concept_notes/",
            ),
        ),
        migrations.AlterField(
            model_name="checklistjob",
            name="generated_pdf",
            field=models.FileField(
                blank=True,
                storage=resources.storage.PrivateMediaStorage(),
                upload_to="checklist_jobs/pdfs/",
            ),
        ),
        migrations.AlterField(
            model_name="resource",
            name="pdf_file",
            field=models.FileField(
                storage=resources.storage.PrivateMediaStorage(),
                upload_to="resources/files/",
                validators=[
                    FileExtensionValidator(["pdf", "docx"]),
                    resources.models.validate_resource_file,
                ],
                verbose_name="resource file",
            ),
        ),
    ]
