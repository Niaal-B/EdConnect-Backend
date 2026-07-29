from django.test import TestCase

# Create your tests here.
from django.test import SimpleTestCase
from rest_framework import serializers

from .serializers import GenerateNotesSerializer
from .services import InvalidYouTubeURLError, YouTubeTranscriptService


class YouTubeTranscriptServiceTests(SimpleTestCase):
    def test_extract_video_id_accepts_supported_youtube_urls(self):
        supported_urls = {
            "https://youtu.be/abcDEF123_4": "abcDEF123_4",
            "https://www.youtube.com/watch?v=abcDEF123_4": "abcDEF123_4",
            "https://m.youtube.com/watch?v=abcDEF123_4&feature=youtu.be": "abcDEF123_4",
            "https://www.youtube.com/embed/abcDEF123_4": "abcDEF123_4",
            "https://www.youtube.com/shorts/abcDEF123_4": "abcDEF123_4",
            "https://www.youtube-nocookie.com/embed/abcDEF123_4": "abcDEF123_4",
        }

        for youtube_url, expected_video_id in supported_urls.items():
            with self.subTest(youtube_url=youtube_url):
                self.assertEqual(
                    YouTubeTranscriptService.extract_video_id(youtube_url),
                    expected_video_id,
                )

    def test_extract_video_id_rejects_non_youtube_urls(self):
        with self.assertRaises(InvalidYouTubeURLError):
            YouTubeTranscriptService.extract_video_id("https://example.com/watch?v=abcDEF123_4")

    def test_generate_serializer_returns_friendly_invalid_url_error(self):
        serializer = GenerateNotesSerializer(data={"youtube_url": "https://example.com/video"})

        with self.assertRaises(serializers.ValidationError):
            serializer.is_valid(raise_exception=True)
