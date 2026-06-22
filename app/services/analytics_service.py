from sqlalchemy.orm import Session
from app.models.analytics import Analytics
import uuid

class AnalyticService:
    
    @staticmethod
    def post_analytic(db: Session, tool_id: str, event_type: str):
        
        analysis = Analytics(
            id = str(uuid.uuid4()),
            tool_id = tool_id,
            event_type=event_type
        ) 
        
        db.add(analysis)
        db.commit()
        db.refresh(analysis)
        
        return analysis
    

    @staticmethod
    def get_all_analytics(db: Session):
        return db.query(Analytics).all()
    
    @staticmethod
    def get_analytics_by_tool(db: Session, tool_id: str):
        return (
            db.query(Analytics).filter(Analytics.tool_id == tool_id).all()
        )