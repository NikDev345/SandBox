from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status


from app.models.notes_cleaner import (
    NotesCleanerRequest,
    NotesCleanerResponse,
)
from app.models.user import Users
from app.services.notes_cleaner.notes_cleaner import NotesCleaner
from app.utils.auth import get_current_user


router = APIRouter(
    prefix="/notes_cleaner",
    tags=["Notes Cleaner"],
)


@router.post(
    "/clean",
    response_model=NotesCleanerResponse,
    status_code=status.HTTP_200_OK,
)
async def clean_notes(
    text: str | None = Form(None),
    file: UploadFile | None = File(None),
    current_user: Users = Depends(get_current_user),
):
    try:
        request = NotesCleanerRequest(text=text)

        response = await NotesCleaner._clean_notes(
            current_user,
            request=request,
            file=file,
        )

        return response

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to clean notes: {str(e)}",
        )