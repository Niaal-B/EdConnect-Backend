"""Business services for LearnAI note generation."""

import logging
import os
import re
from dataclasses import dataclass
from typing import Final

import requests
from django.contrib.auth.models import AbstractBaseUser
from django.db import transaction
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import (
    NoTranscriptFound,
    TranscriptsDisabled,
    VideoUnavailable,
    YouTubeTranscriptApiException,
)

from .models import LearnAISummary
from .prompts import build_study_notes_prompt
from .utils import get_youtube_video_title

logger = logging.getLogger(__name__)


class LearnAIError(Exception):
    """Base exception for expected LearnAI failures."""

    message = "Unable to generate notes right now. Please try again."

    def __str__(self) -> str:
        return self.message


class InvalidYouTubeURLError(LearnAIError):
    message = "Enter a valid YouTube video URL."


class TranscriptNotAvailableError(LearnAIError):
    message = "A transcript is not available for this video. It may be private, unavailable, or have captions disabled."


class AIServiceUnavailableError(LearnAIError):
    message = "The notes service is temporarily unavailable. Please try again."


class AIQuotaExceededError(LearnAIError):
    message = "Groq quota limit reached. Please try again later or check your Groq API billing and quota."


class AIResponseError(LearnAIError):
    message = "The notes service returned an invalid response. Please try again."


@dataclass(frozen=True)
class TranscriptResult:
    """Transcript data returned by the YouTube provider."""

    video_id: str
    transcript: str


class YouTubeTranscriptService:
    """Validate YouTube links and fetch their caption transcript only."""

    VIDEO_ID_PATTERN: Final[re.Pattern[str]] = re.compile(r"^[A-Za-z0-9_-]{11}$")

    @classmethod
    def extract_video_id(cls, youtube_url: str) -> str:
        """Extract a video ID from supported canonical and short YouTube URLs."""
        from urllib.parse import parse_qs, urlparse

        parsed = urlparse(youtube_url.strip())
        host = parsed.netloc.lower().removeprefix("www.").removeprefix("m.")
        video_id = ""

        if host == "youtu.be":
            video_id = parsed.path.lstrip("/").split("/")[0]
        elif host in {"youtube.com", "youtube-nocookie.com"}:
            if parsed.path == "/watch":
                video_id = parse_qs(parsed.query).get("v", [""])[0]
            elif parsed.path.startswith(("/shorts/", "/embed/", "/live/")):
                video_id = parsed.path.strip("/").split("/")[1]

        if not cls.VIDEO_ID_PATTERN.fullmatch(video_id):
            raise InvalidYouTubeURLError()
        return video_id

    def get_transcript(self, youtube_url: str) -> TranscriptResult:
        """Fetch and normalize the caption text for a valid YouTube video URL."""
        video_id = self.extract_video_id(youtube_url)
        
        # Try multiple languages with fallback
        languages = ['en', 'en-US', 'en-GB', 'hi', 'es', 'fr', 'de']
        transcript = None
        last_error = None
        
        for lang in languages:
            try:
                fetched_transcript = YouTubeTranscriptApi().fetch(video_id, languages=[lang])
                transcript = " ".join(snippet.text.strip() for snippet in fetched_transcript if snippet.text.strip())
                if transcript:
                    break
            except (
                NoTranscriptFound,
                TranscriptsDisabled,
                VideoUnavailable,
                YouTubeTranscriptApiException,
            ) as exc:
                last_error = exc
                continue
            except requests.RequestException as exc:
                last_error = exc
                continue
        
        if not transcript:
            # Try without language specification
            try:
                fetched_transcript = YouTubeTranscriptApi().fetch(video_id)
                transcript = " ".join(snippet.text.strip() for snippet in fetched_transcript if snippet.text.strip())
            except (
                NoTranscriptFound,
                TranscriptsDisabled,
                VideoUnavailable,
                YouTubeTranscriptApiException,
            ) as exc:
                logger.warning("YouTube transcript request failed for video %s", video_id, exc_info=True)
                raise TranscriptNotAvailableError() from exc
            except requests.RequestException as exc:
                logger.warning("YouTube transcript request failed for video %s", video_id, exc_info=True)
                raise TranscriptNotAvailableError() from exc

        if not transcript:
            raise TranscriptNotAvailableError()
        return TranscriptResult(video_id=video_id, transcript=transcript)


class AIStudyNotesService:
    """Generate Markdown notes through Groq without Django model knowledge."""

    API_URL: Final[str] = "https://api.groq.com/openai/v1/chat/completions"
    HTTP_TOO_MANY_REQUESTS: Final[int] = 429
    TIMEOUT_SECONDS: Final[int] = 60

    def __init__(self, api_key: str | None = None, model: str | None = None) -> None:
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        self.model = model or os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

    def generate_notes(self, transcript: str) -> str:
        """Send a transcript to Groq and return the generated Markdown."""
        if not self.api_key:
            logger.error("GROQ_API_KEY is not configured")
            raise AIServiceUnavailableError()

        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "user",
                    "content": build_study_notes_prompt(transcript),
                }
            ],
            "temperature": 0.2,
        }
        try:
            response = requests.post(
                self.API_URL,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
                timeout=self.TIMEOUT_SECONDS,
            )
            if response.status_code == self.HTTP_TOO_MANY_REQUESTS:
                logger.warning("Groq quota exceeded for model %s", self.model)
                raise AIQuotaExceededError()
            response.raise_for_status()
            data = response.json()
            summary = data["choices"][0]["message"]["content"].strip()
        except AIQuotaExceededError:
            raise
        except (requests.RequestException, ValueError, KeyError, IndexError, TypeError) as exc:
            logger.warning("Groq note generation failed", exc_info=True)
            if isinstance(exc, requests.RequestException):
                raise AIServiceUnavailableError() from exc
            raise AIResponseError() from exc

        if not summary:
            raise AIResponseError()
        return summary


class LearnAIService:
    """Orchestrate transcript extraction, AI generation, and persistence."""

    def __init__(
        self,
        transcript_service: YouTubeTranscriptService | None = None,
        ai_service: AIStudyNotesService | None = None,
    ) -> None:
        self.transcript_service = transcript_service or YouTubeTranscriptService()
        self.ai_service = ai_service or AIStudyNotesService()

    def generate_notes(self, *, student: AbstractBaseUser, youtube_url: str) -> LearnAISummary:
        """Generate and save a student's study notes for a YouTube lecture."""
        transcript_result = self.transcript_service.get_transcript(youtube_url)
        summary = self.ai_service.generate_notes(transcript_result.transcript)
        title = get_youtube_video_title(transcript_result.video_id) or f"YouTube lecture ({transcript_result.video_id})"

        with transaction.atomic():
            return LearnAISummary.objects.create(
                student=student,
                youtube_url=youtube_url,
                video_id=transcript_result.video_id,
                video_title=title,
                transcript=transcript_result.transcript,
                summary=summary,
            )
