from sqlalchemy.orm import Session
from app.models.tool import Tools
import uuid


class ToolService:

    @staticmethod
    def create_tool(
        db: Session,
        name: str,
        category: str,
        description: str,
        icon_url: str,
        source_path: str,
        slug: str | None = None,
    ):
        """
        Create a new tool if it does not already exist.
        """

        slug = slug or name.strip().upper().replace(" ", "-")

        existing_tool = (
            db.query(Tools)
            .filter(Tools.slug == slug)
            .first()
        )

        if existing_tool:
            return existing_tool

        tool = Tools(
            id=str(uuid.uuid4()),
            name=name,
            slug=slug,
            description=description,
            category=category,
            icon_url=icon_url,
            source_path=source_path,
        )

        db.add(tool)
        db.commit()
        db.refresh(tool)

        return tool

    @staticmethod
    def return_tool(db: Session, id: str):
        """
        Get tool by ID.
        """

        return (
            db.query(Tools)
            .filter(Tools.id == id)
            .first()
        )

    @staticmethod
    def get_tool_count(db: Session):
        """
        Return total number of tools.
        """

        return db.query(Tools).count()

    @staticmethod
    def get_tool_by_slug(db: Session, slug: str):
        """
        Get tool by slug.
        """

        return (
            db.query(Tools)
            .filter(Tools.slug == slug)
            .first()
        )

    @staticmethod
    def get_all_tools(db: Session):
        """
        Return all registered tools.
        """

        return (
            db.query(Tools)
            .order_by(Tools.name.asc())
            .all()
        )