from youtube_transcript_api import (
    NoTranscriptFound,
    TranscriptsDisabled,
    YouTubeTranscriptApi,
)

from app.services.youtube_summarizer.validator import (
    YouTubeSummaryValidator,
)


class YouTubeClient:
    """
    Service responsible for retrieving YouTube transcripts.
    """

    SUPPORTED_LANGUAGES = (
        "en",
        "en-US",
        "en-GB",
    )

    _client = YouTubeTranscriptApi()

    @classmethod
    def get_transcript(
        cls,
        youtube_url: str,
    ) -> tuple[str, str]:
        """
        Fetch transcript for a YouTube video.

        Returns:
            (video_id, transcript)
        """

        video_id = YouTubeSummaryValidator.extract_video_id(
            youtube_url
        )

        try:

            transcript = cls._client.fetch(
                video_id,
                languages=cls.SUPPORTED_LANGUAGES,
            )

        except TranscriptsDisabled:
            raise ValueError(
                "Transcripts are disabled for this video."
            )

        except NoTranscriptFound:
            raise ValueError(
                "No English transcript found."
            )

        except Exception as e:
            raise RuntimeError(
                f"Failed to retrieve transcript: {e}"
            )

        text = cls._merge_transcript(transcript)

        if not text:
            raise ValueError(
                "Transcript is empty."
            )

        return video_id, text

    @staticmethod
    def _merge_transcript(
        transcript,
    ) -> str:
        """
        Merge transcript snippets into plain text.
        """

        lines = []

        for snippet in transcript:

            text = snippet.text.strip()

            if not text:
                continue

            # Remove common caption artifacts
            if text.lower() in (
                "[music]",
                "[applause]",
                "[laughter]",
            ):
                continue

            lines.append(text)

        return "\n".join(lines).strip()