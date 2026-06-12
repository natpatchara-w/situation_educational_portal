from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("resources", "0008_private_file_storage"),
    ]

    operations = [
        migrations.CreateModel(
            name="ThrottleRecord",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("scope", models.CharField(max_length=64)),
                ("key_hash", models.CharField(max_length=64)),
                ("attempts", models.PositiveIntegerField(default=0)),
                ("first_attempt_at", models.DateTimeField()),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.AddConstraint(
            model_name="throttlerecord",
            constraint=models.UniqueConstraint(fields=("scope", "key_hash"), name="unique_throttle_scope_key"),
        ),
    ]
