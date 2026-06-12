from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("resources", "0012_chatsource"),
    ]

    operations = [
        migrations.AddField(
            model_name="checklistjob",
            name="language",
            field=models.CharField(
                choices=[("en", "English"), ("id", "Indonesian")],
                default="en",
                max_length=2,
            ),
        ),
    ]
