from sqlalchemy import Column, String, DateTime, Boolean
from pydantic import BaseModel, EmailStr, Field
from app.database.engine import Base
from datetime import datetime


class PasswordOTP(Base):
    __tablename__ = "password_otps"

    email = Column(String, primary_key=True, nullable=False)
    hash_otp = Column(String, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    verified = Column(Boolean, default=False, nullable=False)


class PasswordOTPRequest(BaseModel):
    email: EmailStr


class VerifyPasswordOTPRequest(BaseModel):
    email: EmailStr
    otp: str = Field(min_length=6, max_length=6)


class ChangePasswordRequest(BaseModel):
    email: EmailStr
    new_password: str = Field(min_length=6)
    confirm_password: str = Field(min_length=6)