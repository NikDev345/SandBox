"""
Brainstorm Generator API

Provides endpoints for AI-powered brainstorming.
"""

from fastapi import APIRouter, Depends, HTTPException, status

from app.utils.auth import get_current_user
from app.models.brainstorm_generator import (
    BrainstormRequest,
    BrainstormResponse,
)
from app.services.brainstorm_generator.brainstorm_generator_service import (
    BrainstormGeneratorService,
)

router = APIRouter(
    prefix="/brainstorm-generator",
    tags=["Brainstorm Generator"],
)


@router.post(
    "/generate",
    response_model=BrainstormResponse,
    status_code=status.HTTP_200_OK,
)
def generate_brainstorm(
    request: BrainstormRequest,
    current_user=Depends(get_current_user),
):
    """
    Generate brainstorming ideas using AI.
    """

    try:
        return BrainstormGeneratorService.generate(request)

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )

    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate brainstorming ideas: {str(exc)}",
        )