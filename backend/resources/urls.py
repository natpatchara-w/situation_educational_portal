from django.urls import path

from . import views


urlpatterns = [
    path("auth/csrf/", views.csrf, name="api-csrf"),
    path("auth/login/", views.login_view, name="api-login"),
    path("auth/logout/", views.logout_view, name="api-logout"),
    path("auth/me/", views.me_view, name="api-me"),
    path("checklists/generate/", views.checklist_generate, name="api-checklist-generate"),
    path("checklists/jobs/", views.checklist_job_list, name="api-checklist-job-list"),
    path("checklists/jobs/create/", views.checklist_job_create, name="api-checklist-job-create"),
    path("checklists/jobs/<int:job_id>/preview/", views.checklist_job_preview, name="api-checklist-job-preview"),
    path("checklists/jobs/<int:job_id>/download/", views.checklist_job_download, name="api-checklist-job-download"),
    path("resources/", views.resource_list, name="api-resource-list"),
    path("resources/<int:resource_id>/download/", views.resource_download, name="api-resource-download"),
]
