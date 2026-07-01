from sqlalchemy import Column, String, DateTime
from app.database.engine import Base
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
import uuid


class Users(Base):
    __tablename__ = 'users'
    def generate_uuid():
        return str(uuid.uuid4())
    
    id = Column(String, primary_key=True, default= generate_uuid, nullable=False)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=True)
    provider = Column(String, default='local', index=True, nullable=False)
    provider_user_id = Column(String, nullable=True)
    avatar_url = Column(String, default='ui/assets/default_avatar.png', nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    role = Column(String, default='user')
    bio = Column(String, default="")
    accent_color = Column(String,default="blue")
    theme = Column(
        String,
        default="dark"
    )

    animations = Column(
        String,
        default="enabled"
    )

    sidebar_mode = Column(
        String,
        default="expanded"
    )

    
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

class UpdatePasswordRequest(BaseModel):
    current_password: str
    new_password: str