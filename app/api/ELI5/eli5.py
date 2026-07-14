"""
ELI5 API
--------
Handles HTTP endpoints for the ELI5 (Explain Like I'm Five) tool.

Responsibilities:
- Authenticate users
- Validate incoming requests
- Delegate business logic to the service layer
- Return structured responses

No AI logic or prompt engineering should exist in this file.
"""

from fastapi import APIRouter, Depends, HTTPException, status

from app.models.eli5 import ELI5Request, ELI5Response
from app.services.ELI5.eli5_services import ELI5Service
from app.utils.auth import get_current_user
from app.models.user import Users

router = APIRouter(
    prefix="/eli5",
    tags=["ELI5"],
)


@router.post(
    "/explain",
    response_model=ELI5Response,
    status_code=status.HTTP_200_OK,
    summary="Generate an ELI5 explanation",
)
async def explain_topic(
    request: ELI5Request,
    current_user: Users = Depends(get_current_user),
) -> ELI5Response:
    """
    Generate a beginner-friendly explanation for a topic.

    The endpoint authenticates the user, validates the request,
    delegates processing to the ELI5 service, and returns the
    formatted explanation.
    """
    try:
        service = ELI5Service()

        response = await service.generate_explanation(
            request=request,
            user=current_user,
        )

        return response

    except HTTPException:
        raise

    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate explanation: {str(exc)}",
        )