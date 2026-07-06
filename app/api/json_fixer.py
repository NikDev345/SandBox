from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.utils.auth import get_current_user
from app.database.engine import get_db
from app.models.json_fixer import (
    JSONFixRequest,
    JSONFixResponse,
)
from app.services.json_fixer_service import JSONFixerService

router = APIRouter(
    prefix="/json-fixer",
    tags=["Developer - JSON Fixer"],
)


@router.post(
    "/fix",
    response_model=JSONFixResponse,
)
def fix_json(
    request: JSONFixRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Repair and format malformed JSON.
    """
    try:
        result = JSONFixerService.fix_json(
            db=db,
            user_id=current_user["sub"],
            json_text=request.json_text,
        )
        return JSONFixResponse(**result)

    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    except Exception as e:
        print("JSON Fixer Error:", repr(e))
        raise HTTPException(status_code=500, detail="Internal server error.")