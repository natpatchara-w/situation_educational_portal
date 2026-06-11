from django.core.management.base import BaseCommand

from resources.cleanup import delete_expired_checklist_jobs


class Command(BaseCommand):
    help = "Delete expired checklist jobs and their private files."

    def add_arguments(self, parser):
        parser.add_argument("--batch-size", type=int, default=None)

    def handle(self, *args, **options):
        deleted = delete_expired_checklist_jobs(batch_size=options["batch_size"])
        self.stdout.write(self.style.SUCCESS(f"Deleted {deleted} expired checklist job(s)."))
