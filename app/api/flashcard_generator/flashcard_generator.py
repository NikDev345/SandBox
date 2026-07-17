"""
Flashcard Generator API
-----------------------
Handles HTTP endpoints for the Flashcard Generator.

Responsibilities:
- Authenticate users
- Validate requests
- Delegate business logic to the service layer

No AI logic should exist in this file.
"""

from fastapi import APIRouter, Depends, HTTPException, status

from app.models.flashcard_generator import (
    FlashcardGeneratorRequest,
    FlashcardGeneratorResponse,
)
from app.models.user import Users
from app.services.flashcard_generator.flashcard_generator import (
    FlashcardGeneratorService,
)
from app.utils.auth import get_current_user

router = APIRouter(
    prefix="/flashcard-generator",
    tags=["Flashcard Generator"],
)


@router.post(
    "/generate",
    response_model=FlashcardGeneratorResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate Flashcards",
)
async def generate_flashcards(
    request: FlashcardGeneratorRequest,
    current_user: Users = Depends(get_current_user),
) -> FlashcardGeneratorResponse:
    """
    Generate educational flashcards from provided content.
    """

    try:
        return await FlashcardGeneratorService.generate(
            request=request,
            user=current_user,
        )

    except HTTPException:
        raise

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )

    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        )

    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Flashcard generation failed: {str(exc)}",
        )
