from sqlalchemy.orm import Session
from app.models.execution import Executions
import uuid

class ExecutionService:
    
    @staticmethod
    def create_execution(db: Session, user_id: str, tool_id: str, user_input: str, output: str):
        
        execution = Executions(
            id = str(uuid.uuid4()),
            user_id = user_id,
            tool_id = tool_id,
            user_input = user_input,
            output = output
        )
        
        db.add(execution)
        db.commit()
        db.refresh(execution)
        
        return execution
    
    @staticmethod
    def get_execution(
        db: Session,
        execution_id: str
    ):
        return (
            db.query(Executions)
            .filter(Executions.id == execution_id)
            .first()
        )
        
    @staticmethod
    def get_user_executions(
        db: Session,
        user_id: str
    ):
        return (
            db.query(Executions)
            .filter(
                Executions.user_id == user_id
            )
            .all()
        )
        
    @staticmethod
    def get_tool_executions(
        db: Session,
        tool_id: str
    ):
        return (
            db.query(Executions)
            .filter(
                Executions.tool_id == tool_id
            )
            .all()
        )
        
    @staticmethod
    def get_all_executions(db: Session):
        return db.query(Executions).all()
    
    @staticmethod
    def get_execution_count(db: Session):
        return db.query(Executions).count()