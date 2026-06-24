from fastapi import HTTPException

def require_admin(user):

    if user.get('role') not in ["admin"]:
        raise HTTPException(
            status_code=403,
            detail="Permission denied"
        )

    return True