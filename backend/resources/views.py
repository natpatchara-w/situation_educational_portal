import json
from pathlib import Path

from django.contrib.auth import authenticate, login, logout
from django.core.files.base import ContentFile
from django.db.models import Q
from django.http import FileResponse, Http404, HttpResponse, JsonResponse
from django.utils import timezone
from django.utils.text import get_valid_filename
from django.views.decorators.csrf import csrf_protect, ensure_csrf_cookie
from django.views.decorators.http import require_GET, require_POST

from .checklist_generator import (
    ChecklistGenerationError,
    InvalidConceptNoteError,
    OpenAIConfigurationError,
    extract_docx_text,
    generate_checklist_payload,
    render_checklist_pdf,
)
from .models import ChecklistJob, OpenAISettings, Resource


CONTENT_TYPES = {
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".pdf": "application/pdf",
}


def api_login_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({"detail": "Authentication required."}, status=401)
        return view_func(request, *args, **kwargs)

    return wrapper


def checklist_permission_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.has_perm("resources.can_generate_checklist"):
            return JsonResponse({"detail": "Checklist generation permission required."}, status=403)
        return view_func(request, *args, **kwargs)

    return wrapper


@ensure_csrf_cookie
@require_GET
def csrf(request):
    return JsonResponse({"detail": "CSRF cookie set."})


@require_POST
@csrf_protect
def login_view(request):
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return JsonResponse({"detail": "Invalid JSON payload."}, status=400)

    username = payload.get("username", "")
    password = payload.get("password", "")
    user = authenticate(request, username=username, password=password)

    if user is None:
        return JsonResponse({"detail": "Invalid username or password."}, status=400)

    login(request, user)
    return JsonResponse(_serialize_user(user))


@require_POST
@csrf_protect
def logout_view(request):
    logout(request)
    return JsonResponse({"detail": "Logged out."})


@require_GET
def me_view(request):
    if not request.user.is_authenticated:
        return JsonResponse({"detail": "Authentication required."}, status=401)
    return JsonResponse(_serialize_user(request.user))


@api_login_required
@require_GET
def resource_list(request):
    search = request.GET.get("search", "").strip()
    category = request.GET.get("category", "").strip()

    resources = Resource.objects.filter(is_active=True)
    if category in Resource.Category.values:
        resources = resources.filter(category=category)
    if search:
        resources = resources.filter(Q(title__icontains=search) | Q(description__icontains=search))

    return JsonResponse(
        {
            "resources": [
                {
                    "id": resource.id,
                    "title": resource.title,
                    "description": resource.description,
                    "category": resource.category,
                    "categoryLabel": resource.get_category_display(),
                    "fileType": _resource_file_type(resource),
                    "uploadedAt": resource.uploaded_at.isoformat(),
                    "downloadUrl": f"/api/resources/{resource.id}/download/",
                }
                for resource in resources
            ]
        }
    )


@api_login_required
@require_GET
def resource_download(request, resource_id):
    try:
        resource = Resource.objects.get(id=resource_id, is_active=True)
    except Resource.DoesNotExist as exc:
        raise Http404("Resource not found.") from exc

    filename = get_valid_filename(resource.pdf_file.name.rsplit("/", 1)[-1])
    content_type = CONTENT_TYPES.get(Path(filename).suffix.lower(), "application/octet-stream")
    response = FileResponse(resource.pdf_file.open("rb"), content_type=content_type)
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response


