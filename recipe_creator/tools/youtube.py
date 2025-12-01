"""YouTube transcript tool for Recipe Agent."""

import re

from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import NoTranscriptFound, TranscriptsDisabled


def extract_video_id(url_or_id: str) -> str | None:
    """Extract YouTube video ID from URL or return as-is if already an ID."""
    if not url_or_id or not url_or_id.strip():
        return None

    url_or_id = url_or_id.strip()
    patterns = [
        r"(?:youtube\.com\/watch\?v=)([^&\s]+)",
        r"(?:youtu\.be\/)([^\?\s]+)",
        r"(?:youtube\.com\/embed\/)([^\?\s]+)",
    ]
    for pattern in patterns:
        if match := re.search(pattern, url_or_id):
            return match.group(1)
    return url_or_id  # Assume it's already a video ID


def get_youtube_transcript(video_url_or_id: str) -> str:
    """Get the transcript from a YouTube video to extract recipe information.

    Use this tool when a user wants to get a recipe from a specific YouTube video,
    or when you need to analyze cooking tutorial content.

    Args:
        video_url_or_id: YouTube video URL (any format) or video ID

    Returns:
        Full transcript text from the video, or error message if unavailable
    """
    video_id = extract_video_id(video_url_or_id)
    if not video_id:
        return "Error: No valid video URL or ID provided."

    try:
        ytt_api = YouTubeTranscriptApi()
        transcript = ytt_api.fetch(video_id)
        full_text = " ".join([entry.text for entry in transcript])
        return f"Transcript for video {video_id}:\n\n{full_text}"
    except (TranscriptsDisabled, NoTranscriptFound):
        return f"No transcript available for video {video_id}. Try searching for a similar recipe instead."
    except Exception as e:
        return f"Error retrieving transcript for video {video_id}: {e}"

