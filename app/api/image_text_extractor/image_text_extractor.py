"""
app/api/image_text_extractor/image_text_extractor.py
----------------------------------------------------
FastAPI router for the Image Text Extractor tool.

Responsibilities
----------------
- Authenticate user
- Receive uploaded image
- Build request model
- Delegate business logic to ImageTextExtractorService
- Return typed response
"""

from __future__ import annotations

import logging
from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    UploadFile,
    status,
)

from app.models.image_text_extractor import (
    ImageTextExtractorRequest,
    ImageTextExtractorResponse,
)

from app.services.image_text_extractor import (
    image_text_extractor_service,
)
from app.utils.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/image-text-extractor",
    tags=["Image Text Extractor"],
)

SUPPORTED_CONTENT_TYPES = {
    "image/png",
    "image/jpeg",
    "image/jpg",
    "image/webp",
    "image/bmp",
    "image/tiff",
}


@router.post(
    "/extract",
    response_model=ImageTextExtractorResponse,
    summary="Extract text from an uploaded image",
)
async def extract_text(
    current_user = Depends(get_current_user),
    image: UploadFile = File(...),
    language: str = Form("auto"),
    preserve_layout: bool = Form(True),
    enhance_image: bool = Form(True),
    output_format: str = Form("text"),
) -> ImageTextExtractorResponse:
    """
    Extract text from an uploaded image.

    Authentication
    --------------
    JWT Required

    Supported Formats
    -----------------
    - PNG
    - JPG
    - JPEG
    - WEBP
    - BMP
    - TIFF
    """

    logger.info(
        "Image OCR request | user=%s | file=%s",
current_user.get("sub"),
        image.filename,
    )

    if image.content_type not in SUPPORTED_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported content type: {image.content_type}",
        )

    request = ImageTextExtractorRequest(
        language=language,
        preserve_layout=preserve_layout,
        enhance_image=enhance_image,
        output_format=output_format,
    )

    try:

        response = await image_text_extractor_service.process(
            file=image,
            request=request,
        )

        logger.info(
            "OCR completed | user=%s | success=%s",
            current_user.get("sub"),
            response.success,
        )

        return response

    except ValueError as exc:

        logger.warning(
            "Validation failed | user=%s | %s",
            current_user.get("sub"),
            exc,
        )

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    except RuntimeError as exc:

        logger.exception(
            "OCR runtime error | user=%s",
            current_user.get("sub"),
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc

    except Exception as exc:

        logger.exception(
            "Unexpected OCR exception | user=%s",
            current_user.email,
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error.",
        ) from exc