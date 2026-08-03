from sqlalchemy import Column, ForeignKey, String, DateTime, UniqueConstraint
from app.database.engine import Base
from pydantic import BaseModel
from datetime import datetime

class Bookmarks(Base):
    __tablename__ = "bookmarks"
    
    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "execution_id",
            name="uq_user_execution_bookmark"
        ),
    )
    
    id = Column(String, primary_key=True)

    user_id = Column(
        String,
        ForeignKey("users.id"),
        nullable=False
    )

    execution_id = Column(
        String,
        ForeignKey("executions.id"),
        nullable=False
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )
    
# request model
class BookmarkCreate(BaseModel):
    execution_id: str
    
# response model
class BookmarkResponse(BaseModel):
    id: str
    execution_id: str
    created_at: datetime

    class Config:
        orm_mode = True
        
# item model for bookmark list
class BookmarkItem(BaseModel):
    bookmark_id: str
    execution_id: str
    tool_name: str
    tool_slug: str
    user_input: str
    output: str
    created_at: datetime
    
# List response model
class BookmarkListResponse(BaseModel):
    bookmarks: list[BookmarkItem]