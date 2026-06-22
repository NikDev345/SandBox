from sqlalchemy import Column, String, DateTime
from app.database.engine import Base
from pydantic import BaseModel
from datetime import datetime


class Users(Base):
    __tablename__ = 'users'
    
    id = Column(String, primary_key=True)
    name = Column(String)
    email = Column(String, unique=True)
    password_hash = Column(String)
    provider = Column(String, default='local')
    created_at = Column(DateTime, default=datetime.utcnow)
    
# Session Schemas-------------------------------------------------------------------
class UserCreate(BaseModel):
    name: str
    email: str
    password: str
        
class UserResponse(BaseModel):
    id: str
    name: str
    email: str
    provider: str
    created_at: datetime
    
    class Config: 
        orm_mode = True
        
class UserLogin(BaseModel):
    email: str
    password: str