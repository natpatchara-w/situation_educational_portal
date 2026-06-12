from celery import shared_task
from django.core.files.base import ContentFile
from django.utils.text import get_valid_filename

from .audit import audit_event
from .checklist_generator import (
    ChecklistGenerationError,
    InvalidConceptNoteError,
    OpenAIConfigurationError,
    extract_docx_text,
    generate_checklist_payload,
    render_checklist_pdf,
)
from .models import ChecklistJob, OpenAISettings
from .cleanup import delete_expired_checklist_jobs


@shared_task(bind=True, autoretry_for=(), ignore_result=True)
def generate_checklist_job(self, job_id):
    try:
        job = ChecklistJob.objects.get(id=job_id)
    except ChecklistJob.DoesNotExist:
        return

    job.status = ChecklistJob.Status.PROCESSING
    job.error_message = ""
    job.save(update_fields=["status", "error_message", "updated_at"])

    try:
        with job.concept_note.open("rb") as uploaded_file:
            concept_note_text = extract_docx_text(uploaded_file)
        settings = OpenAISettings.get_solo()
        payload = generate_checklist_payload(concept_note_text, settings.api_key.strip(), language=job.language)
        pdf = render_checklist_pdf(payload)
    except (InvalidConceptNoteError, OpenAIConfigurationError, ChecklistGenerationError) as exc:
        job.status = ChecklistJob.Status.ERROR
        job.error_message = str(exc)
        job.save(update_fields=["status", "error_message", "updated_at"])
        audit_event("checklist_job_failed", user=job.user, job_id=job.public_id, reason=exc.__class__.__name__)
        return

    suffix = "daftar-periksa.pdf" if job.language == ChecklistJob.Language.INDONESIAN else "checklist.pdf"
    fallback_filename = "daftar-periksa-relawan.pdf" if job.language == ChecklistJob.Language.INDONESIAN else "volunteer-checklist.pdf"
    filename = get_valid_filename(f"{payload['event_title'][:80]} {suffix}") or fallback_filename
    job.output_filename = filename
    job.generated_pdf.save(filename, ContentFile(pdf), save=False)
    job.status = ChecklistJob.Status.DONE
    job.error_message = ""
    job.save(update_fields=["output_filename", "generated_pdf", "status", "error_message", "updated_at"])
    audit_event("checklist_job_completed", user=job.user, job_id=job.public_id, output_filename=job.output_filename)


@shared_task(ignore_result=True)
def cleanup_expired_checklist_jobs():
    delete_expired_checklist_jobs()
