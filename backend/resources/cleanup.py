from django.conf import settings
from django.utils import timezone

from .audit import audit_event
from .models import ChecklistJob


def delete_expired_checklist_jobs(batch_size=None):
    batch_size = batch_size or settings.CHECKLIST_JOB_CLEANUP_BATCH_SIZE
    jobs = list(ChecklistJob.objects.filter(expires_at__lte=timezone.now())[:batch_size])
    deleted = 0
    for job in jobs:
        for field in (job.concept_note, job.generated_pdf):
            if field:
                field.delete(save=False)
        audit_event("checklist_job_deleted", user=job.user, job_id=job.public_id)
        job.delete()
        deleted += 1
    return deleted
