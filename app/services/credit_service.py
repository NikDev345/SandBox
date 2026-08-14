# app/services/credit_service.py

from datetime import datetime
from app.models.user import Users
from fastapi import HTTPException
CREDIT_COST = 20

def check_user_credits(user: Users):
    return user.free_credits_remaining >= CREDIT_COST

def reset_credits_if_needed(user: Users):
    today = datetime.utcnow().date()

    if user.last_credit_reset != today:
        user.free_credits_remaining = user.free_credits_total
        user.last_credit_reset = today
        return True

    return False
        
def enforce_credit_limit(db, user_id: str):
    user = db.query(Users).filter(Users.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )
    # reset
    if reset_credits_if_needed(user):
        db.commit()

    # check
    if user.free_credits_remaining < CREDIT_COST:
        raise HTTPException(
            status_code=403,
            detail="You have no credits remaining. Please try again tomorrow."
        )

    return user