@api_login_required
@checklist_permission_required
@require_POST
@csrf_protect
def checklist_generate(request):
    concept_note = request.FILES.get("concept_note")
    if concept_note is None:
        return JsonResponse({"detail": "Upload a DOCX Event Concept Note."}, status=400)

    try:
        concept_note_text = extract_docx_text(concept_note)
        settings = OpenAISettings.get_solo()
        payload = generate_checklist_payload(concept_note_text, settings.api_key.strip())
        pdf = render_checklist_pdf(payload)
    except InvalidConceptNoteError as exc:
        return JsonResponse({"detail": str(exc)}, status=400)
    except OpenAIConfigurationError as exc:
        return JsonResponse({"detail": str(exc)}, status=503)
    except ChecklistGenerationError as exc:
        return JsonResponse({"detail": str(exc)}, status=502)

    filename = get_valid_filename(f"{payload['event_title'][:80]} checklist.pdf") or "volunteer-checklist.pdf"
    response = HttpResponse(pdf, content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response


@api_login_required
@checklist_permission_required
@require_GET
def checklist_job_list(request):
    jobs = ChecklistJob.objects.filter(user=request.user, expires_at__gt=timezone.now())
    return JsonResponse({"jobs": [_serialize_checklist_job(job) for job in jobs]})


@api_login_required
@checklist_permission_required
@require_POST
@csrf_protect
def checklist_job_create(request):
    concept_note = request.FILES.get("concept_note")
    if concept_note is None:
        return JsonResponse({"detail": "Upload a DOCX Event Concept Note."}, status=400)

    settings = OpenAISettings.get_solo()
    expires_at = timezone.now() + timezone.timedelta(minutes=settings.checklist_queue_timeout_minutes)
    job = ChecklistJob.objects.create(
        user=request.user,
        input_filename=get_valid_filename(concept_note.name) or "concept-note.docx",
        concept_note=concept_note,
        expires_at=expires_at,
    )

    try:
        with job.concept_note.open("rb") as uploaded_file:
            concept_note_text = extract_docx_text(uploaded_file)
        payload = generate_checklist_payload(concept_note_text, settings.api_key.strip())
        pdf = render_checklist_pdf(payload)
    except InvalidConceptNoteError as exc:
        job.status = ChecklistJob.Status.ERROR
        job.error_message = str(exc)
        job.save(update_fields=["status", "error_message", "updated_at"])
        return JsonResponse({"job": _serialize_checklist_job(job)}, status=400)
    except OpenAIConfigurationError as exc:
        job.status = ChecklistJob.Status.ERROR
        job.error_message = str(exc)
        job.save(update_fields=["status", "error_message", "updated_at"])
        return JsonResponse({"job": _serialize_checklist_job(job)}, status=503)
    except ChecklistGenerationError as exc:
        job.status = ChecklistJob.Status.ERROR
        job.error_message = str(exc)
        job.save(update_fields=["status", "error_message", "updated_at"])
        return JsonResponse({"job": _serialize_checklist_job(job)}, status=502)

    filename = get_valid_filename(f"{payload['event_title'][:80]} checklist.pdf") or "volunteer-checklist.pdf"
    job.output_filename = filename
    job.generated_pdf.save(filename, ContentFile(pdf), save=False)
    job.status = ChecklistJob.Status.DONE
    job.error_message = ""
    job.save(update_fields=["output_filename", "generated_pdf", "status", "error_message", "updated_at"])
    return JsonResponse({"job": _serialize_checklist_job(job)})


@api_login_required
@checklist_permission_required
@require_GET
def checklist_job_preview(request, job_id):
    job = _get_current_checklist_job(request.user, job_id)
    if job.status != ChecklistJob.Status.DONE or not job.generated_pdf:
        return JsonResponse({"detail": "Checklist PDF is not ready."}, status=409)

    response = FileResponse(job.generated_pdf.open("rb"), content_type="application/pdf")
    response["Content-Disposition"] = f'inline; filename="{get_valid_filename(job.output_filename)}"'
    return response


@api_login_required
@checklist_permission_required
@require_GET
def checklist_job_download(request, job_id):
    job = _get_current_checklist_job(request.user, job_id)
    if job.status != ChecklistJob.Status.DONE or not job.generated_pdf:
        return JsonResponse({"detail": "Checklist PDF is not ready."}, status=409)

    response = FileResponse(job.generated_pdf.open("rb"), content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="{get_valid_filename(job.output_filename)}"'
    return response


def _serialize_user(user):
    return {
        "id": user.id,
        "username": user.get_username(),
        "isStaff": user.is_staff,
        "canGenerateChecklist": user.has_perm("resources.can_generate_checklist"),
    }


def _serialize_checklist_job(job):
    return {
        "id": job.id,
        "inputFilename": job.input_filename,
        "outputFilename": job.output_filename or "volunteer-checklist.pdf",
        "status": job.status,
        "error": job.error_message,
        "createdAt": job.created_at.isoformat(),
        "updatedAt": job.updated_at.isoformat(),
        "expiresAt": job.expires_at.isoformat(),
        "previewUrl": f"/api/checklists/jobs/{job.id}/preview/" if job.status == ChecklistJob.Status.DONE else "",
        "downloadUrl": f"/api/checklists/jobs/{job.id}/download/" if job.status == ChecklistJob.Status.DONE else "",
    }


def _get_current_checklist_job(user, job_id):
    try:
        return ChecklistJob.objects.get(id=job_id, user=user, expires_at__gt=timezone.now())
    except ChecklistJob.DoesNotExist as exc:
        raise Http404("Checklist job not found.") from exc


def _resource_file_type(resource):
    extension = Path(resource.pdf_file.name).suffix.lower()
    if extension == ".docx":
        return "DOCX"
    if extension == ".pdf":
        return "PDF"
    return extension.lstrip(".").upper() or "FILE"
