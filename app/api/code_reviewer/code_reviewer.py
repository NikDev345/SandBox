from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.utils.auth import get_current_user
from app.database.engine import get_db
from app.models.code_reviewer import CodeReviewerRequest, CodeReviewerResponse
from app.services.code_reviewer.code_review_service import CodeReviewService

router = APIRouter(
    prefix="/code-review",
    tags=["Code Review"]
)

@router.post("/review", response_model=CodeReviewerResponse)
def code_review(data: CodeReviewerRequest, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    try:
        review = CodeReviewService.review_code(db, current_user, data.code, data.language, data.review_type)
    except Exception:
        raise HTTPException(
            status_code=500,
            detail='Failed to review code'
        )
    
    return CodeReviewerResponse(
        review=review
    )