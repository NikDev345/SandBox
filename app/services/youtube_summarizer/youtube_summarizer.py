import time

from app.models.youtube_summarizer import (
    YouTubeSummaryRequest,
    YouTubeSummaryResponse,
)
from app.services.gemini_service import GeminiService
from app.utils.text_cleaner import TextCleaner
from app.services.youtube_summarizer.formatter import (
    YouTubeSummaryFormatter,
)
from app.services.youtube_summarizer.prompt_engine import (
    PromptEngine,
)
from app.services.youtube_summarizer.validator import (
    YouTubeSummaryValidator,
)
from app.services.youtube_summarizer.youtube_client import (
    YouTubeClient,
)


class YouTubeSummarizerService:
    """
    Service responsible for generating structured
    YouTube summaries using Gemini AI.
    """

    def __init__(self):
        self.gemini = GeminiService()

    async def generate(
        self,
        request: YouTubeSummaryRequest,
    ) -> YouTubeSummaryResponse:
        """
        Generate a structured summary for a YouTube video.
        """

        start_time = time.perf_counter()

        try:
            # Step 1 — Validate request
            YouTubeSummaryValidator.validate(request)

            # Step 2 — Fetch transcript
            _, transcript = YouTubeClient.get_transcript(
                str(request.youtube_url)
            )

            # Step 3 — Clean transcript
            cleaned_transcript = TextCleaner.clean(
                transcript
            )

            # Step 4 — Build prompt
            prompt = PromptEngine.build_prompt(
                transcript=cleaned_transcript,
                request=request,
            )

            # Step 5 — Generate AI response
            response = await self.gemini.generate_json(
                prompt=prompt
            )

            if not isinstance(response, dict):
                raise RuntimeError(
                    "Gemini returned an invalid response."
                )

            # Step 6 — Calculate processing time
            processing_time = round(
                time.perf_counter() - start_time,
                2,
            )

            # Step 7 — Format response
            return YouTubeSummaryFormatter.format(
                data=response,
                processing_time=processing_time,
            )

        except ValueError:
            raise

        except RuntimeError:
            raise

        except Exception as e:
            raise RuntimeError(
                f"YouTube summarization failed: {e}"
            ) from e