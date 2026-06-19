from sqlalchemy import Column, ForeignKey, Integer, String, DateTime
from database.engine import Base
from pydantic import BaseModel
from datetime import datetime

    
class Analytics(Base):
    __tablename__ = 'analytics'
    
    id = Column(Integer, primary_key=True)
    tool_id = Column(Integer)
    event_type = Column(String)
    timestamp = Column(DateTime)
    
class AnalyticCreate(BaseModel):
    tool_id: int
    event_type: str
    
class AnalyticResponse(BaseModel):
    id: int
    tool_id: int
    event_type: str
    timestamp: datetime
    
    class Config:
        orm_mode = True