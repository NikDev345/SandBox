from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field

class GenerationMode(str, Enum):
    AI = "ai"
    BUILDER = "builder"


class LogicalOperator(str, Enum):
    AND = "AND"
    OR = "OR"


class SortDirection(str, Enum):
    ASC = "ASC"
    DESC = "DESC"
    
class SQLDialect(str, Enum):
    MYSQL = "mysql"
    POSTGRESQL = "postgresql"
    SQLITE = "sqlite"
    SQLSERVER = "sqlserver"
    ORACLE = "oracle"
    
class QueryType(str, Enum):
    SELECT = "SELECT"
    INSERT = "INSERT"
    UPDATE = "UPDATE"
    DELETE = "DELETE"


class JoinType(str, Enum):
    INNER = "INNER"
    LEFT = "LEFT"
    RIGHT = "RIGHT"
    FULL = "FULL"
    
class ExecutionCost(BaseModel):
    label: str          # Low, Medium, High
    score: int          # 0–100
    factors: List[str]  # Reasons contributing to the score


class Condition(BaseModel):
    field: str = Field(..., description="Column name")
    operator: str = Field(..., description="=, >, <, >=, <=, LIKE, IN, etc.")
    value: str = Field(..., description="Comparison value")
    logical_operator: Optional[LogicalOperator] = Field(
        default=LogicalOperator.AND,
        description="Relationship with the next condition"
    )


class Join(BaseModel):
    join_type: JoinType
    table: str
    left_column: str
    operator: str = Field(
    default="=",
    description="Join operator"
)
    right_column: str


class Sort(BaseModel):
    field: str
    direction: SortDirection = SortDirection.ASC


class VisualBuilder(BaseModel):

    query_type: QueryType = QueryType.SELECT

    database: Optional[str] = None

    table: str

    columns: List[str] = Field(default_factory=list)

    conditions: List[Condition] = Field(default_factory=list)

    joins: List[Join] = Field(default_factory=list)

    group_by: List[str] = Field(default_factory=list)

    having: List[Condition] = Field(default_factory=list)

    sort: List[Sort] = Field(default_factory=list)

    limit: Optional[int] = Field(default=None, ge=1)


class SQLGeneratorRequest(BaseModel):
    mode: GenerationMode

    prompt: Optional[str] = Field(
        default=None,
        description="Natural language query when mode='ai'"
    )

    builder: Optional[VisualBuilder] = Field(
        default=None,
        description="Visual Builder data when mode='builder'"
    )

    dialect: SQLDialect = SQLDialect.MYSQL
    
class SQLGeneratorResponse(BaseModel):
    success: bool

    sql: str    
    query_type: str

    tables: List[str]

    complexity: str

    execution_cost: ExecutionCost

    formatted_sql: Optional[str] = None