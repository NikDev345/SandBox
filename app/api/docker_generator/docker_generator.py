from fastapi import APIRouter, File, HTTPException, UploadFile, Depends
from tempfile import TemporaryDirectory
from pathlib import Path
from app.models.docker_gen import DockerfileGeneratorResponse
from app.services.docker_generator.docker_service import DockerService
from app.models.user import Users
from app.utils.auth import get_current_user
import shutil
from sqlalchemy.orm import Session
from app.database.engine import get_db

router = APIRouter(prefix="/docker-generator", tags=["Docker Generator"])

@router.post(
    "/generate",
    response_model=DockerfileGeneratorResponse,
    summary="Generate Dockerfile",
)
async def generate_dockerfile(
    folder: list[UploadFile] = File(...),
    current_user: Users = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> DockerfileGeneratorResponse:
    
    if not folder:
        raise HTTPException(
            status_code=400,
            detail="Project folder is required.",
        )
    
    with TemporaryDirectory() as temp_dir:

        project_root = Path(temp_dir)

        for file in folder:
            
            if not file.filename:
                continue

            relative_path = Path(file.filename)

            if relative_path.is_absolute() or ".." in relative_path.parts:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid file path.",
                )

            destination = project_root / relative_path

            destination.parent.mkdir(
                parents=True,
                exist_ok=True,
            )

            with destination.open("wb") as buffer:
                shutil.copyfileobj(file.file, buffer)

        try:
            return DockerService.generate(project_root, current_user["sub"], db)

        except ValueError as e:
            raise HTTPException(
                status_code=400,
                detail=str(e),
            )

        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to generate Dockerfile: {e}",
            )