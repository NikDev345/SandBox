from app.models.api_mock import MockAPIRequest, DeleteResponse, AuthType,MockAPIResponse, MockAPI, HTTPMethod, MockAPIListResponse, MockAPISummary, MockAPIDetailResponse, AuthConfig
import secrets, string, base64, asyncio
from uuid import uuid4
from sqlalchemy.orm import Session
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse

class MockAPIService:
    BASE_URL='http://127.0.0.1:8000'
    @staticmethod
    def _validate_request(request: MockAPIRequest):
        if not request.name or not request.name.strip():
            raise ValueError("Name cannot be empty")
        
        if request.response_body is None or not isinstance(request.response_body, dict):
            raise ValueError(
                "response_body must be a valid JSON Object"
            )
            
        if request.response_delay_ms < 0:
            raise ValueError(
                "Response delay cannot be negative"
            )

        # Validate authentication configuration
        auth = request.authentication
        
        if auth.auth_type == AuthType.NONE:
            return
        
        elif auth.auth_type == AuthType.BEARER:
            if not auth.bearer_token or not auth.bearer_token.strip():
                raise ValueError(
                    "Bearer token is required"
                )
                
        elif auth.auth_type == AuthType.API_KEY:
            if not auth.api_key or not auth.api_key.strip():
                raise ValueError(
                    "API Key is required!"
                )
                
            if not auth.api_key_header or not auth.api_key_header.strip():
                raise ValueError(
                    "API Key Header is required"
                )
                
        elif auth.auth_type == AuthType.BASIC:
            if not auth.username or not auth.username.strip():
                raise ValueError(
                    "Username is required"
                )
                
            if not auth.password or not auth.password.strip():
                raise ValueError(
                    "Password is required"
                )
                
        else:
            raise ValueError(
                f"Unsupported Authentication type: {auth}"
            )
            
    @staticmethod
    def _generate_endpoint_token(length: int = 12):
        characters = string.ascii_letters + string.digits
        return "".join(secrets.choice(characters) for _ in range(length))
    
    @staticmethod
    def _build_mock_entity(request: MockAPIRequest, endpoint_token: str, user_id: str):
        return MockAPI(
            id=str(uuid4()),
            user_id=user_id,

            name=request.name.strip(),
            description=None,

            endpoint_token=endpoint_token,

            method=request.method.value,
            status_code=request.status_code,

            response_body=request.response_body,
            response_headers=request.response_headers,
            response_delay_ms=request.response_delay_ms,

            auth_type=request.authentication.auth_type.value,
            auth_config=request.authentication.model_dump(),

            is_active=True,
            hit_count=0,
        )
        
    @staticmethod
    def _save_mock(db: Session, mock: MockAPI):
        db.add(mock)
        db.commit()
        db.refresh(mock)
        
        return mock
    
    @staticmethod
    def _build_response(mock: MockAPI) -> MockAPIResponse:
        
        return MockAPIResponse(
            success=True,
            message="Mock API created successfully.",
            endpoint_token=mock.endpoint_token,
            endpoint_url=f"{MockAPIService.BASE_URL}/mock/{mock.endpoint_token}",
            method=HTTPMethod(mock.method),
            status_code=mock.status_code,
        )
# ----------------------------------------------------------------------------------------------------------------------------------- 
    @staticmethod
    def create_mock_api(db: Session, request: MockAPIRequest, user_id: str, user=None) -> MockAPIResponse:
        MockAPIService._validate_request(request)

        endpoint_token = MockAPIService._generate_endpoint_token()

        mock = MockAPIService._build_mock_entity(
            request=request,
            endpoint_token=endpoint_token,
            user_id=user_id,
        )

        saved_mock = MockAPIService._save_mock(
            db=db,
            mock=mock,
        )

        return MockAPIService._build_response(saved_mock)
