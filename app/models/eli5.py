"""
ELI5 Models
-----------
Pydantic request and response models for the ELI5 tool.
"""

from typing import List

from pydantic import BaseModel, Field


class ImportantConcept(BaseModel):
    """
    A key concept extracted from the explanation.
    """

    title: str = Field(..., description="Concept name.")
    description: str = Field(..., description="Simple one-sentence description.")


class ELI5Request(BaseModel):
    """
    Request model for generating an ELI5 explanation.
    """

    topic: str = Field(
        ...,
        min_length=3,
        max_length=500,
        description="Topic or concept to explain.",
    )


class ELI5Response(BaseModel):
    """
    Response model returned by the ELI5 tool.
    """

    summary: str = Field(
        ...,
        description="One-sentence plain English summary.",
    )
    explanation: str = Field(
        ...,
        description="Full beginner-friendly explanation.",
    )
    analogy: str = Field(
        ...,
        description="A real-world analogy for the topic.",
    )
    important_concepts: List[ImportantConcept] = Field(
        default_factory=list,
        description="Key concepts extracted from the explanation.",
    )