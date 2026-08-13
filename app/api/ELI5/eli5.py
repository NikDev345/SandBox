"""
ELI5 API
--------
HTTP endpoints for the Explain Like I'm Five tool.

The API layer intentionally remains lightweight.
Heavy AI/business dependencies are imported only when
the endpoint is actually used.
"""

from __future__ import annotations

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)
from sqlalchemy.orm import Session

from app.database.engine import get_db
from app.models.eli5 import ELI5Request, ELI5Response
from app.utils.auth import get_current_user


router = APIRouter(
    prefix="/eli5",
    tags=["ELI5"],
)


# ============================================================
# GENERATE ELI5 EXPLANATION
# ============================================================

@router.post(
    "/explain",
    response_model=ELI5Response,
    status_code=status.HTTP_200_OK,
    summary="Generate an ELI5 explanation",
)
async def explain_topic(
    request: ELI5Request,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ELI5Response:
    """
    Generate a beginner-friendly explanation.

    The ELI5 service is imported lazily so that importing
    the API router does not initialize the AI stack during
    application startup.
    """

    try:

        # ----------------------------------------------------
        # Lazy import
        # ----------------------------------------------------

        from app.services.ELI5.eli5_services import (
            ELI5Service,
        )

        service = ELI5Service()

        response = await service.generate_explanation(
            request=request,
            db=db,
            user=current_user,
        )

        return response

    except HTTPException:
        raise

    except ValueError as exc:

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )

    except Exception as exc:

        print(
            "[ELI5] Generation failed:",
            repr(exc),
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate explanation.",
        )