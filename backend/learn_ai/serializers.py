"""Serializers for the LearnAI API."""

from rest_framework import serializers

from .models import LearnAISummary
from .services import InvalidYouTubeURLError, YouTubeTranscriptService


class GenerateNotesSerializer(serializers.Serializer):
    """Validate a YouTube URL before initiating note generation."""

    youtube_url = serializers.URLField(max_length=500)

    def validate_youtube_url(self, value: str) -> str:
        try:
            YouTubeTranscriptService.extract_video_id(value)
        except InvalidYouTubeURLError as exc:
            raise serializers.ValidationError("Enter a valid YouTube video URL.") from exc
        return value


class LearnAISummarySerializer(serializers.ModelSerializer):
    """Serialize stored notes without exposing the raw transcript."""

    class Meta:
        model = LearnAISummary
        fields = ("id", "youtube_url", "video_id", "video_title", "summary", "created_at", "updated_at")
        read_only_fields = fields
