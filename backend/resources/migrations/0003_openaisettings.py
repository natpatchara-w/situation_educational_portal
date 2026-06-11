from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("resources", "0002_support_docx_resource_files"),
    ]

    operations = [
        migrations.CreateModel(
            name="OpenAISettings",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("api_key", models.CharField(blank=True, max_length=255, verbose_name="OpenAI API key")),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "verbose_name": "OpenAI settings",
                "verbose_name_plural": "OpenAI settings",
            },
        ),
    ]
