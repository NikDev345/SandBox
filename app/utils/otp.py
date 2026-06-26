from passlib.context import CryptContext
import secrets

pwd_context = CryptContext(
    schemes=['bcrypt'],
    deprecated='auto'
)

def generate_otp():
    otp = secrets.randbelow(900000) + 100000
    return str(otp)

def hash_otp(otp):
    return pwd_context.hash(otp)

def verify_otp(plain_otp, hash_otp):
    return pwd_context.verify(
     plain_otp, hash_otp   
    )