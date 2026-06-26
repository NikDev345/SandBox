from sqlalchemy import Column, String, DateTime, Integer
from pydantic import BaseModel, EmailStr, Field
from app.database.engine import Base
from datetime import datetime


class EmailOTP(Base):
    __tablename__ = "email_otps"

    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    email = Column(String, index=True, nullable=False)
    name = Column(String, nullable=False)
    hash_password = Column(String, nullable=False)
    hash_otp = Column(String, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    

class SendOTPRequest(BaseModel):
    name: str = Field(min_length=2)
    email: EmailStr
    password: str = Field(min_length=6)


class VerifyOTPRequest(BaseModel):
    email: EmailStr
    otp: str = Field(min_length=6, max_length=6)
    
class ResendOTPRequest(BaseModel):
    email: EmailStr