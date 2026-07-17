"""
Flashcard Generator API
-----------------------
Handles HTTP endpoints for the Flashcard Generator.

Responsibilities:
- Authenticate users
- Validate requests
- Parse uploaded documents
- Delegate business logic to the service layer

No AI logic should exist in this file.
"""

import os
import tempfile

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    UploadFile,
    status,
)

from app.models.flashcard_generator import (
    FlashcardDifficulty,
    FlashcardGeneratorRequest,
    FlashcardGeneratorResponse,
    FlashcardLanguage,
    FlashcardSettings,
    FlashcardType,
)
from app.models.user import Users
from app.services.flashcard_generator.flashcard_generator import (
    FlashcardGeneratorService,
)
from app.services.quiz.parser import DocumentParser
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
    content: str | None = Form(None),

    file: UploadFile | None = File(None),

    number_of_cards: int = Form(10),

    difficulty: FlashcardDifficulty = Form(FlashcardDifficulty.MEDIUM),

    card_type: FlashcardType = Form(FlashcardType.BASIC),

    language: FlashcardLanguage = Form(FlashcardLanguage.ENGLISH),

    include_examples: bool = Form(True),

    include_memory_tips: bool = Form(True),

    include_keywords: bool = Form(True),

    include_tags: bool = Form(True),

    shuffle_cards: bool = Form(False),

    current_user: Users = Depends(get_current_user),
) -> FlashcardGeneratorResponse:
    """
    Generate educational flashcards from pasted content or an uploaded document.
    """

    try:
        extracted_text = content

        if file is not None:

            extension = os.path.splitext(
                file.filename
            )[1].lower()

            with tempfile.NamedTemporaryFile(
                delete=False,
                suffix=extension,
            ) as temp:

                temp.write(await file.read())

                temp_path = temp.name

            try:

                extracted_text = DocumentParser.parse(
                    temp_path
                )

            finally:

                if os.path.exists(temp_path):
                    os.remove(temp_path)

        if not extracted_text:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Provide either pasted content or a document to upload.",
            )

        request = FlashcardGeneratorRequest(
            content=extracted_text,
            settings=FlashcardSettings(
                number_of_cards=number_of_cards,
                difficulty=difficulty,
                card_type=card_type,
                language=language,
                include_examples=include_examples,
                include_memory_tips=include_memory_tips,
                include_keywords=include_keywords,
                include_tags=include_tags,
                shuffle_cards=shuffle_cards,
            ),
        )

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