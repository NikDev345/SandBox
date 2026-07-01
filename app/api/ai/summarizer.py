from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.engine import get_db
from app.utils.auth import get_current_user
from app.schemas.ai.summarizer import (
    SummarizeRequest,
    SummarizeResponse,
)
from app.services.ai.summarizer_service import SummarizerService

router = APIRouter(
    prefix="/summarizer",
    tags=["AI - Text Summarizer"],
)


@router.post(
    "/generate",
    response_model=SummarizeResponse,
)
def generate_summary(
    request: SummarizeRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Generate AI summary.
    """

    try:
        summary = SummarizerService.summarize(
            db=db,
            user_id=current_user["sub"],
            text=request.text,
            length=request.length,
        )

        return SummarizeResponse(
            summary=summary
        )

    except Exception as e:
        print("Summarizer Error:", repr(e))
        raise