from django.contrib import admin
from django import forms

from .audit import audit_event
from .models import ChatSource, ChecklistJob, OpenAISettings, Resource


@admin.register(Resource)
class ResourceAdmin(admin.ModelAdmin):
    list_display = ("title", "category", "access_level", "is_active", "uploaded_at")
    list_filter = ("category", "access_level", "is_active", "uploaded_at")
    search_fields = ("title", "description")
    readonly_fields = ("uploaded_at",)

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        audit_event(
            "admin_resource_saved",
            request=request,
            resource_id=obj.public_id,
            resource_title=obj.title,
            changed=change,
        )


class OpenAISettingsForm(forms.ModelForm):
    api_key = forms.CharField(
        label="OpenAI API key",
        required=False,
        widget=forms.PasswordInput(render_value=False),
        help_text="Leave blank to keep the currently stored encrypted key.",
    )

    class Meta:
        model = OpenAISettings
        fields = ("api_key", "checklist_queue_timeout_minutes")

    def save(self, commit=True):
        instance = super().save(commit=False)
        submitted_key = self.cleaned_data.get("api_key", "").strip()
        if submitted_key:
            instance.api_key = submitted_key
        elif instance.pk:
            instance.api_key = OpenAISettings.objects.get(pk=instance.pk).api_key
        if commit:
            instance.save()
            self.save_m2m()
        return instance


@admin.register(OpenAISettings)
class OpenAISettingsAdmin(admin.ModelAdmin):
    form = OpenAISettingsForm
    fields = ("api_key", "checklist_queue_timeout_minutes", "updated_at")
    readonly_fields = ("updated_at",)

    def has_add_permission(self, request):
        return not OpenAISettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        audit_event("admin_openai_settings_saved", request=request, changed=change)


@admin.register(ChatSource)
class ChatSourceAdmin(admin.ModelAdmin):
    list_display = ("title", "url", "is_active", "created_by", "updated_at")
    list_filter = ("is_active", "created_at", "updated_at")
    search_fields = ("title", "url")
    readonly_fields = ("public_id", "created_at", "updated_at")

    def save_model(self, request, obj, form, change):
        if not obj.created_by_id:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
        audit_event(
            "admin_chat_source_saved",
            request=request,
            source_id=obj.public_id,
            source_url=obj.url,
            changed=change,
        )


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
