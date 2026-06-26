
from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.orm import Session
from fastapi.responses import JSONResponse

from app.database.engine import get_db
from app.models.user import UserCreate, UserLogin
from app.services.auth_service import AuthService
from app.utils.jwt import create_access_token
from app.utils.auth import get_current_user

from app.models.otp import SendOTPRequest, VerifyOTPRequest, ResendOTPRequest
from app.models.password_reset import ForgotPasswordRequest, ResetPasswordRequest


from app.services.password_reset_service import PasswordResetService
from app.services.otp_service import OTPService
from app.utils.security import hash_password

router = APIRouter(
    prefix="/auth",
    tags=["Auth"]
)


@router.post("/send-otp")
def signsend_signup_otpup(
    data: SendOTPRequest,
    db: Session = Depends(get_db)
):
    result = OTPService.send_signup_otp(
        db=db,
        name=data.name.strip(),
        email=data.email,
        hash_password=hash_password(data.password)
    )
    
    if result is None:
        raise HTTPException(
            status_code=400,
            detail="Email already exists"
        )

    if result is False:
        raise HTTPException(
            status_code=500,
            detail="Failed to send OTP"
        )

    return {
        "message": "OTP sent successfully"
    }
    
@router.post("/verify-otp")
def verify_signup_otp(
    data: VerifyOTPRequest,
    db: Session = Depends(get_db)
):

    user = OTPService.verify_signup_otp(
        db=db,
        email=data.email,
        otp=data.otp
    )

    if user is None:
        raise HTTPException(
            status_code=404,
            detail="OTP not found"
        )

    if user is False:
        raise HTTPException(
            status_code=400,
            detail="Invalid or expired OTP"
        )

    token = create_access_token(
        {
            "sub": user.id,
            "email": user.email,
            "role": user.role
        }
    )

    return {
        "message": "Account created successfully",
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "role": user.role
        }
    }
    
@router.post("/resend-otp")
def resend_signup_otp(
    data: ResendOTPRequest,
    db: Session = Depends(get_db)
):

    result = OTPService.resend_signup_otp(
        db=db,
        email=data.email
    )

    if result is None:
        raise HTTPException(
            status_code=404,
            detail="OTP request not found"
        )

    if result is False:
        raise HTTPException(
            status_code=500,
            detail="Failed to resend OTP"
        )

    return {
        "message": "OTP sent successfully"
    }

@router.post("/forgot-password")
def forgot_password(
    data: ForgotPasswordRequest,
    db: Session = Depends(get_db)
):

    result = PasswordResetService.create_reset_token(
        db=db,
        email=data.email
    )

    if result is None:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    if result is False:
        raise HTTPException(
            status_code=500,
            detail="Failed to send reset email"
        )

    return {
        "message": "Password reset email sent successfully."
    }
    
@router.post("/reset-password")
def reset_password(
    data: ResetPasswordRequest,
    db: Session = Depends(get_db)
):

    user = PasswordResetService.reset_password(
        db=db,
        token=data.token,
        password=data.password
    )

    if user is None:
        raise HTTPException(
            status_code=404,
            detail="Invalid reset token"
        )

    if user is False:
        raise HTTPException(
            status_code=400,
            detail="Reset token has expired"
        )

    return {
        "message": "Password updated successfully."
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
         "email": user.email,
         'role': user.role}
        
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

@router.post("/logout")
def logout():
    response = JSONResponse(
        content={"message": "Logged out successfully"}
    )

    response.delete_cookie(
        key="access_token",
        path="/"
    )
    response.delete_cookie("access_token", path="/")
    response.delete_cookie("token", path="/")

    return response