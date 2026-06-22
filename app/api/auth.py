from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.utils.jwt import create_access_token

from app.database.engine import get_db

from app.models.user import (
    UserCreate,
    UserLogin
)

from app.services.auth_service import (
    AuthService
)

router = APIRouter(
    prefix="/auth",
    tags=["Auth"]
)


@router.post("/signup")
def signup(
    data: UserCreate,
    db: Session = Depends(get_db)
):

    user = AuthService.create_user(
        db=db,
        name=data.name,
        email=data.email,
        password=data.password
    )

    if not user:

        raise HTTPException(
            status_code=400,
            detail="Email already exists"
        )

    return {
        "message":
        "User created successfully"
    }


@router.post("/login")
def login(
    data: UserLogin,
    db: Session = Depends(get_db)
):

    user = AuthService.authenticate_user(
        db=db,
        email=data.email,
        password=data.password
    )

    if not user:

        raise HTTPException(
            status_code=401,
            detail="Invalid credentials"
        )
        
    token = create_access_token(
        {
            "sub": user.id,
            "email": user.email
        }
    )

    return {
        "access_token": token,
        "token_type": "bearer",
        "user_id": user.id
    }