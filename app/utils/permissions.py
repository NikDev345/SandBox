from fastapi import HTTPException

def require_admin(user):

    if user.role not in ["admin"]:
        raise HTTPException(
            status_code=403,
            detail="Permission denied"
        )

    return True