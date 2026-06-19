from sqlalchemy import Column, ForeignKey, Integer, String, DateTime
from database.engine import Base
from pydantic import BaseModel
from datetime import datetime
    
class Executions(Base):
    __tablename__ = 'executions'
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    tool_id = Column(Integer, ForeignKey("tools.id"))
    user_input = Column(String)
    output = Column(String)
    created_at = Column(DateTime)
    
class ExecutionCreate(BaseModel):
    user_id: int
    tool_id: int    
    user_input: str
    output: str
    
class ExecutionResponse(BaseModel):
    id: int
    user_id: int
    tool_id: int
    user_input: str
    output: str
    created_at: datetime
    
    class Config:
        orm_mode = True