from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database.engine import get_db
from app.models.user import Users, UserCreate, UserResponse, UserLogin
import uuid

router = APIRouter(prefix="/auth", tags=["Auth"])

@router.post('/signup')
def signup(data: UserCreate, db: Session = Depends(get_db)):
    pass

@router.post('login')
def login(data: UserLogin, db: Session = Depends(get_db)):
    pass