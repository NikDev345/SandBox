from typing import List
from pydantic import BaseModel, Field, ConfigDict


class JSONFixRequest(BaseModel):
    """
    Request schema for JSON Fixer.
    """
    model_config = ConfigDict(from_attributes=True)

    json_text: str = Field(
        ...,
        min_length=2,
        max_length=100000,
        description="Malformed or valid JSON to repair."
    )


class JSONFixResponse(BaseModel):
    """
    Response schema for JSON Fixer.
    """
    model_config = ConfigDict(from_attributes=True)

    success: bool = Field(
        default=True,
        description="Whether the JSON was successfully repaired."
    )
    message: str = Field(
        default="JSON repaired successfully.",
        description="Status message."
    )
    fixed_json: str = Field(
        ...,
        description="Repaired and pretty-formatted JSON."
    )
    repairs: List[str] = Field(
        default_factory=list,
        description="List of repairs applied while fixing the JSON."
    )