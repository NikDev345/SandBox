from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.engine import get_db
from app.utils.auth import get_current_user
from app.services.user_service import UserService
from pydantic import BaseModel

class AppearanceUpdate(BaseModel):

    theme: str

    accent_color: str

    animations: str

    sidebar_mode: str

router = APIRouter(
    prefix="/user",
    tags=["User"]
)


@router.get("/profile")
def get_profile(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):

    user = UserService.get_profile(
        db,
        current_user
    )

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    return user


@router.get("/appearance")
def get_appearance(

    db: Session = Depends(get_db),

    current_user=Depends(get_current_user)

):

    user = UserService.get_profile(
        db,
        current_user
    )

    return {

        "theme": user.theme,

        "accent_color": user.accent_color,

        "animations": user.animations,

        "sidebar_mode": user.sidebar_mode

    }


@router.put("/profile")
def update_profile(
    data: dict,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):

    user = UserService.update_profile(
        db=db,
        current_user=current_user,
        name=data.get("name"),
        bio=data.get("bio")
    )

    return {
        "message": "Profile updated successfully",
        "user": user
    }


@router.put("/theme")
def update_theme(
    data: dict,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):

    user = UserService.update_theme(
        db=db,
        current_user=current_user,
        theme=data.get("theme")
    )

    return {
        "message": "Theme updated",
        "theme": user.theme
    }

@router.put("/appearance")
def update_appearance(

    data: AppearanceUpdate,

    db: Session = Depends(get_db),

    current_user=Depends(get_current_user)

):

    user = UserService.update_appearance(

        db=db,

        current_user=current_user,

        theme=data.theme,

        accent_color=data.accent_color,

        animations=data.animations,

        sidebar_mode=data.sidebar_mode

    )

    return {

        "message": "Appearance updated",

        "appearance": {

            "theme": user.theme,

            "accent_color": user.accent_color,

            "animations": user.animations,

            "sidebar_mode": user.sidebar_mode

        }

    }
    
    
@router.put("/avatar")
def update_avatar(
    data: dict,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):

    user = UserService.update_avatar(
        db=db,
        current_user=current_user,
        avatar_url=data.get("avatar_url")
    )

    return {
        "message": "Avatar updated",
        "avatar": user.avatar_url
    }