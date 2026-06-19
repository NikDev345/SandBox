from sqlalchemy.orm import Session

from app.models.user import Users
from app.utils.security import (
    hash_password,
    verify_password
)


class AuthService:

    @staticmethod
    def create_user(
        db: Session,
        name: str,
        email: str,
        password: str
    ):

        existing_user = (
            db.query(Users)
            .filter(
                Users.email == email
            )
            .first()
        )

        if existing_user:

            return None

        user = Users(
            name=name,
            email=email,
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
    def authenticate_user(
        db: Session,
        email: str,
        password: str
    ):

        user = (
            db.query(Users)
            .filter(
                Users.email == email
            )
            .first()
        )

        if not user:

            return None

        if not verify_password(
            password,
            user.password_hash
        ):
            return None

        return user