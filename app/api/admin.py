from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from app.database.engine import get_db
from app.utils.auth import get_current_user
from app.utils.permissions import require_admin
from datetime import datetime, timezone, timedelta

# Import your models — adjust paths if needed
from app.models.user import Users
from app.models.tool import Tools
from app.models.execution import Executions, to_ist

router = APIRouter(
    prefix="/admin",
    tags=["Admin"]
)
IST = timezone(timedelta(hours=5, minutes=30))

def _to_ist_str(value):
    if value is None:
        return None
    if isinstance(value, str):
        # Parse the string first
        try:
            dt = datetime.fromisoformat(value)
        except ValueError:
            return value  # return as-is if unparseable
    else:
        dt = value
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(IST).isoformat()

def _admin_user(current_user=Depends(get_current_user)):
    """Dependency: resolves current user AND enforces admin role."""
    require_admin(current_user)
    return current_user


# ── GET /admin/stats ──────────────────────────────────────────
# Returns headline counts for the admin dashboard cards.

@router.get("/stats")
def get_admin_stats(
    db: Session = Depends(get_db),
    current_user=Depends(_admin_user)
):
    total_users      = db.query(func.count(Users.id)).scalar() or 0
    total_tools      = db.query(func.count(Tools.id)).scalar() or 0
    total_executions = db.query(func.count(Executions.id)).scalar() or 0

    return {
        "total_users":      total_users,
        "total_tools":      total_tools,
        "total_executions": total_executions,
    }


# ── GET /admin/executions ─────────────────────────────────────
# Full execution log with joined user e-mail and tool name.
# Supports ?limit=&offset= for basic pagination.

@router.get("/executions")
def get_all_executions(
    limit:  int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user=Depends(_admin_user)
):
    rows = (
        db.query(
            Executions.id,
            Executions.tool_id,
            Executions.user_id,
            Executions.created_at,
            Executions.user_input,
            Executions.output,
            Users.email.label("user_email"),
            Tools.name.label("tool_name"),
        )
        .outerjoin(Users, Users.id == Executions.user_id)
        .outerjoin(Tools, Tools.id == Executions.tool_id)
        .order_by(desc(Executions.created_at))
        .limit(limit)
        .offset(offset)
        .all()
    )

    total = db.query(func.count(Executions.id)).scalar() or 0

    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "executions": [
            {
                "exec_id":    r.id,
                "tool_id":    r.tool_id,
                "tool_name":  r.tool_name  or "—",
                "user_id":    r.user_id,
                "user_email": r.user_email or "—",
                "timestamp": _to_ist_str(r.created_at),
            }
            for r in rows
        ],
    }


# ── GET /admin/tool-views ─────────────────────────────────────
# How many times each tool has been executed, sorted by most used.

@router.get("/tool-views")
def get_tool_views(
    db: Session = Depends(get_db),
    current_user=Depends(_admin_user)
):
    rows = (
        db.query(
            Tools.id,
            Tools.name,
            Tools.category,
            func.count(Executions.id).label("execution_count"),
        )
        .outerjoin(Executions, Executions.tool_id == Tools.id)
        .group_by(Tools.id, Tools.name, Tools.category)
        .order_by(desc("execution_count"))
        .all()
    )

    return {
        "tools": [
            {
                "tool_id":         r.id,
                "tool_name":       r.name,
                "category":        r.category,
                "execution_count": r.execution_count,
            }
            for r in rows
        ]
    }


# ── GET /admin/users ──────────────────────────────────────────
# Light user list (no passwords) for potential future use.

@router.get("/users")
def get_all_users(
    limit:  int = 100,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user=Depends(_admin_user)
):
    users = (
        db.query(Users)
        .order_by(desc(Users.created_at))
        .limit(limit)
        .offset(offset)
        .all()
    )
    total = db.query(func.count(Users.id)).scalar() or 0

    return {
        "total": total,
        "users": [
            {
                "id":         u.id,
                "name":       u.name,
                "email":      u.email,
                "role":       u.role,
                "provider":   u.provider,
                "created_at": u.created_at.isoformat() if u.created_at else None,
            }
            for u in users
        ],
    }