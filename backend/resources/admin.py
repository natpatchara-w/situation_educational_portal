from django.contrib import admin

from .models import OpenAISettings, Resource


@admin.register(Resource)
class ResourceAdmin(admin.ModelAdmin):
    list_display = ("title", "category", "is_active", "uploaded_at")
    list_filter = ("category", "is_active", "uploaded_at")
    search_fields = ("title", "description")
    readonly_fields = ("uploaded_at",)


@admin.register(OpenAISettings)
class OpenAISettingsAdmin(admin.ModelAdmin):
    fields = ("api_key", "updated_at")
    readonly_fields = ("updated_at",)

    def has_add_permission(self, request):
        return not OpenAISettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False
