from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.models.user import Users
from app.models.otp import EmailOTP

from app.utils.otp import generate_otp, hash_otp, verify_otp
from app.services.email_service import send_otp_email

import uuid

class OTPService:
    
    @staticmethod
    def send_signup_otp(db:Session, email: str, name: str, hash_password: str):
        
        existing_user = db.query(Users).filter(Users.email == email).first()
        
        if existing_user:
            return None
        
        db.query(EmailOTP).filter(EmailOTP.email == email).delete()
        
        
        new_otp = generate_otp()
        hashed_otp = hash_otp(new_otp)
        
        expires_at = datetime.utcnow() + timedelta(minutes=5)
        
        otp = EmailOTP(
            email=email,
            name=name,
            hash_password=hash_password,
            hash_otp=hashed_otp,
            expires_at=expires_at,
            created_at=datetime.utcnow()
        )
        
        db.add(otp)
        db.commit()
        
        sent = send_otp_email(email, new_otp)
        
        if not sent:
            db.delete(otp)
            db.commit()
            return False
        
        return True
    
    @staticmethod
    def verify_signup_otp(db: Session, email: str, otp: str):
    
        otp_record = db.query(EmailOTP).filter(EmailOTP.email == email).first()
        
        if not otp_record:
            return None
        
        curr_time = datetime.utcnow()
        
        if curr_time > otp_record.expires_at:
            db.delete(otp_record)
            db.commit()
            return False
        
        verified = verify_otp(otp, otp_record.hash_otp)
        
        if verified:
            user = Users(
                id = str(uuid.uuid4()),
                name=otp_record.name,
                email=otp_record.email,
                password_hash=otp_record.hash_password,
                provider='local'
            )
            
            db.add(user)
            db.delete(otp_record)
            db.commit()
            db.refresh(user)
            return user
        else:
            return False
        
    @staticmethod
    def resend_signup_otp(
        db: Session,
        email: str
    ):

        otp_record = (
            db.query(EmailOTP)
            .filter(EmailOTP.email == email)
            .first()
        )

        if not otp_record:
            return None

        new_otp = generate_otp()

        otp_record.hash_otp = hash_otp(new_otp)
        otp_record.expires_at = datetime.utcnow() + timedelta(minutes=5)

        sent = send_otp_email(
            email,
            new_otp
        )

        if not sent:
            return False

        db.commit()

        return True