# -------------------------------------------------------------------------------------------------------------------------------------
    
    @staticmethod
    def _find_mock_by_token(db: Session, token: str):
        
        existing_mock = db.query(MockAPI).filter(MockAPI.endpoint_token==token).first()
        
        if not existing_mock:
            raise ValueError(
                "No Mock API found!"
            )
            
        if not existing_mock.is_active:
            raise ValueError(
                "Mock API is disabled"
            )
            
        return existing_mock
    
    @staticmethod
    def _validate_method(mock: MockAPI, request_method: str):
        if mock.method != request_method.upper():
            raise ValueError(
                "Method not allowed!"
            )
            
    @staticmethod
    def _authenticate_request(mock: MockAPI, request: Request):
        auth_type = AuthType(mock.auth_type)
        auth_config = mock.auth_config or {}
        
        if auth_type == AuthType.NONE:
            return
        
        elif auth_type == AuthType.BEARER:
            authorization = request.headers.get("Authorization")
            expected = f"Bearer {auth_config.get('bearer_token')}"
            
            if authorization != expected:
                raise HTTPException(
                    status_code=401,
                    detail="Invalid Bearer token"
                )
                
            return 
        
        elif auth_type == AuthType.API_KEY:
            header_name = auth_config.get('api_key_header', "X-API-Key")
            expected_key = auth_config.get('api_key')
            
            received_key = request.headers.get(header_name)
            
            if received_key != expected_key:
                raise HTTPException(
                    status_code=402,
                    detail="Invalid API Key"
                )
                
            return
        
        elif auth_type == AuthType.BASIC:
            authorization = request.headers.get("Authorization")
            
            if not authorization or not authorization.startswith('Basic '):
                raise HTTPException(
                    status_code=403,
                    detail="Invalid Basic Authentication"
                )
                
            try:
                encoded = authorization.split("  ", 1)[1]
                decoded = base64.b64decode(encoded).decode("utf-8")
                username, password = decoded.split(": ", 1)
                
            except Exception:
                raise HTTPException(
                    status_code=403,
                    detail="Invalid Basic Authentication"
                )
                
            if (
                username != auth_config.get('username') or
                password != auth_config.get('password')
            ):
                raise HTTPException(
                    status_code=500,
                    detail="Invalid username or password"
                )
                
            return
        
        raise HTTPException(
            status_code=408,
            detail=f"Unsupported authentication type: {auth_type}"
        )
        
    @staticmethod
    async def _apply_delay(mock: MockAPI):
        delay = mock.response_delay_ms
        if delay == 0:
            return 
        
        await asyncio.sleep(delay/1000)
        
    @staticmethod
    def _increment_hit_count(db: Session, mock: MockAPI):
        mock.hit_count += 1
        
        db.commit()
        db.refresh(mock)
        
    @staticmethod
    def _build_json_response(mock: MockAPI):
        
        return JSONResponse(
            content=mock.response_body,
            status_code=mock.status_code,
            headers=mock.response_headers
        ) 
        
    @staticmethod
    async def execute_mock(db: Session, token: str, request: Request, user=None):
        mock = MockAPIService._find_mock_by_token(db, token)
        MockAPIService._validate_method(mock, request_method=request.method)
        MockAPIService._authenticate_request(mock, request)
        await MockAPIService._apply_delay(mock)
        response = MockAPIService._build_json_response(mock)
        
        try:
            MockAPIService._increment_hit_count(db, mock)
        except Exception:
            pass
        
        return response
        
    @staticmethod
    def list_mock_apis(db: Session, user_id: str) -> MockAPIListResponse:
        """
        Retrieve all mock APIs for a user.
        """

        mocks = (
            db.query(MockAPI)
            .filter(MockAPI.user_id == user_id)
            .order_by(MockAPI.created_at.desc())
            .all()
        )

        response_list = [
            MockAPISummary(
                id=mock.id,
                name=mock.name,
                endpoint_token=mock.endpoint_token,
                endpoint_url=f"/mock/{mock.endpoint_token}",
                method=HTTPMethod(mock.method),
                status_code=mock.status_code,
                hit_count=mock.hit_count,
                is_active=mock.is_active,
            )
            for mock in mocks
        ]

        return MockAPIListResponse(
            success=True,
            total=len(mocks),
            mocks=response_list,
        )
        
    @staticmethod
    def get_mock_api(
        db: Session,
        mock_id: str,
        user_id: str,
    ) -> MockAPIDetailResponse:
        """
        Retrieve a single mock API owned by the given user.
        """

        # Find the mock
        mock = (
            db.query(MockAPI)
            .filter(MockAPI.id == mock_id)
            .first()
        )

        # Verify ownership (also handles mock not found)
        if mock is None or mock.user_id != user_id:
            raise HTTPException(
                status_code=404,
                detail="Mock API not found.",
            )

        return MockAPIDetailResponse(
            success=True,
            id=mock.id,
            name=mock.name,
            endpoint_token=mock.endpoint_token,
            endpoint_url=f"/mock/{mock.endpoint_token}",
            method=HTTPMethod(mock.method),
            status_code=mock.status_code,
            response_body=mock.response_body,
            response_delay_ms=mock.response_delay_ms,
            authentication=AuthConfig(**mock.auth_config),
            hit_count=mock.hit_count,
            is_active=mock.is_active,
            created_at=mock.created_at,
        )
        
    @staticmethod
    def update_mock_api(
        db: Session,
        mock_id: str,
        request: MockAPIRequest,
        user_id: str,
    ) -> MockAPIDetailResponse:
        """
        Update an existing mock API.
        """

        # Validate request
        MockAPIService._validate_request(request)

        # Find mock
        mock = (
            db.query(MockAPI)
            .filter(MockAPI.id == mock_id)
            .first()
        )

        # Verify ownership
        if mock is None or mock.user_id != user_id:
            raise HTTPException(
                status_code=404,
                detail="Mock API not found."
            )

        # Update editable fields
        mock.name = request.name.strip()
        mock.description = request.description
        mock.method = request.method.value
        mock.status_code = request.status_code
        mock.response_body = request.response_body
        mock.response_headers = request.response_headers
        mock.response_delay_ms = request.response_delay_ms
        mock.auth_type = request.authentication.value
        mock.auth_config = request.authentication.model_dump()

        # Save changes
        db.commit()
        db.refresh(mock)

        # Build response
        return MockAPIDetailResponse(
            success=True,
            id=mock.id,
            name=mock.name,
            description=mock.description,
            endpoint_token=mock.endpoint_token,
            endpoint_url=f"/mock/{mock.endpoint_token}",
            method=HTTPMethod(mock.method),
            status_code=mock.status_code,
            response_body=mock.response_body,
            response_headers=mock.response_headers,
            response_delay_ms=mock.response_delay_ms,
            authentication=AuthConfig(**mock.auth_config),
            hit_count=mock.hit_count,
            is_active=mock.is_active,
            created_at=mock.created_at,
            updated_at=mock.updated_at,
        )
        
    @staticmethod
    def delete_mock_api(
        db: Session,
        mock_id: str,
        user_id: str,
    )->DeleteResponse:
        """
        Delete a mock API owned by the given user.
        """

        # Find mock
        mock = (
            db.query(MockAPI)
            .filter(MockAPI.id == mock_id)
            .first()
        )

        # Verify ownership (also handles mock not found)
        if mock is None or mock.user_id != user_id:
            raise HTTPException(
                status_code=404,
                detail="Mock API not found."
            )

        # Delete
        db.delete(mock)

        # Commit
        db.commit()

        # Return success
        return DeleteResponse(
            success=True,
            message="Mock API deleted successfully."
        )