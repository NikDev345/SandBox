from sqlalchemy import Column, ForeignKey, Integer, String, DateTime
from app.database.engine import Base
from pydantic import BaseModel
from datetime import datetime

    
class Analytics(Base):
    __tablename__ = 'analytics'
    
    id = Column(String, primary_key=True)
    tool_id = Column(String,ForeignKey("tools.id"))
    event_type = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
class AnalyticCreate(BaseModel):
    tool_id: str
    event_type: str
    
class AnalyticResponse(BaseModel):
    id: str
    tool_id: str
    event_type: str
    timestamp: datetime
    
    class Config:
        orm_mode = True