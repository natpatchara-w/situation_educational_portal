from django.db import migrations

import resources.fields


def encrypt_existing_keys(apps, schema_editor):
    OpenAISettings = apps.get_model("resources", "OpenAISettings")
    for openai_settings in OpenAISettings.objects.exclude(api_key=""):
        openai_settings.api_key = openai_settings.api_key
        openai_settings.save(update_fields=["api_key"])


class Migration(migrations.Migration):
    dependencies = [
        ("resources", "0005_checklistjob_permission"),
    ]

    operations = [
        migrations.AlterField(
            model_name="openaisettings",
            name="api_key",
            field=resources.fields.EncryptedTextField(blank=True, verbose_name="OpenAI API key"),
        ),
        migrations.RunPython(encrypt_existing_keys, migrations.RunPython.noop),
    ]
