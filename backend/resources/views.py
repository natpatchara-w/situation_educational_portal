import json
from pathlib import Path

from django.contrib.auth import authenticate, login, logout
from django.db.models import Q
from django.http import FileResponse, Http404, JsonResponse
from django.utils.text import get_valid_filename
from django.views.decorators.csrf import csrf_protect, ensure_csrf_cookie
from django.views.decorators.http import require_GET, require_POST

from .models import Resource


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


def _serialize_user(user):
    return {
        "id": user.id,
        "username": user.get_username(),
        "isStaff": user.is_staff,
    }


def _resource_file_type(resource):
    extension = Path(resource.pdf_file.name).suffix.lower()
    if extension == ".docx":
        return "DOCX"
    if extension == ".pdf":
        return "PDF"
    return extension.lstrip(".").upper() or "FILE"
