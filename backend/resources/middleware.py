from django.conf import settings
from django.http import HttpResponse
from urllib.parse import urlparse


class LocalDevCorsMiddleware:
    """Allow the Vite dev server to use cookie-based Django sessions."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.method == "OPTIONS":
            response = HttpResponse()
        else:
            response = self.get_response(request)

        origin = request.headers.get("Origin")
        if _is_allowed_origin(origin):
            response["Access-Control-Allow-Origin"] = origin
            response["Access-Control-Allow-Credentials"] = "true"
            response["Access-Control-Allow-Headers"] = "Authorization, Content-Type, X-CSRFToken"
            response["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
            response["Access-Control-Expose-Headers"] = "Content-Disposition"
        return response


def _is_allowed_origin(origin):
    if not origin:
        return False
    if origin in settings.FRONTEND_ORIGINS:
        return True

    hostname = urlparse(origin).hostname or ""
    return any(hostname.endswith(suffix) for suffix in settings.CORS_ALLOWED_ORIGIN_SUFFIXES)
