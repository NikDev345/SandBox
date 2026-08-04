from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.engine import get_db
from app.utils.auth import get_current_user
from app.services.workspace_service import WorkspaceService

router = APIRouter(
    prefix="/workspace",
    tags=["Workspace"],
)


@router.get("/")
def get_workspace(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Return all data required to render the user's workspace dashboard.
    """

    try:
        workspace = WorkspaceService.get_workspace(
            db=db,
            user_id=current_user["sub"],
        )

        return {
            "success": True,
            "workspace": workspace,
        }

    except ValueError as e:
        raise HTTPException(
            status_code=404,
            detail=str(e),
        )

    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Failed to load workspace.",
        )