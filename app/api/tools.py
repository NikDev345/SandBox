from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.services.tool_service import ToolService
from app.utils.auth import get_current_user
from app.database.engine import get_db
from app.utils.permissions import require_admin
from app.models.tool import ToolCreate

router = APIRouter(
    prefix='/tool',
    tags=['Tools']
)

@router.post('/create')
def create_tool(data: ToolCreate, db: Session = Depends(get_db), current_user= Depends(get_current_user)):
    require_admin(current_user)
    tool = ToolService.create_tool(db, data.name, data.category, data.description, data.icon_url, data.source_path )
    
    if not tool:
        raise HTTPException(
            status_code=400,
            detail="Name already exists"
        )
        
    return {
        "message": "Tool created successfully",
        "tool_id": tool.id,
        "created_by": current_user["sub"]
    }
    
@router.get('/{tool_id}')
def get_tool(tool_id: str, db: Session = Depends(get_db)):
    
    tool = ToolService.return_tool(
        db,
        tool_id
    )
    
    if not tool:
        raise HTTPException(
            status_code=404,
            detail="Tool not found"
        )
        
    return tool
    
@router.get('/count')
def get_tool_count(db: Session = Depends(get_db)):
    return ToolService.get_tool_count(db)