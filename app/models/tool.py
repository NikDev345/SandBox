from sqlalchemy import Column, String, DateTime, Text
from app.database.engine import Base
from pydantic import BaseModel
from datetime import datetime


class Tools(Base):
    __tablename__ = 'tools'
    
    id = Column(String, primary_key=True)
    name = Column(String(100))
    slug = Column(String(100), unique=True)
    description = Column(Text)
    category = Column(String(50))
    icon_url = Column(Text)
    source_path = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
# Session Schemas-------------------------------------------------------------------

class ToolCreate(BaseModel):
    name: str
    category: str
    description: str
    icon_url: str
    source_path: str
    
    
class ToolResponse(BaseModel):
    id: str
    name: str   
    category: str
    slug: str
    
    class Config: 
        orm_mode = True