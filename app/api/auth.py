
from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.database.engine import get_db
from app.models.user import UserCreate, UserLogin
from app.services.auth_service import AuthService
from app.utils.jwt import create_access_token
from app.utils.auth import get_current_user


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
        name=data.name.strip(),
        email=data.email,
        password=data.password
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already exists"
        )

    return {
        "message": "User created successfully",
        "user": data.name
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
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )

    token = create_access_token(
        {"sub": user.id,
         "email": user.email}
        
    )
    return {
        "access_token": token,
        "token_type": "bearer",
        "user_id": user.id,
        "role": user.role
    }

@router.get('/me')
def get_profile(db: Session = Depends(get_db), current_user= Depends(get_current_user)):
    
    user = AuthService.get_profile(db, current_user)
    return user