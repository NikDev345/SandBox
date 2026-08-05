from collections import defaultdict
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.models.execution import Executions
from app.models.tool import Tools


class HistoryService:

    @staticmethod
    def get_user_history(db: Session, user_id: str):
        """
        Returns all executions grouped by:
        - Today
        - Yesterday
        - Last 7 Days
        - Older (grouped by date)
        """

        executions = (
            db.query(Executions, Tools)
            .join(
                Tools,
                Executions.tool_id == Tools.id
            )
            .filter(
                Executions.user_id == user_id
            )
            .order_by(
                Executions.created_at.desc()
            )
            .all()
        )

        today = datetime.utcnow().date()
        yesterday = today - timedelta(days=1)
        last_week = today - timedelta(days=7)

        grouped = defaultdict(list)

        for execution, tool in executions:

            execution_date = execution.created_at.date()

            if execution_date == today:
                section = "Today"

            elif execution_date == yesterday:
                section = "Yesterday"

            elif execution_date >= last_week:
                section = "Last 7 Days"

            else:
                section = execution.created_at.strftime("%d %B %Y")

            grouped[section].append({
                "execution_id": execution.id,
                "tool_id": tool.id,
                "tool_name": tool.name,
                "tool_slug": tool.slug,
                "tool_icon": tool.icon_url,
                "user_input": execution.user_input,
                "output": execution.output,
                "created_at": execution.created_at.isoformat()
            })

        history = []

        order = [
            "Today",
            "Yesterday",
            "Last 7 Days"
        ]

        for section in order:
            if section in grouped:
                history.append({
                    "title": section,
                    "items": grouped.pop(section)
                })

        for section, items in grouped.items():
            history.append({
                "title": section,
                "items": items
            })

        return history
    @staticmethod
    def get_history_details(    
        db: Session,
        execution_id: str,
        user_id: str
    ):
        execution = (
            db.query(Executions, Tools)
            .join(
                Tools,
                Executions.tool_id == Tools.id
            )
            .filter(
                Executions.id == execution_id,
                Executions.user_id == user_id
            )
            .first()
        )

        if not execution:
            return None

        execution, tool = execution

        return {
            "execution_id": execution.id,
            "tool": {
                "id": tool.id,
                "name": tool.name,
                "slug": tool.slug,
                "icon": tool.icon_url,
                "category": tool.category,
            },
            "user_input": execution.user_input,
            "output": execution.output,
            "created_at": execution.created_at.isoformat(),
        }
    @staticmethod
    def delete_history(
        db: Session,
        execution_id: str,
        user_id: str
    ):
        execution = (
            db.query(Executions)
            .filter(
                Executions.id == execution_id,
                Executions.user_id == user_id
            )
            .first()
        )

        if not execution:
            return False

        db.delete(execution)
        db.commit()

        return True