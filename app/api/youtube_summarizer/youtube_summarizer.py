from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
)
from sqlalchemy.orm import Session
from app.database.engine import get_db
from app.utils.auth import get_current_user
from app.models.youtube_summarizer import (
    YouTubeSummaryRequest,
    YouTubeSummaryResponse,
)
from app.services.youtube_summarizer.youtube_summarizer import (
    YouTubeSummarizerService,
)

router = APIRouter(
    prefix="/youtube-summarizer",
    tags=["YouTube Summarizer"],
)

youtube_summarizer_service = YouTubeSummarizerService()

@router.post(
    "/generate",
    response_model=YouTubeSummaryResponse,
)
async def generate_summary(
    request: YouTubeSummaryRequest,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Generate a structured summary for a YouTube video.
    """

    try:

        return await youtube_summarizer_service.generate(
            request=request,
            user_id=current_user['sub'],
            db=db,
        )
        
    except HTTPException as e:
        raise e

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e),
        )

    except RuntimeError as e:
        raise HTTPException(
            status_code=500,
            detail=str(e),
        )

    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Internal server error.",
        )