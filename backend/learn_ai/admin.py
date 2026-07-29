"""Django admin configuration for LearnAI."""

from django.contrib import admin

from .models import LearnAISummary


@admin.register(LearnAISummary)
class LearnAISummaryAdmin(admin.ModelAdmin):
    list_display = ("id", "student", "video_title", "video_id", "created_at")
    list_filter = ("created_at",)
    search_fields = ("student__email", "student__username", "video_title", "video_id")
    readonly_fields = ("created_at", "updated_at")
