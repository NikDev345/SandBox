from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.database.engine import get_db

from app.models.analytics import AnalyticCreate
from app.services.analytics_service import AnalyticService

router = APIRouter(
    prefix='/analytics',
    tags=['Analysis']
)

@router.post('/create')
def create_analysis(db: Session = Depends(get_db), data= AnalyticCreate):
    
    analysis = AnalyticService.post_analytic(db, data.tool_id, data.event_type)
    
    return {
        "message": "Analysis created successfully",
        "Analysis_id": analysis.id,
        "done_by": analysis.tool_id
    }
    
@router.get('/')
def get_all_users(db: Session = Depends(get_db)):
    
    return AnalyticService.get_all_analytics(db)

@router.get('/{tool_id}')
def get_analysis_by_tool(tool_id: str, db: Session = Depends(get_db)):
    return AnalyticService.get_analytics_by_tool(db, tool_id)