from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database.engine import get_db
from app.utils.auth import get_current_user
from app.models.bookmarks import (
    BookmarkCreate,
    BookmarkResponse,
    BookmarkListResponse
)
from app.services.bookmark_service import BookmarkService

router = APIRouter(
    prefix="/bookmarks",
    tags=["Bookmarks"],
)


@router.post(
    "",
    response_model=BookmarkResponse,
    status_code=201,
)
def create_bookmark(
    request: BookmarkCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        return BookmarkService.create_bookmark(
            db=db,
            user_id=current_user["sub"],
            execution_id=request.execution_id,
        )
    except PermissionError as e:
        raise HTTPException(
            status_code=403,
            detail=str(e),
        )
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e),
        )


@router.get("", response_model=BookmarkListResponse)
def get_bookmarks(
    tool: str | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        return BookmarkService.get_bookmarks(
            db=db,
            user_id=current_user["sub"],
            tool_slug=tool,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=404,
            detail=str(e),
        )


@router.delete("/{execution_id}")
def delete_bookmark(
    execution_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        BookmarkService.delete_bookmark(
            db=db,
            user_id=current_user["sub"],
            execution_id=execution_id,
        )

        return {
            "success": True,
            "message": "Bookmark deleted successfully.",
        }

    except ValueError as e:
        raise HTTPException(
            status_code=404,
            detail=str(e),
        )