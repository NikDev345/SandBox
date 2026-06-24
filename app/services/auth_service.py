from sqlalchemy.orm import Session
from app.models.user import Users
from app.utils.security import (
    hash_password,
    verify_password
)
import uuid 


class AuthService:


    @staticmethod
    def create_user(
        db: Session,
        name: str,
        email: str,
        password: str
    ):

        existing_user = db.query(Users).filter(Users.email == email).first()

        if existing_user:

            return None

        user = Users(
            id = str(uuid.uuid4()),
            name=name,
            email=email,
            password_hash=hash_password(
                password
            ),
            provider="local",
            role='users'
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

        user = db.query(Users).filter(Users.email == email).first()

        if not user:

            return None

        if not verify_password(
            password,
            user.password_hash
        ):
            return None

        return user

    @staticmethod
    def get_profile(db: Session, current_user: Session):
        user = db.query(Users).filter(Users.id == current_user['sub']).first()
        
        return {
            'id': user.id,
            
            'name': user.name,
            'email': user.email,
            'role': user.role,
            'provider': user.provider
        }