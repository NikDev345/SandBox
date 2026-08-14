import shutil
import uuid
from pathlib import Path
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from app.models.item import (
    ActionItemExtractorRequest,
    ActionItemExtractorResponse,
)
from app.services.item_extractor.item import ActionItemService
from app.models.user import Users
from app.utils.auth import get_current_user
from sqlalchemy.orm import Session
from app.database.engine import get_db

router = APIRouter(
    prefix="/item-extractor",
    tags=["Action Item Extractor"],
)

service = ActionItemService()

UPLOAD_DIR = Path("/tmp/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt"}
MAX_FILE_SIZE = 25 * 1024 * 1024  # 25MB


@router.post(
    "/upload",
    summary="Upload a document for extraction",
)
async def upload_file(
    file: UploadFile = File(...),
    current_user: Users = Depends(get_current_user),
):
    ext = Path(file.filename).suffix.lower()

    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{ext}'. Supported: .pdf, .docx, .txt",
        )

    contents = await file.read()

    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail="File exceeds the 25MB size limit.",
        )

    unique_name = f"{uuid.uuid4().hex}{ext}"
    file_path = UPLOAD_DIR / unique_name
    file_path.write_bytes(contents)

    return {"file_path": str(file_path)}


@router.post(
    "/extract",
    response_model=ActionItemExtractorResponse,
    summary="Extract action items from text or document",
)
async def extract_action_items(
    request: ActionItemExtractorRequest,
    current_user: Users = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> ActionItemExtractorResponse:

    try:
        return await service.generate(request, current_user["sub"], db)
    
    except HTTPException as e:
        raise e

    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Failed to extract action items.",
        )