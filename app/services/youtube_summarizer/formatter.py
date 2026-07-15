from app.models.youtube_summarizer import (
    TimelineItem,
    YouTubeSummaryResponse,
)


class YouTubeSummaryFormatter:
    """
    Converts Gemini JSON into a YouTubeSummaryResponse.
    """

    @staticmethod
    def format(
        data: dict,
        processing_time: float,
    ) -> YouTubeSummaryResponse:
        """
        Convert Gemini JSON response into a
        YouTubeSummaryResponse.
        """

        if not isinstance(data, dict):
            raise ValueError("Invalid Gemini response.")

        timeline = []

        for item in data.get("timeline", []):

            if not isinstance(item, dict):
                continue

            timeline.append(
                TimelineItem(
                    title=item.get("title", ""),
                    summary=item.get("summary", ""),
                )
            )

        return YouTubeSummaryResponse(
            success=True,
            summary=data.get("summary", ""),
            key_points=data.get("key_points", []),
            timeline=timeline,
            important_quotes=data.get(
                "important_quotes",
                [],
            ),
            action_items=data.get(
                "action_items",
                [],
            ),
            keywords=data.get(
                "keywords",
                [],
            ),
            processing_time=processing_time,
        )