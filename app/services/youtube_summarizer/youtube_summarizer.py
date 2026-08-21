import time, json
from typing import Optional
from app.models.youtube_summarizer import (
    YouTubeSummaryRequest,
    YouTubeSummaryResponse,
    YouTubeSummaryLLMResponse
)
from app.services.LLM_Gateway.llm_config import gateway
from app.router_llm.gateway import LLMRequest
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
from app.services.tool_service import ToolService
from app.services.tool_executor import ExecutionService
from sqlalchemy.orm import Session

class YouTubeSummarizerService:
    """
    Service responsible for generating structured
    YouTube summaries using Gemini AI.
    """

    def __init__(self):
        self.gateway = gateway

    async def generate(
        self,
        request: YouTubeSummaryRequest,
        user_id: str,
        db: Session
    ) -> YouTubeSummaryResponse:
        """
        Generate a structured summary for a YouTube video.
        """
        from app.services.credit_service import enforce_credit_limit
        enforce_credit_limit(db, user_id)
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

            result = await self.gateway.generate(
                LLMRequest(
                    prompt=prompt,
                    tool_slug="youtube_summarizer",
                    temperature=0.1,
                    response_schema=YouTubeSummaryLLMResponse,
                    max_output_tokens=15000
                )
            )

            if not result or not result.text:
                raise RuntimeError("Empty response from LLM")
            parsed = result.text
            if isinstance(parsed, str):
                parsed = json.loads(parsed)

            if not isinstance(parsed, dict):
                raise RuntimeError("Invalid structured response from LLM")

            response = YouTubeSummaryLLMResponse(**parsed)

            # Step 6 — Calculate processing time
            processing_time = round(
                time.perf_counter() - start_time,
                2,
            )
            
            output = YouTubeSummaryFormatter.format(
                data=response,
                processing_time=processing_time,
            )
            output.key_points = list(dict.fromkeys(output.key_points))
            output.keywords = list(dict.fromkeys(output.keywords))
            user_output = output.model_dump_json(exclude_none=True)
            
            tool = ToolService.get_tool_by_slug(
                    db=db,
                    slug="youtube_summarizer",
                )
            tool_id = tool.id if tool else "youtube_summarizer"
            execution_id: Optional[str] = None
            try:
                execution = ExecutionService.create_execution(
                    db=db,
                    user_id=user_id,
                    tool_id=tool_id,
                    user_input=request.model_dump_json(),
                    output=user_output,
                )
                execution_id = execution.id
            except Exception:
                pass

            # Step 7 — Format response
            output.execution_id = execution_id
            return output

        except ValueError:
            raise

        except RuntimeError:
            raise

        except Exception as e:
            raise RuntimeError(
                f"YouTube summarization failed: {e}"
            ) from e