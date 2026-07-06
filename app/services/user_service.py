from sqlalchemy.orm import Session

from app.models.user import Users


class UserService:

    @staticmethod
    def get_profile(
        db: Session,
        current_user: dict
    ):

        return db.query(
            Users
        ).filter(
            Users.id == current_user["sub"]
        ).first()

    @staticmethod
    def update_profile(
        db: Session,
        current_user: dict,
        name: str,
        bio: str = None
    ):

        user = db.query(
            Users
        ).filter(
            Users.id == current_user["sub"]
        ).first()

        if not user:
            return None

        # Always update local profile
        user.local_name = name
        user.name = name
        user.name_customized = True
        
        if hasattr(user, "bio"):
            user.bio = bio

        # Update displayed profile only if no OAuth provider is connected
        if not user.google_connected and not user.github_connected:
            user.name = user.local_name

        db.commit()
        db.refresh(user)

        return {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "role": user.role,
            "provider": user.provider,
            "avatar": user.avatar_url,
            "bio": user.bio,
            "created_at": user.created_at.isoformat()
        }

    @staticmethod
    def update_theme(
        db: Session,
        current_user: dict,
        theme: str
    ):

        user = db.query(
            Users
        ).filter(
            Users.id == current_user["sub"]
        ).first()

        if not user:
            return None

        user.theme = theme

        db.commit()

        return user
    
    
    
    @staticmethod
    def update_appearance(
        db: Session,
        current_user: dict,
        theme: str,
        accent_color: str,
        animations: str,
        sidebar_mode: str
    ):

        user = db.query(Users).filter(
            Users.id == current_user["sub"]
        ).first()

        if not user:
            return None

        user.theme = theme
        user.accent_color = accent_color
        user.animations = animations
        user.sidebar_mode = sidebar_mode

        db.commit()
        db.refresh(user)

        return user



    @staticmethod
    def update_avatar(
        db: Session,
        current_user: dict,
        avatar_url: str
    ):

        user = db.query(
            Users
        ).filter(
            Users.id == current_user["sub"]
        ).first()

        if not user:
            return None

        user.avatar_url = avatar_url

        db.commit()

        db.refresh(user)

        return user
    