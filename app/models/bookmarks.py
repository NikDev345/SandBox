from sqlalchemy import Column, ForeignKey, String, DateTime, UniqueConstraint, func
from app.database.engine import Base
from pydantic import BaseModel, field_validator
from datetime import datetime, timezone, timedelta

IST = timezone(timedelta(hours=5, minutes=30))

def to_ist(dt):
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(IST)

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
        DateTime(timezone=True),
        server_default=func.now(),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    
# request model
class BookmarkCreate(BaseModel):
    execution_id: str
    
# response model
class BookmarkResponse(BaseModel):
    id: str
    execution_id: str
    created_at: datetime
    
    @field_validator("created_at", mode="before")
    @classmethod
    def convert_to_ist(cls, v):
        if isinstance(v, datetime):
            return to_ist(v)
        return v


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
    
    @field_validator("created_at", mode="before")
    @classmethod
    def convert_to_ist(cls, v):
        if isinstance(v, datetime):
            return to_ist(v)
        return v
    
# List response model
class BookmarkListResponse(BaseModel):
    bookmarks: list[BookmarkItem]