from sqlalchemy import Column, ForeignKey, String, DateTime, Boolean
from app.database.engine import Base
from pydantic import BaseModel
from datetime import datetime

class Executions(Base):
    __tablename__ = 'executions'
    
    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"))
    tool_id = Column(String, ForeignKey("tools.id"))
    user_input = Column(String)
    output = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    bookmarked = Column(Boolean, default=False, nullable=False)
    
class ExecutionCreate(BaseModel):
    tool_id: str    
    user_input: str
    output: str
    
class ExecutionResponse(BaseModel):
    id: str
    user_id: str
    tool_id: str
    user_input: str
    output: str
    created_at: datetime
    bookmarked: bool = False
    
    class Config:
        orm_mode = True