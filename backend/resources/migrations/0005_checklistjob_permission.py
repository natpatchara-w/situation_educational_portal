from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("resources", "0004_persistent_checklist_jobs"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="checklistjob",
            options={
                "ordering": ["-created_at"],
                "permissions": [("can_generate_checklist", "Can generate checklist")],
            },
        ),
    ]
