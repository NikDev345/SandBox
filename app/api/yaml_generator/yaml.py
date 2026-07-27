from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
import yaml

from app.models.yaml import (
    KubernetesComposeRequest,
    KubernetesFormRequest,
    KubernetesGeneratorResponse,
    InputMode,
)
from app.services.yaml_generator.yaml import YAMLGen
from app.utils.auth import get_current_user
from app.models.user import Users

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
):

    try:

        if mode == InputMode.FORM:

            request = KubernetesFormRequest.model_validate_json(data)

            return YAMLGen.generate(request)

        if compose_file is None:
            raise HTTPException(
                status_code=400,
                detail="compose_file is required for compose mode.",
            )

        request = KubernetesComposeRequest.model_validate_json(data)

        compose_content = (
            await compose_file.read()
        ).decode("utf-8")

        compose_dict = yaml.safe_load(compose_content)

        return YAMLGen.generate(
            request=request,
            compose_data=compose_dict,
        )

    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=str(e),
        )