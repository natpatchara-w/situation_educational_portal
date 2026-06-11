import django.core.validators
from django.db import migrations, models

import resources.models


class Migration(migrations.Migration):

    dependencies = [
        ("resources", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="resource",
            name="pdf_file",
            field=models.FileField(
                upload_to="resources/files/",
                validators=[
                    django.core.validators.FileExtensionValidator(["pdf", "docx"]),
                    resources.models.validate_resource_file,
                ],
                verbose_name="resource file",
            ),
        ),
    ]
