import json
from pathlib import Path

from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.db.models import Q
from django.http import FileResponse, Http404, JsonResponse
from django.utils import timezone
from django.utils.text import get_valid_filename
from django.views.decorators.csrf import csrf_protect, ensure_csrf_cookie
from django.views.decorators.http import require_GET, require_POST

from .audit import audit_event
from .education_chat import (
    EducationChatConfigurationError,
    EducationChatError,
    EducationChatProviderError,
    answer_volunteer_question,
    is_public_website_url,
)
from .models import ChatSource, ChecklistJob, OpenAISettings, Resource
from .tasks import generate_checklist_job
from .throttling import client_ip, is_throttled, reset_throttle, throttle_key


CONTENT_TYPES = {
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".pdf": "application/pdf",
}
SUPPORTED_LANGUAGES = {choice.value for choice in ChecklistJob.Language}


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


def staff_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_staff:
            return JsonResponse({"detail": "Staff permission required."}, status=403)
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
    key_hash = throttle_key(client_ip(request), username)
    if is_throttled("api_login", key_hash, settings.LOGIN_THROTTLE_LIMIT, settings.LOGIN_THROTTLE_WINDOW_SECONDS):
        audit_event("api_login_throttled", request=request, username=username)
        return JsonResponse({"detail": "Too many login attempts. Try again later."}, status=429)

    user = authenticate(request, username=username, password=password)

    if user is None:
        audit_event("api_login_failed", request=request, username=username)
        return JsonResponse({"detail": "Invalid username or password."}, status=400)

    reset_throttle("api_login", key_hash)
    login(request, user)
    audit_event("api_login_success", request=request, user=user)
    return JsonResponse(_serialize_user(user))


@require_POST
@csrf_protect
def logout_view(request):
    audit_event("api_logout", request=request)
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
    if len(search) > settings.RESOURCE_SEARCH_MAX_LENGTH:
        return JsonResponse({"detail": "Search is too long."}, status=400)

    resources = _visible_resources_for_user(request.user).filter(is_active=True)
    if category in Resource.Category.values:
        resources = resources.filter(category=category)
    if search:
        resources = resources.filter(Q(title__icontains=search) | Q(description__icontains=search))

    return JsonResponse(
        {
            "resources": [
                {
                    "id": str(resource.public_id),
                    "title": resource.title,
                    "description": resource.description,
                    "category": resource.category,
                    "categoryLabel": resource.get_category_display(),
                    "fileType": _resource_file_type(resource),
                    "uploadedAt": resource.uploaded_at.isoformat(),
                    "downloadUrl": f"/api/resources/{resource.public_id}/download/",
                }
                for resource in resources
            ]
        }
    )


@api_login_required
@require_GET
def resource_download(request, resource_id):
    try:
        resource = _visible_resources_for_user(request.user).get(public_id=resource_id, is_active=True)
    except Resource.DoesNotExist as exc:
        raise Http404("Resource not found.") from exc

    audit_event("resource_download", request=request, resource_id=resource.public_id, resource_title=resource.title)
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
    return JsonResponse({"detail": "Use /api/checklists/jobs/create/ for queued checklist generation."}, status=410)


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
    if not settings.AI_CHECKLIST_GENERATION_ENABLED:
        return JsonResponse({"detail": "AI checklist generation is disabled."}, status=503)
    if request.POST.get("ai_processing_acknowledged", "").strip().lower() not in {"1", "true", "yes", "on"}:
        return JsonResponse({"detail": "AI processing acknowledgement is required."}, status=400)

    key_hash = throttle_key(request.user.pk)
    if is_throttled(
        "checklist_job_create",
        key_hash,
        settings.CHECKLIST_JOB_THROTTLE_LIMIT,
        settings.CHECKLIST_JOB_THROTTLE_WINDOW_SECONDS,
    ):
        return JsonResponse({"detail": "Checklist generation limit reached. Try again later."}, status=429)

    concept_note = request.FILES.get("concept_note")
    if concept_note is None:
        return JsonResponse({"detail": "Upload a DOCX Event Concept Note."}, status=400)
    language = _request_language(request.POST.get("language"))
    if language is None:
        return JsonResponse({"detail": "Unsupported language."}, status=400)

    openai_settings = OpenAISettings.get_solo()
    expires_at = timezone.now() + timezone.timedelta(minutes=openai_settings.checklist_queue_timeout_minutes)
    job = ChecklistJob.objects.create(
        user=request.user,
        input_filename=get_valid_filename(concept_note.name) or "concept-note.docx",
        concept_note=concept_note,
        language=language,
        expires_at=expires_at,
    )
    audit_event("checklist_job_created", request=request, job_id=job.public_id, input_filename=job.input_filename)
    generate_checklist_job.delay(job.id)
    job.refresh_from_db()
    return JsonResponse({"job": _serialize_checklist_job(job)}, status=202)


