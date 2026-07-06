from datetime import datetime

from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    ForeignKey
)

from pydantic import BaseModel, EmailStr, Field

from app.database.engine import Base


class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"

    id = Column(
        Integer,
        primary_key=True,
        autoincrement=True,
        nullable=False
    )

    user_id = Column(
        String,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    token = Column(
        String,
        unique=True,
        nullable=False,
        index=True
    )

    expires_at = Column(
        DateTime,
        nullable=False
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )


# -----------------------------
# Request Schemas
# -----------------------------

class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str

    password: str = Field(
        min_length=6
    )