from sqlalchemy.orm import Session
from app.models.tool import Tools
import uuid


class ToolService:
    
    @staticmethod
    def create_tool(db: Session, name: str, category: str, description: str, icon_url: str, source_path: str):
        slug = name.strip().upper().replace(' ', '-')
        existing_tool = (
            db.query(Tools).filter(Tools.slug == slug).first()
        )
        
        if existing_tool:
            return None
        
        tool = Tools(
            id = str(uuid.uuid4()),
            name = name,
            slug = slug,
            description = description,
            category = category,
            icon_url = icon_url,
            source_path = source_path
        )
        
        db.add(tool)
        db.commit()
        db.refresh(tool)
        
        return tool

    @staticmethod
    def return_tool(db: Session, id: str):
        tool = db.query(Tools).filter(Tools.id == id).first()
        
        if not tool:
            return None
        
        return tool
    
    @staticmethod
    def get_tool_count(db: Session):
        return db.query(Tools).count()
    
    @staticmethod
    def get_tool_by_slug(db: Session, slug: str):
        return (
            db.query(Tools)
            .filter(Tools.slug == slug)
            .first()
         )