@api_login_required
@checklist_permission_required
@require_GET
def checklist_job_preview(request, job_id):
    job = _get_current_checklist_job(request.user, job_id)
    if job.status != ChecklistJob.Status.DONE or not job.generated_pdf:
        return JsonResponse({"detail": "Checklist PDF is not ready."}, status=409)

    audit_event("checklist_job_preview", request=request, job_id=job.public_id)
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

    audit_event("checklist_job_download", request=request, job_id=job.public_id)
    response = FileResponse(job.generated_pdf.open("rb"), content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="{get_valid_filename(job.output_filename)}"'
    return response


@api_login_required
@require_POST
@csrf_protect
def chat_reply(request):
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return JsonResponse({"detail": "Invalid JSON payload."}, status=400)

    message = str(payload.get("message", "")).strip()
    if not message:
        return JsonResponse({"detail": "Enter a question for the education chat."}, status=400)
    if len(message) > settings.CHAT_MAX_MESSAGE_CHARS:
        return JsonResponse({"detail": "Chat message is too long."}, status=400)
    language = _request_language(payload.get("language"))
    if language is None:
        return JsonResponse({"detail": "Unsupported language."}, status=400)

    openai_settings = OpenAISettings.get_solo()
    try:
        result = answer_volunteer_question(
            user=request.user,
            question=message,
            history=payload.get("history", []),
            api_key=openai_settings.api_key.strip(),
            language=language,
        )
    except EducationChatConfigurationError as exc:
        return JsonResponse({"detail": str(exc)}, status=503)
    except EducationChatProviderError as exc:
        return JsonResponse({"detail": str(exc)}, status=503)
    except EducationChatError as exc:
        return JsonResponse({"detail": str(exc)}, status=400)

    audit_event("education_chat_reply", request=request, source_count=len(result.sources))
    return JsonResponse(
        {
            "reply": result.answer,
            "sources": result.sources,
            "provider": "OpenAI",
            "model": settings.OPENAI_CHAT_MODEL,
            "reasoningEffort": settings.OPENAI_CHAT_REASONING_EFFORT,
        }
    )


@api_login_required
@staff_required
@require_GET
def chat_source_list(request):
    return JsonResponse({"sources": [_serialize_chat_source(source) for source in ChatSource.objects.all()]})


@api_login_required
@staff_required
@require_POST
@csrf_protect
def chat_source_create(request):
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return JsonResponse({"detail": "Invalid JSON payload."}, status=400)

    title = str(payload.get("title", "")).strip()[:180]
    url = str(payload.get("url", "")).strip()
    if not is_public_website_url(url):
        return JsonResponse({"detail": "Enter a public http or https website URL."}, status=400)

    source = ChatSource(title=title, url=url, created_by=request.user)
    try:
        source.full_clean()
        source.save()
    except ValidationError as exc:
        return JsonResponse({"detail": _validation_message(exc)}, status=400)
    except IntegrityError:
        return JsonResponse({"detail": "This website is already in chat settings."}, status=400)

    audit_event("chat_source_created", request=request, source_id=source.public_id, source_url=source.url)
    return JsonResponse({"source": _serialize_chat_source(source)}, status=201)


@api_login_required
@staff_required
@require_POST
@csrf_protect
def chat_source_update(request, source_id):
    source = _get_chat_source(source_id)
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return JsonResponse({"detail": "Invalid JSON payload."}, status=400)

    if "title" in payload:
        source.title = str(payload.get("title", "")).strip()[:180]
    if "isActive" in payload:
        source.is_active = bool(payload.get("isActive"))

    try:
        source.full_clean()
        source.save(update_fields=["title", "is_active", "updated_at"])
    except ValidationError as exc:
        return JsonResponse({"detail": _validation_message(exc)}, status=400)

    audit_event("chat_source_updated", request=request, source_id=source.public_id, source_url=source.url)
    return JsonResponse({"source": _serialize_chat_source(source)})


@api_login_required
@staff_required
@require_POST
@csrf_protect
def chat_source_delete(request, source_id):
    source = _get_chat_source(source_id)
    audit_event("chat_source_deleted", request=request, source_id=source.public_id, source_url=source.url)
    source.delete()
    return JsonResponse({"detail": "Website removed."})


def _serialize_user(user):
    return {
        "id": user.id,
        "username": user.get_username(),
        "isStaff": user.is_staff,
        "canGenerateChecklist": user.has_perm("resources.can_generate_checklist"),
    }


def _serialize_checklist_job(job):
    return {
        "id": str(job.public_id),
        "inputFilename": job.input_filename,
        "outputFilename": job.output_filename or "volunteer-checklist.pdf",
        "language": job.language,
        "status": job.status,
        "error": job.error_message,
        "createdAt": job.created_at.isoformat(),
        "updatedAt": job.updated_at.isoformat(),
        "expiresAt": job.expires_at.isoformat(),
        "previewUrl": f"/api/checklists/jobs/{job.public_id}/preview/" if job.status == ChecklistJob.Status.DONE else "",
        "downloadUrl": f"/api/checklists/jobs/{job.public_id}/download/" if job.status == ChecklistJob.Status.DONE else "",
    }


def _get_current_checklist_job(user, job_id):
    try:
        return ChecklistJob.objects.get(public_id=job_id, user=user, expires_at__gt=timezone.now())
    except ChecklistJob.DoesNotExist as exc:
        raise Http404("Checklist job not found.") from exc


def _request_language(value):
    language = str(value or ChecklistJob.Language.ENGLISH).strip().lower()
    if language not in SUPPORTED_LANGUAGES:
        return None
    return language


def _visible_resources_for_user(user):
    resources = Resource.objects.all()
    if user.is_staff:
        return resources

    visibility = Q(access_level=Resource.AccessLevel.AUTHENTICATED)
    if user.has_perm("resources.can_generate_checklist"):
        visibility |= Q(access_level=Resource.AccessLevel.CHECKLIST_GENERATORS)
    return resources.filter(visibility)


def _resource_file_type(resource):
    extension = Path(resource.pdf_file.name).suffix.lower()
    if extension == ".docx":
        return "DOCX"
    if extension == ".pdf":
        return "PDF"
    return extension.lstrip(".").upper() or "FILE"


def _serialize_chat_source(source):
    return {
        "id": str(source.public_id),
        "title": source.title,
        "url": source.url,
        "isActive": source.is_active,
        "createdAt": source.created_at.isoformat(),
        "updatedAt": source.updated_at.isoformat(),
    }


def _get_chat_source(source_id):
    try:
        return ChatSource.objects.get(public_id=source_id)
    except ChatSource.DoesNotExist as exc:
        raise Http404("Website source not found.") from exc


def _validation_message(exc):
    if hasattr(exc, "message_dict"):
        for messages in exc.message_dict.values():
            if messages:
                return messages[0]
    if getattr(exc, "messages", None):
        return exc.messages[0]
    return str(exc)
