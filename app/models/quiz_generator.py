from __future__ import annotations

from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict


# ==========================================================
# ENUMS
# ==========================================================

class InputType(str, Enum):
    PROMPT = "prompt"
    DOCUMENT = "document"


class DocumentType(str, Enum):
    PDF = "pdf"
    DOCX = "docx"
    PPTX = "pptx"
    TXT = "txt"
    MARKDOWN = "markdown"


class Difficulty(str, Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"
    MIXED = "mixed"


class QuestionType(str, Enum):
    MCQ = "mcq"
    TRUE_FALSE = "true_false"
    FILL_BLANK = "fill_blank"
    SHORT_ANSWER = "short_answer"
    MULTIPLE_SELECT = "multiple_select"


class Language(str, Enum):
    ENGLISH = "english"


class Audience(str, Enum):
    SCHOOL = "school"
    COLLEGE = "college"
    UNIVERSITY = "university"
    INTERVIEW = "interview"
    PROFESSIONAL = "professional"


# ==========================================================
# REQUEST MODELS
# ==========================================================

class QuizSettings(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        validate_assignment=True
    )

    question_count: int = Field(
        default=10,
        ge=1,
        le=100
    )

    difficulty: Difficulty = Difficulty.MEDIUM

    language: Language = Language.ENGLISH

    audience: Audience = Audience.COLLEGE

    question_types: List[QuestionType] = Field(
        default_factory=lambda: [QuestionType.MCQ]
    )

    shuffle_questions: bool = False

    shuffle_options: bool = False

    include_explanations: bool = True

    include_hints: bool = False


class QuizRequest(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        validate_assignment=True
    )

    input_type: InputType

    prompt: Optional[str] = None

    extracted_text: Optional[str] = None

    filename: Optional[str] = None

    document_type: Optional[DocumentType] = None

    settings: QuizSettings


# ==========================================================
# RESPONSE MODELS
# ==========================================================

class QuizOption(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str

    text: str


class QuizQuestion(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str

    question: str

    question_type: QuestionType

    options: List[QuizOption] = Field(default_factory=list)

    correct_answers: List[str] = Field(default_factory=list)

    explanation: Optional[str] = None

    hint: Optional[str] = None

    difficulty: Difficulty

    marks: int = 1


class QuizMetadata(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str

    description: Optional[str] = None

    total_questions: int

    estimated_time_minutes: int

    language: Language

    difficulty: Difficulty


class QuizResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    success: bool

    metadata: QuizMetadata

    questions: List[QuizQuestion]

    generation_time_ms: Optional[int] = None

    model_used: Optional[str] = None

    warning: Optional[str] = None

    error: Optional[str] = None