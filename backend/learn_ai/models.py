"""Database models for generated LearnAI study notes."""

from django.conf import settings
from django.db import models


class LearnAISummary(models.Model):
    """A set of AI-generated study notes created from a YouTube lecture."""

    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="learn_ai_summaries",
    )
    youtube_url = models.URLField(max_length=500)
    video_id = models.CharField(max_length=32, db_index=True)
    video_title = models.CharField(max_length=500)
    transcript = models.TextField()
    summary = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-created_at",)
        indexes = [models.Index(fields=("student", "-created_at"))]

    def __str__(self) -> str:
        return f"{self.student} — {self.video_title}"
