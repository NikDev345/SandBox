from enum import Enum
from typing import Any, Dict, Optional
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    JSON,
    String,
)
from datetime import datetime
from pydantic import BaseModel, Field
from app.database.engine import Base

class MockAPI(Base):
    __tablename__ = "mock_apis"

    id = Column(String, primary_key=True)

    user_id = Column(
        String,
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )

    name = Column(String, nullable=False)
    description = Column(String, nullable=True)

    endpoint_token = Column(
        String,
        unique=True,
        nullable=False,
        index=True,
    )

    method = Column(String, nullable=False)

    status_code = Column(
        Integer,
        nullable=False,
        default=200,
    )

    response_body = Column(
        JSON,
        nullable=False,
    )

    response_headers = Column(
        JSON,
        nullable=False,
        default=dict,
    )

    response_delay_ms = Column(
        Integer,
        nullable=False,
        default=0,
    )

    auth_type = Column(
        String,
        nullable=False,
        default="NONE",
    )

    auth_config = Column(
        JSON,
        nullable=True,
    )

    is_active = Column(
        Boolean,
        nullable=False,
        default=True,
    )

    hit_count = Column(
        Integer,
        nullable=False,
        default=0,
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow,
    )

    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )


class HTTPMethod(str, Enum):
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    PATCH = "PATCH"
    DELETE = "DELETE"


class AuthType(str, Enum):
    NONE = "NONE"
    BEARER = "BEARER"
    API_KEY = "API_KEY"
    BASIC = "BASIC"


class AuthConfig(BaseModel):
    auth_type: AuthType = AuthType.NONE

    # Bearer Token
    bearer_token: Optional[str] = None

    # API Key
    api_key: Optional[str] = None
    api_key_header: Optional[str] = "X-API-Key"

    # Basic Authentication
    username: Optional[str] = None
    password: Optional[str] = None


class MockAPIRequest(BaseModel):
    name: str = Field(..., description="Friendly name for the mock API")

    method: HTTPMethod = HTTPMethod.GET

    status_code: int = Field(
        default=200,
        ge=100,
        le=599,
        description="HTTP status code to return"
    )

    response_body: Dict[str, Any] = Field(
        default_factory=dict,
        description="JSON response returned by the mock endpoint"
    )

    response_headers: Dict[str, str] = Field(
        default_factory=dict,
        description="Optional response headers"
    )

    response_delay_ms: int = Field(
        default=0,
        ge=0,
        description="Artificial delay before sending the response"
    )

    authentication: AuthConfig = Field(
        default_factory=AuthConfig
    )


class MockAPIResponse(BaseModel):
    success: bool
    message: str

    endpoint_token: str
    endpoint_url: str

    method: HTTPMethod
    status_code: int
    
class MockAPISummary(BaseModel):
    id: str
    name: str
    endpoint_token: str
    endpoint_url: str
    method: HTTPMethod
    status_code: int
    hit_count: int
    is_active: bool

    class Config:
        from_attributes = True
        
class MockAPIListResponse(BaseModel):
    success: bool
    total: int
    mocks: list[MockAPISummary]
    
class MockAPIDetailResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]

    endpoint_token: str
    endpoint_url: str

    method: HTTPMethod
    status_code: int

    response_body: dict
    response_headers: dict
    response_delay_ms: int

    authentication: AuthConfig

    hit_count: int
    is_active: bool

    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
        
class DeleteResponse(BaseModel):
    success: bool
    message: str