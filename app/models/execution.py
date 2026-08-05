
from sqlalchemy import Column, ForeignKey, String, DateTime, Boolean, func
from zoneinfo import ZoneInfo
from app.database.engine import Base
from pydantic import BaseModel, field_validator
from datetime import timedelta, timezone, datetime
class Executions(Base):
    __tablename__ = 'executions'
    
    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"))
    tool_id = Column(String, ForeignKey("tools.id"))
    user_input = Column(String)
    output = Column(String)
    created_at = Column(
            DateTime(timezone=True),
            server_default=func.now(),  # DB generates the time
            default=lambda: datetime.now(timezone.utc),
            nullable=False,
        )
    bookmarked = Column(Boolean, default=False, nullable=False)
    
class ExecutionCreate(BaseModel):
    tool_id: str    
    user_input: str
    output: str

IST = timezone(timedelta(hours=5, minutes=30))
def to_ist(dt):
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(IST).isoformat()

class ExecutionResponse(BaseModel):
    id: str
    user_id: str
    tool_id: str
    user_input: str
    output: str
    created_at: datetime
    bookmarked: bool = False
    @field_validator("created_at", mode="before")
    @classmethod
    def convert_to_ist(cls, v):
        if isinstance(v, datetime):
            if v.tzinfo is None:
                v = v.replace(tzinfo=timezone.utc)  # assume UTC from DB
            return v.astimezone(IST)
        return v
    
    class Config:
        orm_mode = True