import shutil
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand

from resources.models import ChecklistJob, Resource


class Command(BaseCommand):
    help = "Copy legacy files from MEDIA_ROOT into PRIVATE_MEDIA_ROOT without deleting originals."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true")

    def handle(self, *args, **options):
        copied = 0
        checked = 0
        fields = []
        fields.extend((resource.pdf_file,) for resource in Resource.objects.exclude(pdf_file=""))
        fields.extend((job.concept_note, job.generated_pdf) for job in ChecklistJob.objects.all())

        for group in fields:
            for field in group:
                if not field:
                    continue
                checked += 1
                source = Path(settings.MEDIA_ROOT) / field.name
                destination = Path(settings.PRIVATE_MEDIA_ROOT) / field.name
                if not source.exists() or destination.exists():
                    continue
                if options["dry_run"]:
                    self.stdout.write(f"Would copy {source} -> {destination}")
                    continue
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, destination)
                copied += 1

        self.stdout.write(self.style.SUCCESS(f"Checked {checked} file reference(s); copied {copied} file(s)."))
