from django.urls import path

from . import views


urlpatterns = [
    path("auth/csrf/", views.csrf, name="api-csrf"),
    path("auth/login/", views.login_view, name="api-login"),
    path("auth/logout/", views.logout_view, name="api-logout"),
    path("auth/me/", views.me_view, name="api-me"),
    path("checklists/generate/", views.checklist_generate, name="api-checklist-generate"),
    path("resources/", views.resource_list, name="api-resource-list"),
    path("resources/<int:resource_id>/download/", views.resource_download, name="api-resource-download"),
]
