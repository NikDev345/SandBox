from fastapi import APIRouter, HTTPException, Depends
from app.models.commit import (
    CommitMessageRequest,
    CommitMessageResponse,
)
from app.services.commit_message.commit import CommitMessageGenerator
from app.utils.auth import get_current_user
from app.models.user import Users

router = APIRouter(
    prefix="/commit-message",
    tags=["Commit Message Generator"],
)


@router.post(
    "/generate",
    response_model=CommitMessageResponse,
    summary="Generate AI commit message suggestions",
)
async def generate_commit_message(
    request: CommitMessageRequest,
    current_user: Users = Depends(get_current_user),
) -> CommitMessageResponse:
    """
    Generate AI-powered Git commit message suggestions
    for the specified repository.
    """

    try:
        return CommitMessageGenerator.generate(request, current_user["sub"])

    except FileNotFoundError as e:
        raise HTTPException(
            status_code=404,
            detail=str(e),
        )

    except NotADirectoryError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e),
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
            detail="An unexpected error occurred while generating commit messages.",
        )