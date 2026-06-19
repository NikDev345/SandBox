from sqlalchemy import Column, ForeignKey, Integer, String, DateTime
from database.engine import Base
from pydantic import BaseModel
from datetime import datetime

class Users(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    email = Column(String)
    provider = Column(String)
    created_at = Column(DateTime)
    
# Session Schemas-------------------------------------------------------------------
class UserCreate(BaseModel):
    name: str
    email: str
    password: str
        
class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    provider: str
    created_at: datetime
    
    class Config: 
        orm_mode = True
        
class UserLogin(BaseModel):
    email: str
    password: str