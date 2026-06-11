from django.conf import settings
from django.http import HttpResponse

from .throttling import client_ip, is_throttled, throttle_key


class ConfiguredCorsMiddleware:
    """Allow exact configured frontend origins to use cookie-based Django sessions."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.method == "OPTIONS":
            response = HttpResponse()
        else:
            response = self.get_response(request)

        origin = request.headers.get("Origin")
        if origin in settings.FRONTEND_ORIGINS:
            response["Access-Control-Allow-Origin"] = origin
            response["Access-Control-Allow-Credentials"] = "true"
            response["Access-Control-Allow-Headers"] = "Content-Type, X-CSRFToken"
            response["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
            response["Access-Control-Expose-Headers"] = "Content-Disposition"
            response["Vary"] = "Origin"
        return response


class DatabaseLoginThrottleMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.method == "POST" and request.path == "/admin/login/":
            key_hash = throttle_key(client_ip(request), request.POST.get("username", ""))
            if is_throttled(
                "admin_login",
                key_hash,
                settings.ADMIN_LOGIN_THROTTLE_LIMIT,
                settings.ADMIN_LOGIN_THROTTLE_WINDOW_SECONDS,
            ):
                return HttpResponse("Too many login attempts.", status=429)
        return self.get_response(request)
