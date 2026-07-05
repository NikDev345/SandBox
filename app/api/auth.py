
from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.orm import Session
from fastapi.responses import JSONResponse

from app.database.engine import get_db
from app.models.user import Users, UserLogin, UpdatePasswordRequest, DeleteConfirmation
from app.services.auth_service import AuthService
from app.utils.jwt import create_access_token
from app.utils.auth import get_current_user
from app.utils.security import verify_password
from app.models.otp import SendOTPRequest, VerifyOTPRequest, ResendOTPRequest
from app.models.password_reset import ForgotPasswordRequest, ResetPasswordRequest
from app.models.password_otp import (
    PasswordOTP,
    PasswordOTPRequest,
    VerifyPasswordOTPRequest,
    ChangePasswordRequest
)

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

@router.put('/update_password')
def update_password(data: UpdatePasswordRequest, db: Session = Depends(get_db), current_user: Session = Depends(get_current_user)):
    user = AuthService.update_password(db, current_user, data.new_password, data.current_password)
    if user is None:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )
    if user is False:
        raise HTTPException(
            status_code=401,
            detail="Current password is incorrect"
        )
    if user == 'same_password':
        raise HTTPException(
            status_code=400,
            detail="New password must be different from the current password."
        )
    return {
        "message": "Password updated successfully."
    }
    
@router.post("/send-password-otp")
def send_password_otp(
    data: PasswordOTPRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):

    user = db.query(Users).filter(
        Users.id == current_user["sub"]
    ).first()

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    if user.email != data.email:
        raise HTTPException(
            status_code=403,
            detail="Invalid email"
        )

    result = OTPService.send_password_otp(
        db,
        data.email
    )

    if result is None:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    if result is False:
        raise HTTPException(
            status_code=500,
            detail="Failed to send OTP"
        )

    return {
        "message": "OTP sent successfully"
    }
    
@router.post("/verify-password-otp")
def verify_password_otp(
    data: VerifyPasswordOTPRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):

    user = db.query(Users).filter(
        Users.id == current_user["sub"]
    ).first()

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    if user.email != data.email:
        raise HTTPException(
            status_code=403,
            detail="Invalid email"
        )

    result = OTPService.verify_password_otp(
        db,
        data.email,
        data.otp
    )

    if result is None:
        raise HTTPException(
            status_code=404,
            detail="OTP not found"
        )

    if result is False:
        raise HTTPException(
            status_code=400,
            detail="Invalid or expired OTP"
        )

    return {
        "message": "OTP verified"
    }
    
@router.put("/change-password")
def change_password(
    data: ChangePasswordRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):

    record = db.query(PasswordOTP).filter(
        PasswordOTP.email == data.email,
        PasswordOTP.verified == True
    ).first()

    if not record:
        raise HTTPException(
            status_code=403,
            detail="Verify OTP first"
        )

    user = db.query(Users).filter(
        Users.id == current_user["sub"]
    ).first()
    
    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )
        
    if data.new_password != data.confirm_password:
        raise HTTPException(
            status_code=400,
            detail="Passwords do not match."
        )
        
    if verify_password(
        data.new_password,
        user.password_hash
    ):
        raise HTTPException(
            status_code=400,
            detail="New password must be different from the current password."
        )

    user.password_hash = hash_password(
        data.new_password
    )

    db.delete(record)

    db.commit()

    return {
        "message": "Password updated successfully"
    }
    
@router.delete('/account')
def delete_account(data: DeleteConfirmation, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    user = db.query(Users).filter(
        Users.id == current_user["sub"]
    ).first()

    expected = f"DELETE {user.name}"

    if data.confirmation_text != expected:
        raise HTTPException(
            status_code=400,
            detail="Confirmation text does not match."
        )

    db.delete(user)
    db.commit()

    response = JSONResponse(
        content={
            "message": "Account deleted successfully."
        }
    )

    response.delete_cookie(
        key="access_token",
        path="/"
    )

    response.delete_cookie(
        key="token",
        path="/"
    )

    return response
    
@router.get('/confirm-delete')
def confirm_delete(db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    
    user = db.query(Users).filter(
        Users.id == current_user["sub"]
    ).first() 
    
    return {
        "confirmation_text": f"DELETE {user.name}"
    }