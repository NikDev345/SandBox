from fastapi import APIRouter, HTTPException, Depends

from app.models.sql_generator import (
    SQLGeneratorRequest,
    SQLGeneratorResponse,
)
from app.services.sql_generator.sql_generator import SQLGeneratorService
from app.utils.auth import get_current_user
from app.models.user import Users
from app.database.engine import get_db
from sqlalchemy.orm import Session

router = APIRouter(
    prefix="/sql-generator",
    tags=["SQL Generator"],
)


@router.post(
    "/generate",
    response_model=SQLGeneratorResponse,
    summary="Generate SQL Query",
    description="""
Generate a SQL query using either:

- AI Prompt
- Visual Builder
""",
)
async def generate_sql(
    request: SQLGeneratorRequest, current_user:Users = Depends(get_current_user), db: Session = Depends(get_db)
) -> SQLGeneratorResponse:
    """
    Generates a SQL query.
    """

    try:
        return SQLGeneratorService.generate(request, current_user, db)

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e),
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate SQL: {e}",
        )