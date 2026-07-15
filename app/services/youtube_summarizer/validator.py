from urllib.parse import parse_qs, urlparse

from app.models.youtube_summarizer import YouTubeSummaryRequest


class YouTubeSummaryValidator:
    """
    Validates YouTube Summary requests.
    """

    SUPPORTED_DOMAINS = {
        "youtube.com",
        "www.youtube.com",
        "m.youtube.com",
        "youtu.be",
        "www.youtu.be",
    }

    @classmethod
    def validate(
        cls,
        request: YouTubeSummaryRequest,
    ) -> None:
        """
        Validate the incoming request.

        Raises:
            ValueError
        """

        youtube_url = str(request.youtube_url).strip()

        if not youtube_url:
            raise ValueError("YouTube URL is required.")

        video_id = cls.extract_video_id(youtube_url)

        if not video_id:
            raise ValueError("Invalid YouTube URL.")

    @classmethod
    def extract_video_id(
        cls,
        youtube_url: str,
    ) -> str:
        """
        Extracts the YouTube Video ID.

        Supports

        https://www.youtube.com/watch?v=...

        https://youtu.be/...

        https://youtube.com/embed/...

        https://youtube.com/shorts/...

        Returns

        Video ID

        Raises

        ValueError
        """

        parsed = urlparse(youtube_url)

        if parsed.netloc.lower() not in cls.SUPPORTED_DOMAINS:
            raise ValueError("Unsupported YouTube domain.")

        # youtube.com/watch?v=...
        if parsed.path == "/watch":
            video_id = parse_qs(parsed.query).get("v", [None])[0]

        # youtu.be/VIDEO_ID
        elif parsed.netloc.lower().endswith("youtu.be"):
            video_id = parsed.path.lstrip("/")

        # youtube.com/embed/VIDEO_ID
        elif parsed.path.startswith("/embed/"):
            video_id = parsed.path.split("/")[2]

        # youtube.com/shorts/VIDEO_ID
        elif parsed.path.startswith("/shorts/"):
            video_id = parsed.path.split("/")[2]

        else:
            raise ValueError("Unsupported YouTube URL format.")

        if not video_id:
            raise ValueError("Unable to extract video ID.")

        if len(video_id) != 11:
            raise ValueError("Invalid YouTube video ID.")

        return video_id