from __future__ import annotations

from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class FlashcardDifficulty(str, Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"
    MIXED = "mixed"


class FlashcardType(str, Enum):
    BASIC = "basic"
    CLOZE = "cloze"
    DEFINITION = "definition"
    CONCEPT = "concept"
    INTERVIEW = "interview"
    MIXED = "mixed"


class FlashcardLanguage(str, Enum):
    ENGLISH = "english"


class FlashcardSettings(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        validate_assignment=True,
    )

    number_of_cards: int = Field(
        default=10,
        ge=1,
        le=100,
    )

    difficulty: FlashcardDifficulty = FlashcardDifficulty.MEDIUM

    card_type: FlashcardType = FlashcardType.BASIC

    language: FlashcardLanguage = FlashcardLanguage.ENGLISH

    include_examples: bool = True

    include_memory_tips: bool = True

    include_keywords: bool = True

    include_tags: bool = True

    shuffle_cards: bool = False


class FlashcardGeneratorRequest(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        validate_assignment=True,
    )

    content: str

    settings: FlashcardSettings = Field(
        default_factory=FlashcardSettings,
    )


class Flashcard(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str

    front: str

    back: str

    card_type: FlashcardType

    difficulty: FlashcardDifficulty

    category: str = "General"

    tags: List[str] = Field(default_factory=list)

    keywords: List[str] = Field(default_factory=list)

    example: Optional[str] = None

    memory_tip: Optional[str] = None


class FlashcardStatistics(BaseModel):
    model_config = ConfigDict(extra="forbid")

    total_cards: int

    estimated_study_time_minutes: int

    difficulty: FlashcardDifficulty

    card_type: FlashcardType

    language: FlashcardLanguage

    categories: List[str] = Field(default_factory=list)

    total_keywords: int = 0

    total_tags: int = 0


class FlashcardResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str

    description: Optional[str] = None

    flashcards: List[Flashcard]

    statistics: FlashcardStatistics


class FlashcardGeneratorResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    success: bool

    result: FlashcardResult

    generation_time_ms: Optional[int] = None

    model_used: Optional[str] = None

    warning: Optional[str] = None

    error: Optional[str] = None
