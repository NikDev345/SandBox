from sqlalchemy.orm import Session

from app.models.user import Users
from app.models.tool import Tools
from app.models.execution import Executions
from datetime import datetime, timedelta

class WorkspaceService:

    @staticmethod
    def get_workspace(
        db: Session,
        user_id: str,
    ):
        """
        Returns all information required by the Workspace section
        on the dashboard.
        """

        # Current user
        user = (
            db.query(Users)
            .filter(Users.id == user_id)
            .first()
        )
        if not user:
            raise ValueError("User not found.")
        
        # Total tools available
        total_tools = (
            db.query(Tools)
            .count()
        )

        # Total executions by current user
        total_executions = (
            db.query(Executions)
            .filter(
                Executions.user_id == user_id
            )
            .count()
        )

        # Today's UTC range
        today_start = datetime.utcnow().replace(
            hour=0,
            minute=0,
            second=0,
            microsecond=0
        )

        tomorrow_start = today_start + timedelta(days=1)

        # Count today's executions
        today_executions = (
            db.query(Executions)
            .filter(
                Executions.user_id == user_id,
                Executions.created_at >= today_start,
                Executions.created_at < tomorrow_start
            )   
            .count()
        )
        
        # Daily reset logic
        today = datetime.utcnow().date()

        if user.last_credit_reset != today:
            user.free_credits_remaining = user.free_credits_total
            user.last_credit_reset = today
            db.commit()
        
        
        return {
            "name": user.name,
            "email": user.email,
            "avatar": user.avatar_url,

            "total_tools": total_tools,
            "executions": total_executions,

            "daily_credits": {
                "remaining": user.free_credits_remaining,
                "used": user.free_credits_total - user.free_credits_remaining,
                "limit": user.free_credits_total,
                "executions_today": today_executions,
            }
        }