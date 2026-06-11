from django.contrib import admin

from .models import Resource


@admin.register(Resource)
class ResourceAdmin(admin.ModelAdmin):
    list_display = ("title", "category", "is_active", "uploaded_at")
    list_filter = ("category", "is_active", "uploaded_at")
    search_fields = ("title", "description")
    readonly_fields = ("uploaded_at",)
