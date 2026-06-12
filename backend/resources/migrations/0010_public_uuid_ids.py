import uuid

from django.db import migrations, models


def populate_public_ids(apps, schema_editor):
    for model_name in ("Resource", "ChecklistJob"):
        model = apps.get_model("resources", model_name)
        for item in model.objects.filter(public_id__isnull=True):
            item.public_id = uuid.uuid4()
            item.save(update_fields=["public_id"])


class Migration(migrations.Migration):
    dependencies = [
        ("resources", "0009_throttlerecord"),
    ]

    operations = [
        migrations.AddField(
            model_name="resource",
            name="public_id",
            field=models.UUIDField(default=uuid.uuid4, editable=False, null=True),
        ),
        migrations.AddField(
            model_name="checklistjob",
            name="public_id",
            field=models.UUIDField(default=uuid.uuid4, editable=False, null=True),
        ),
        migrations.RunPython(populate_public_ids, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="resource",
            name="public_id",
            field=models.UUIDField(default=uuid.uuid4, editable=False, unique=True),
        ),
        migrations.AlterField(
            model_name="checklistjob",
            name="public_id",
            field=models.UUIDField(default=uuid.uuid4, editable=False, unique=True),
        ),
    ]
