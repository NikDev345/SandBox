"""
============================================================
Decision Maker API

FastAPI endpoints for the Decision Maker tool.

Author: Sandbox AI
============================================================
"""

from fastapi import APIRouter, Depends, HTTPException, status

from app.models.decision_maker import (
    DecisionMakerRequest,
    DecisionMakerResponse,
)
from app.utils.auth import get_current_user
from app.services.decision_maker.decision_maker_service import (
    DecisionMakerService,
)

router = APIRouter(
    prefix="/decision-maker",
    tags=["Decision Maker"],
)


@router.post(
    "/analyze",
    response_model=DecisionMakerResponse,
    status_code=status.HTTP_200_OK,
)
async def analyze_decision(
    request: DecisionMakerRequest,
    current_user=Depends(get_current_user),
):
    """
    Analyze a user's decision using AI.
    """

    try:

        response = await DecisionMakerService.analyze(
            request
        )

        return response

    except ValueError as exc:

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )

    except RuntimeError as exc:

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        )

    except Exception:

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred.",
        )   