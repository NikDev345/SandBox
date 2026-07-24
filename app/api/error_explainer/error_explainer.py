from fastapi import APIRouter, Depends, HTTPException

from app.utils.auth import get_current_user
from app.models.user import Users
from app.models.error_explainer import (
    ErrorExplainerRequest,
    ErrorExplainerResponse,
)
from app.services.error_explainer.error_explainer import ErrorExplainer

router = APIRouter(
    prefix="/error-explainer",
    tags=["Error Explainer"],
)


@router.post(
    "/explain",
    response_model=ErrorExplainerResponse,
    summary="Explain a programming error using AI",
)
async def explain_error(
    request: ErrorExplainerRequest,
    current_user: Users = Depends(get_current_user),
):
    """
    Analyze a programming error or stack trace and return
    a human-readable explanation along with corrected code
    when applicable.
    """
    try:
        service = ErrorExplainer()
        return await service.explain_error(request)

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e),
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to explain error: {e}",
        )