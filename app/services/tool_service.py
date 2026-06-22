from sqlalchemy.orm import Session
from app.models.tool import Tools
import uuid


class ToolService:
    
    @staticmethod
    def create_tool(db: Session, name: str, category: str):
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
            category = category
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