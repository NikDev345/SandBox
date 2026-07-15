"""
Quiz Generator API
------------------
Handles HTTP endpoints for the Quiz Generator.

Responsibilities:
- Authenticate users
- Validate requests
- Parse uploaded documents
- Clean extracted text
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

from app.models.quiz_generator import (
    Audience,
    Difficulty,
    DocumentType,
    InputType,
    Language,
    QuestionType,
    QuizRequest,
    QuizSettings,
    QuizResponse,
)
from app.models.user import Users
from app.services.quiz.parser import DocumentParser
from app.services.quiz.quiz_generator import QuizGeneratorService
from app.utils.auth import get_current_user
from app.utils.text_cleaner import TextCleaner

router = APIRouter(
    prefix="/quiz",
    tags=["Quiz Generator"],
)


@router.post(
    "/generate",
    response_model=QuizResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate Quiz",
)
async def generate_quiz(
    input_type: InputType = Form(...),

    prompt: str | None = Form(None),

    file: UploadFile | None = File(None),

    question_count: int = Form(10),

    difficulty: Difficulty = Form(Difficulty.MEDIUM),

    language: Language = Form(Language.ENGLISH),

    audience: Audience = Form(Audience.COLLEGE),

    include_explanations: bool = Form(True),

    include_hints: bool = Form(False),

    current_user: Users = Depends(get_current_user),
):

    try:

        extracted_text = None
        document_type = None

        if input_type == InputType.DOCUMENT:

            if file is None:
                raise HTTPException(
                    status_code=400,
                    detail="Document is required.",
                )

            extension = os.path.splitext(
                file.filename
            )[1].lower()

            document_type = DocumentType(
                extension.replace(".", "")
            )

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

                extracted_text = TextCleaner.clean(
                    extracted_text
                )

            finally:

                if os.path.exists(temp_path):
                    os.remove(temp_path)

        request = QuizRequest(

            input_type=input_type,

            prompt=prompt,

            extracted_text=extracted_text,

            document_type=document_type,

            settings=QuizSettings(

                question_count=question_count,

                difficulty=difficulty,

                language=language,

                audience=audience,

                question_types=[
                    QuestionType.MCQ
                ],

                include_explanations=include_explanations,

                include_hints=include_hints,
            ),
        )

        service = QuizGeneratorService()

        return await service.generate_quiz(
            request=request,
            user=current_user,
        )

    except HTTPException:
        raise

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=f"Quiz generation failed: {str(exc)}",
        )