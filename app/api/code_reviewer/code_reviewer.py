from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.utils.auth import get_current_user
from app.database.engine import get_db
from app.models.code_reviewer import CodeReviewerRequest, CodeReviewerResponse
from app.services.code_reviewer.code_review_service import CodeReviewService
from app.services.tool_service import ToolService

router = APIRouter(
    prefix="/code-review",
    tags=["Code Review"]
)

@router.post("/review", response_model=CodeReviewerResponse)
async def code_review(data: CodeReviewerRequest, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    try:
        tool = ToolService.get_tool_by_slug(db, slug='CODE_REVIEWER')
        if not tool:
            tool_id = 'CODE_REVIEWER'
        else:
            tool_id = tool.id
            
        review = await CodeReviewService.review(db=db, 
                                                user_id=current_user['sub'], 
                                                tool_id=tool_id,
                                                input_type=data.input_type, 
                                                code=data.code, 
                                                filename=data.filename, 
                                                files=data.files, 
                                                zip_path=data.zip_path, 
                                                language=data.language)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f'Failed to review code: {str(e)}'
        )
    
    return CodeReviewerResponse(
        review=review
    )