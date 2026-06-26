from datetime import datetime, timedelta
import secrets

from sqlalchemy.orm import Session

from app.models.user import Users
from app.models.password_reset import PasswordResetToken
from app.utils.security import hash_password
from app.services.email_service import send_reset_password_email


class PasswordResetService:

    @staticmethod
    def create_reset_token(
        db: Session,
        email: str
    ):

        user = (
            db.query(Users)
            .filter(Users.email == email)
            .first()
        )

        if not user:
            return None

        db.query(PasswordResetToken).filter(
            PasswordResetToken.user_id == user.id
        ).delete()

        token = secrets.token_urlsafe(32)

        reset_token = PasswordResetToken(
            user_id=user.id,
            token=token,
            expires_at=datetime.utcnow() + timedelta(minutes=15)
        )

        db.add(reset_token)
        db.commit()

        sent = send_reset_password_email(
            email=email,
            token=token
        )

        if not sent:
            db.delete(reset_token)
            db.commit()
            return False

        return True


    @staticmethod
    def reset_password(
        db: Session,
        token: str,
        password: str
    ):

        token_record = (
            db.query(PasswordResetToken)
            .filter(PasswordResetToken.token == token)
            .first()
        )

        if not token_record:
            return None

        if datetime.utcnow() > token_record.expires_at:
            db.delete(token_record)
            db.commit()
            return False

        user = (
            db.query(Users)
            .filter(Users.id == token_record.user_id)
            .first()
        )

        if not user:
            return None

        user.password_hash = hash_password(password)

        db.delete(token_record)

        db.commit()

        db.refresh(user)

        return user