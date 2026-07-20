from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.engine import get_db
from app.utils.auth import get_current_user
from app.models.user import Users
from app.models.api_mock import MockAPIRequest, MockAPIResponse, DeleteResponse, MockAPIListResponse, MockAPIDetailResponse
from app.services.mock_api.mock_api import MockAPIService

router = APIRouter(
    prefix="/api_mock",
    tags=["API Mock Generator"],
)


@router.post(
    "/create",
    response_model=MockAPIResponse,
    summary="Create Mock API",
)
async def create_mock_api(
    request: MockAPIRequest,
    db: Session = Depends(get_db),
    current_user: Users = Depends(get_current_user),
):
    return MockAPIService.create_mock_api(
        db=db,
        request=request,
        user_id=current_user.id,
        user=current_user
    )
    
@router.get(
    "/list",
    response_model=MockAPIListResponse,
    summary="List Mock APIs",
)
async def list_mock_apis(
    db: Session = Depends(get_db),
    current_user: Users = Depends(get_current_user),
):
    return MockAPIService.list_mock_apis(
        db=db,
        user_id=current_user.id,
    )
    
@router.get(
    "/{id}",
    response_model=MockAPIDetailResponse,
    summary="Get Mock API",
)
async def get_mock_api(
    id: str,
    db: Session = Depends(get_db),
    current_user: Users = Depends(get_current_user),
):
    return MockAPIService.get_mock_api(
        db=db,
        mock_id=id,
        user_id=current_user.id,
    )
    
@router.put(
    "/{id}",
    response_model=MockAPIDetailResponse,
    summary="Update Mock API",
)
async def update_mock_api(
    id: str,
    request: MockAPIRequest,
    db: Session = Depends(get_db),
    current_user: Users = Depends(get_current_user),
):
    return MockAPIService.update_mock_api(
        db=db,
        mock_id=id,
        request=request,
        user_id=current_user.id,
    )
    
@router.delete(
    "/{id}",
    response_model=DeleteResponse,
    summary="Delete Mock API",
)
async def delete_mock_api(
    id: str,
    db: Session = Depends(get_db),
    current_user: Users = Depends(get_current_user),
):
    return MockAPIService.delete_mock_api(
        db=db,
        mock_id=id,
        user_id=current_user.id,
    )