from fastapi import APIRouter, Depends, HTTPException, status

from app.models.pro_cons import ProConsResponse, ProConsRequest, AnalysisDepth
from app.services.pro_cons_gen.pro_cons import ProConsService
from app.utils.auth import get_current_user
from app.models.user import Users

router = APIRouter(
    prefix='/pro_cons',
    tags=["Pro Cons Generator"]
)

@router.post('/generate', response_model=ProConsResponse)
async def generate_pro_cons(request: ProConsRequest, current_user: Users = Depends(get_current_user)) -> ProConsResponse:
    
    try:
        response = await ProConsService._generate_analysis(request, current_user)
        return response
    except  HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate explanation: {str(exc)}",
        )
