from sqlalchemy.orm import Session
from app.models.user import Users
from app.utils.security import (
    hash_password,
    verify_password
)
import uuid 


class AuthService:

    @staticmethod
    def get_user_by_email(
        db: Session,
        email: str
    ):
        return (
            db.query(Users)
            .filter(
                Users.email == email.strip().lower()
            )
            .first()
        )

    @staticmethod
    def get_user_by_id(
        db: Session,
        user_id: str
    ):
        return (
            db.query(Users)
            .filter(
                Users.id == user_id
            )
            .first()
        )

    @staticmethod
    def create_user(
        db: Session,
        name: str,
        email: str,
        password: str
    ):
        normalized_email = email.strip().lower()

        existing_user = AuthService.get_user_by_email(
            db,
            normalized_email
        )

        if existing_user:

            return None

        user = Users(
            id = str(uuid.uuid4()),
            name=name,
            email=normalized_email,
            password_hash=hash_password(
                password
            ),
            provider="local"
        )

        db.add(user)

        db.commit()

        db.refresh(user)

        return user

    @staticmethod
    def create_guest_user(
        db: Session
    ):
        guest_id = str(uuid.uuid4())

        user = Users(
            id=guest_id,
            name="Guest",
            email=f"guest-{guest_id}@guest.toolbox.local",
            password_hash=None,
            provider="guest"
        )

        db.add(user)
        db.commit()
        db.refresh(user)

        return user

    @staticmethod
    def get_or_create_oauth_user(
        db: Session,
        provider: str,
        email: str,
        name: str
    ):
        normalized_email = email.strip().lower()
        user = AuthService.get_user_by_email(
            db,
            normalized_email
        )

        if user:
            if user.provider != provider and not user.password_hash:
                user.provider = provider
                db.commit()
                db.refresh(user)

            return user

        user = Users(
            id=str(uuid.uuid4()),
            name=name or normalized_email.split("@")[0],
            email=normalized_email,
            password_hash=None,
            provider=provider
        )

        db.add(user)
        db.commit()
        db.refresh(user)

        return user

    @staticmethod
    def authenticate_user(
        db: Session,
        email: str,
        password: str
    ):
        normalized_email = email.strip().lower()

        user = AuthService.get_user_by_email(
            db,
            normalized_email
        )

        if not user:

            return None

        if user.provider != "local" or not user.password_hash:

            return None

        if not verify_password(
            password,
            user.password_hash
        ):
            return None

        return user
