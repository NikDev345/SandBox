from fastapi import APIRouter
from fastapi import Depends
from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.database.engine import get_db
from app.utils.auth import get_current_user

from app.services.history_service import HistoryService

router = APIRouter(
    prefix="/history",
    tags=["History"]
)


@router.get("/")
def get_history(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    history = HistoryService.get_user_history(
        db=db,
        user_id=current_user["sub"]
    )

    return {
        "success": True,
        "history": history
    }
    
@router.get("/{execution_id}")
def get_history_details(
    execution_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    history = HistoryService.get_history_details(
        db=db,
        execution_id=execution_id,
        user_id=current_user["sub"]
    )

    if not history:
        return {
            "success": False,
            "message": "History not found."
        }

    return {
        "success": True,
        "history": history
    }
@router.delete("/{execution_id}")
def delete_history(
    execution_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    deleted = HistoryService.delete_history(
        db=db,
        execution_id=execution_id,
        user_id=current_user["sub"]
    )

    if not deleted:
        raise HTTPException(
            status_code=404,
            detail="History not found."
        )

    return {
        "success": True,
        "message": "History deleted successfully."
    }