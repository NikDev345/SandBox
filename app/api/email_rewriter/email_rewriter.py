"""
AI Email Studio API

Responsibilities
----------------
- Expose REST endpoints.
- Authenticate users.
- Delegate requests to the service layer.
- Return structured responses.

No AI logic.
No prompt building.
No validation.
"""

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)

from app.models.email_rewriter import (
    EmailStudioRequest,
    EmailStudioResponse,
)

from app.services.email_rewriter.email_rewriter import (
    EmailStudioService,
)

from app.utils.auth import (
    get_current_user,
)


router = APIRouter(
    prefix="/email-rewriter",
    tags=["AI Email Studio"],
)


@router.post(
    "/generate",
    response_model=EmailStudioResponse,
    summary="Generate or Rewrite an Email using AI",
)
async def generate_email(
    request: EmailStudioRequest,
    current_user=Depends(get_current_user),
):
    """
    AI Email Studio Endpoint

    Modes

    • rewrite
    • generate

    Authentication

    JWT Protected
    """

    try:

        return await EmailStudioService.generate(
            request
        )

    except ValueError as exc:

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    except HTTPException:
        raise

    except RuntimeError as exc:

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc

    except Exception as exc:

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process email request.",
        ) from exc
