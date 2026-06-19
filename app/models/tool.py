from sqlalchemy import Column, ForeignKey, Integer, String, DateTime
from database.engine import Base
from pydantic import BaseModel
    
class Tools(Base):
    __tablename__ = 'tools'
    
    id = Column(Integer, primary_key=True)
    name = Column(String)
    slug = Column(String, unique=True)
    category = Column(String)
    
# Session Schemas-------------------------------------------------------------------

class ToolCreate(BaseModel):
    name: str
    category: str
    
class ToolResponse(BaseModel):
    id: int
    name: str
    category: str
    slug: str
    
    class Config: 
        orm_mode = True