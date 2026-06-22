from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.database.engine import get_db

from app.models.execution import ExecutionCreate
from app.utils.auth import get_current_user

from app.services.tool_executor import ExecutionService

router = APIRouter(
    prefix='/execution',
    tags=['Exec']
)

@router.post('/create')
def create_execution(data: ExecutionCreate, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    
    exec = ExecutionService.create_execution(db, current_user['sub'], data.tool_id, data.user_input, data.output)
    
    return {
        "message": "Execution created  successfully",
        "exec_id": exec.id,
        "created_by": current_user["sub"]
    }

@router.get('/{execution_id}')
def get_execution(execution_id: str, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    
    execution = ExecutionService.get_execution(
        db, execution_id
    )
    
    if not execution:
        raise HTTPException(
            status_code=404,
            detail="Execution not found"
        )
        
    return execution

@router.get("/")
def get_my_executions(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    return ExecutionService.get_user_executions(
        db,
        current_user["sub"]
    )
    
@router.get("/tool/{tool_id}")
def get_tool_executions(
    tool_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    return ExecutionService.get_tool_executions(
        db,
        tool_id
    )