from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
import yaml
from app.database.engine import get_db
from app.models.yaml import (
    KubernetesComposeRequest,
    KubernetesFormRequest,
    KubernetesGeneratorResponse,
    InputMode,
)
from app.services.yaml_generator.yaml import YAMLGen
from app.utils.auth import get_current_user
from app.models.user import Users
from sqlalchemy.orm import Session
router = APIRouter(prefix="/yaml-generator", tags=["Tools"])


@router.post(
    "/generate",
    response_model=KubernetesGeneratorResponse,
)
async def generate_kubernetes_yaml(
    mode: InputMode = Form(...),
    data: str = Form(...),
    compose_file: UploadFile | None = File(None),
    current_user: Users =Depends(get_current_user),
    db: Session = Depends(get_db)
):

    try:

        if mode == InputMode.FORM:

            request = KubernetesFormRequest.model_validate_json(data)

            return YAMLGen.generate(request, current_user['sub'], db)

        if compose_file is None:
            raise HTTPException(
                status_code=400,
                detail="compose_file is required for compose mode.",
            )

        request = KubernetesComposeRequest.model_validate_json(data)

        compose_content = (
            await compose_file.read()
        ).decode("utf-8")

        compose_dict = list(yaml.safe_load_all(compose_content)) 

        return YAMLGen.generate(
            request=request,
            user_id=current_user['sub'],
            db=db,
            compose_data=compose_dict,
        )
        
    except HTTPException as e:
        raise e

    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=str(e),
        )