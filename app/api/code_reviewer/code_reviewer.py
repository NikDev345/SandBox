from typing import Optional

from fastapi import APIRouter, Depends, File, Form, UploadFile

from app.utils.auth import get_current_user
from app.models.code_reviewer import (
    CodeReviewRequest,
    CodeReviewResponse,
    ProgrammingLanguage,
    ReviewInputType
)
from app.models.user import Users
from app.services.code_reviewer.code_review_service import CodeReview

router = APIRouter(prefix="/code-review", tags=["Tools"])


@router.post(
    "/review",
    response_model=CodeReviewResponse,
    summary="AI Code Reviewer",
)   
async def code_review(
    language: ProgrammingLanguage = Form(ProgrammingLanguage.AUTO),
    code: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
    current_user: Users = Depends(get_current_user),
):
    input_type = ReviewInputType.FILE if file is not None else ReviewInputType.SNIPPET
    request = CodeReviewRequest(
        input_type=input_type,
        language=language,
        code=code,
    )

    return await CodeReview.generate_review(
        request=request,
        uploaded_file=file,
    )