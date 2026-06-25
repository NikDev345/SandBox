from sqlalchemy import Column, String, DateTime
from app.database.engine import Base
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime

class Users(Base):
    __tablename__ = 'users'
    
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=True)
    provider = Column(String, default='local', index=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    role = Column(String, default='user')

    
# Session Schemas-------------------------------------------------------------------
class UserCreate(BaseModel):
    name: str = Field(min_length=2)
    email: EmailStr
    password: str = Field(min_length=6)
        
class UserResponse(BaseModel):
    id: str
    name: str
    email: str
    provider: str
    created_at: datetime
    
    class Config: 
        orm_mode = True
        
class UserLogin(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)
