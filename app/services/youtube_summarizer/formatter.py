from app.models.youtube_summarizer import (
    TimelineItem,
    YouTubeSummaryResponse,
    YouTubeSummaryLLMResponse
)


class YouTubeSummaryFormatter:
    """
    Converts Gemini JSON into a YouTubeSummaryResponse.
    """

    @staticmethod
    def format(
        data: YouTubeSummaryLLMResponse,
        processing_time: float,
    ) -> YouTubeSummaryResponse:
        """
        Convert Gemini JSON response into a
        YouTubeSummaryResponse.
        """

        if not isinstance(data, YouTubeSummaryLLMResponse):
            raise ValueError("Invalid Gemini response.")

        timeline = [
            TimelineItem(
                title=item.title,
                summary=item.summary,
            )
            for item in (data.timeline or [])
        ]

        return YouTubeSummaryResponse(
            success=True,
            summary=data.summary or "",
            key_points=data.key_points or [],
            timeline=timeline,
            important_quotes=data.important_quotes or [],
            action_items=data.action_items or [],
            keywords=data.keywords or [],
            processing_time=processing_time,
        )