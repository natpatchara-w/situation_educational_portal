from django.contrib import admin

from .models import ChecklistJob, OpenAISettings, Resource


@admin.register(Resource)
class ResourceAdmin(admin.ModelAdmin):
    list_display = ("title", "category", "is_active", "uploaded_at")
    list_filter = ("category", "is_active", "uploaded_at")
    search_fields = ("title", "description")
    readonly_fields = ("uploaded_at",)


@admin.register(OpenAISettings)
class OpenAISettingsAdmin(admin.ModelAdmin):
    fields = ("api_key", "checklist_queue_timeout_minutes", "updated_at")
    readonly_fields = ("updated_at",)

    def has_add_permission(self, request):
        return not OpenAISettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(ChecklistJob)
class ChecklistJobAdmin(admin.ModelAdmin):
    list_display = ("input_filename", "user", "status", "created_at", "expires_at")
    list_filter = ("status", "created_at", "expires_at")
    search_fields = ("input_filename", "output_filename", "user__username")
    readonly_fields = (
        "user",
        "input_filename",
        "output_filename",
        "concept_note",
        "generated_pdf",
        "status",
        "error_message",
        "created_at",
        "updated_at",
        "expires_at",
    )
