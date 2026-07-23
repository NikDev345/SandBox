from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.models.user import Users
from app.database.engine import get_db
from app.utils.auth import get_current_user

from app.models.regex import (
    RegexGeneratorRequest,
    RegexGeneratorResponse
)
from app.services.regex_generator.regex import Regex

router = APIRouter(
    prefix="/regex",
    tags=["Regex Generator"]
)


@router.post(
    "/generate",
    response_model=RegexGeneratorResponse,
    summary="Generate Regex"
)
async def generate_regex(
    request: RegexGeneratorRequest,
    db: Session = Depends(get_db),
    current_user: Users = Depends(get_current_user)
):
    try:
        return Regex.generate_regex(request)

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate regex: {e}"
        )