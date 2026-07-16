from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from app.utils.auth import get_current_user
from app.models.user import Users
from app.models.ss_explainer import (
    ScreenshotExplainerRequest,
    ExplanationAction,
)
from app.services.ss_explainer.ss_explainer import SSExplainer

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
    current_user: Users = Depends(get_current_user)
):
    try:
        request = ScreenshotExplainerRequest(
            action=action,
            custom_action=custom_action,
        )

        return await SSExplainer.explain(
            request,
            image,
            current_user
        )

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

    except Exception:
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred while explaining the screenshot.",
        )