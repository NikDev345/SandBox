from sqlalchemy import Column, String, DateTime, Boolean
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
    
    # Connected accounts
    google_connected = Column(Boolean, default=False)
    github_connected = Column(Boolean, default=False)

    google_id = Column(String, unique=True)
    github_id = Column(String, unique=True)

    google_email = Column(String)
    github_email = Column(String)

    google_avatar = Column(String)
    github_avatar = Column(String)

    google_name = Column(String)
    github_name = Column(String)
    
    local_name = Column(String, nullable=False)
    local_email = Column(String, nullable=False)
    local_avatar = Column(
        String,
        default="ui/assets/default_avatar.png",
        nullable=False
    )
    
    name_customized = Column(Boolean, default=False)
    email_customized = Column(Boolean, default=False)
    avatar_customized = Column(Boolean, default=False)
    
    last_updated = Column(String, nullable=True)

    
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
    
class DeleteConfirmation(BaseModel):
    confirmation_text: str