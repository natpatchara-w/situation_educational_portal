from django.urls import path

from . import views


urlpatterns = [
    path("auth/csrf/", views.csrf, name="api-csrf"),
    path("auth/login/", views.login_view, name="api-login"),
    path("auth/logout/", views.logout_view, name="api-logout"),
    path("auth/me/", views.me_view, name="api-me"),
    path("chat/", views.chat_reply, name="api-chat-reply"),
    path("chat/sources/", views.chat_source_list, name="api-chat-source-list"),
    path("chat/sources/create/", views.chat_source_create, name="api-chat-source-create"),
    path("chat/sources/<uuid:source_id>/update/", views.chat_source_update, name="api-chat-source-update"),
    path("chat/sources/<uuid:source_id>/delete/", views.chat_source_delete, name="api-chat-source-delete"),
    path("checklists/generate/", views.checklist_generate, name="api-checklist-generate"),
    path("checklists/jobs/", views.checklist_job_list, name="api-checklist-job-list"),
    path("checklists/jobs/create/", views.checklist_job_create, name="api-checklist-job-create"),
    path("checklists/jobs/<uuid:job_id>/preview/", views.checklist_job_preview, name="api-checklist-job-preview"),
    path("checklists/jobs/<uuid:job_id>/download/", views.checklist_job_download, name="api-checklist-job-download"),
    path("resources/", views.resource_list, name="api-resource-list"),
    path("resources/<uuid:resource_id>/download/", views.resource_download, name="api-resource-download"),
]
