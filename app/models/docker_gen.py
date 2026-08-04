from pydantic import BaseModel


class QuickStartStep(BaseModel):
    title: str
    command: str


class DockerfileGeneratorResponse(BaseModel):
    dockerfile: str
    quick_start: list[QuickStartStep]
    execution_id: str | None = None 