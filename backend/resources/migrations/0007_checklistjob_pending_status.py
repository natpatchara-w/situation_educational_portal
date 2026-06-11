from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("resources", "0006_encrypt_openai_api_key"),
    ]

    operations = [
        migrations.AlterField(
            model_name="checklistjob",
            name="status",
            field=models.CharField(
                choices=[
                    ("pending", "Pending"),
                    ("processing", "Processing"),
                    ("done", "Done"),
                    ("error", "Error"),
                ],
                default="pending",
                max_length=20,
            ),
        ),
    ]
