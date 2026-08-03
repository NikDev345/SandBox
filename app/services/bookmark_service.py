from app.models.bookmarks import Bookmarks, BookmarkResponse, BookmarkItem, BookmarkListResponse
from app.models.execution import Executions
from app.models.tool import Tools
from sqlalchemy.orm import Session
import uuid
from datetime import datetime, timezone
from app.services.tool_service import ToolService

class BookmarkService:
    
    @staticmethod
    def create_bookmark(
        db: Session,
        user_id: str,
        execution_id: str,
    ):
        exists = db.query(Executions).filter(Executions.id==execution_id).first()
        if not exists:
            raise ValueError("Execution not found.")
        
        if exists.user_id != user_id:
            raise PermissionError(
                "You are not authorized to bookmark this execution."
            )
        
        existing_bookmark = (
            db.query(Bookmarks)
            .filter(
                Bookmarks.user_id == user_id,
                Bookmarks.execution_id == execution_id,
            )
            .first()
        )
        if existing_bookmark:
            raise ValueError("Execution is already bookmarked.")
        
        bookmark = Bookmarks(
            id=str(uuid.uuid4()),
            user_id=user_id,
            execution_id=execution_id,
            created_at=datetime.utcnow(),
        )
        try:
            db.add(bookmark)
            db.commit()
            db.refresh(bookmark)
        except Exception:
            db.rollback()
            raise
        
        return BookmarkResponse(
            id=bookmark.id,
            execution_id=bookmark.execution_id,
            created_at=bookmark.created_at,
        )
        
    @staticmethod
    def delete_bookmark(
        db: Session,
        user_id: str,
        execution_id: str,
    ): 
        bookmark = db.query(
            Bookmarks
        ).filter(
            Bookmarks.user_id == user_id,
            Bookmarks.execution_id == execution_id
        ).first()
        
        if not bookmark:
            raise ValueError("Bookmark not fount")
        
        try:
            db.delete(bookmark)
            db.commit()
            return True
        except Exception:
            db.rollback()
            raise
        
    @staticmethod
    def get_bookmarks(db: Session, user_id: str, tool_slug: str | None = None) -> list[BookmarkItem]:
        
        query = (
            db.query(
                Bookmarks, 
                Executions,
                Tools
            ).join(
                Executions,
                Bookmarks.execution_id == Executions.id
            ).join(
                Tools,
                Executions.tool_id == Tools.id
            ).filter(
                Bookmarks.user_id == user_id
            )
        )
        
        if tool_slug:
            tool = ToolService.get_tool_by_slug(db=db, slug=tool_slug)
            
            if not tool:
                raise ValueError("404. Tool not found")
            
            query = query.filter(
                Executions.tool_id == tool.id
            )
            
        results = (
            query.order_by(
                Bookmarks.created_at.desc()
            ).all()
        )

        bookmarks = []

        for bookmark, execution, tool in results:
            bookmarks.append(
                BookmarkItem(
                    bookmark_id=bookmark.id,
                    execution_id=execution.id,
                    tool_name=tool.name,
                    tool_slug=tool.slug,
                    user_input=execution.user_input,
                    output=execution.output,
                    created_at=bookmark.created_at,
                )
            )

        return BookmarkListResponse(
            bookmarks=bookmarks
        )