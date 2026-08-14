from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from app.utils.auth import get_current_user
from app.models.user import Users
from app.models.ss_explainer import (
    ScreenshotExplainerRequest,
    ExplanationAction,
)
from app.services.ss_explainer.ss_explainer import SSExplainer
from app.database.engine import get_db
from sqlalchemy.orm import Session

router = APIRouter(
    prefix="/screenshot-explainer",
    tags=["Screenshot Explainer"],
)


@router.post(
    "/explain",
    summary="Explain a screenshot using AI",
)
async def explain_screenshot(
    image: UploadFile = File(...),
    action: ExplanationAction = Form(...),
    custom_action: str | None = Form(None),
    current_user: Users = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        request = ScreenshotExplainerRequest(
            action=action,
            custom_action=custom_action,
        )

        return await SSExplainer.explain(
            request,
            image,
            db,
            current_user
        )
        
    except HTTPException as e:
        raise e

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e),
        )

    except RuntimeError as e:
        raise HTTPException(
            status_code=500,
            detail=str(e),
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"An unexpected error occurred while explaining the screenshot: {str(e)}",
        )