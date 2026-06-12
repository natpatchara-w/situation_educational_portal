from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("resources", "0010_public_uuid_ids"),
    ]

    operations = [
        migrations.AddField(
            model_name="resource",
            name="access_level",
            field=models.CharField(
                choices=[
                    ("authenticated", "All authenticated users"),
                    ("checklist_generators", "Checklist generators"),
                    ("staff", "Staff only"),
                ],
                default="authenticated",
                max_length=24,
            ),
        ),
    ]
