"""Small provider-neutral helpers for LearnAI."""

import logging

import requests

logger = logging.getLogger(__name__)


def get_youtube_video_title(video_id: str) -> str | None:
    """Return a public YouTube title using oEmbed, without failing note generation."""
    try:
        response = requests.get(
            "https://www.youtube.com/oembed",
            params={"url": f"https://www.youtube.com/watch?v={video_id}", "format": "json"},
            timeout=10,
        )
        response.raise_for_status()
        title = response.json().get("title")
        return title.strip() if isinstance(title, str) and title.strip() else None
    except (requests.RequestException, ValueError):
        logger.info("Could not retrieve YouTube title for video %s", video_id)
        return None
