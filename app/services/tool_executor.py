from sqlalchemy.orm import Session
from app.models.execution import Executions
from app.models.user import Users
from app.services.credit_service import check_user_credits, reset_credits_if_needed
import uuid

class ExecutionService:
    
    @staticmethod
    def create_execution(db: Session, user_id: str, tool_id: str, user_input: str, output: str):

        CREDIT_COST = 20

        user = (
            db.query(Users)
            .filter(Users.id == user_id)
            .with_for_update()
            .first()
        )
        if not user:
            raise Exception("User not found")

        # 1. RESET + CHECK
        if reset_credits_if_needed(user):
            db.flush()

        if not check_user_credits(user):
            raise Exception("Insufficient credits")

        # 2. DEDUCT
        user.free_credits_remaining -= CREDIT_COST

        # 3. CREATE EXECUTION
        execution = Executions(
            id=str(uuid.uuid4()),
            user_id=user_id,
            tool_id=tool_id,
            user_input=user_input,
            output=output
        )

        db.add(execution)

        # 4. SINGLE COMMIT (important)
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