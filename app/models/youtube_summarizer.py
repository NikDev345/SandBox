from enum import Enum
from typing import List

from pydantic import BaseModel, Field, HttpUrl


class SummaryStyle(str, Enum):
    STANDARD = "standard"
    BULLET_POINTS = "bullet_points"
    DETAILED = "detailed"
    STUDY_NOTES = "study_notes"
    TIMELINE = "timeline"
    ACTION_ITEMS = "action_items"


class SummaryLength(str, Enum):
    SHORT = "short"
    MEDIUM = "medium"
    LONG = "long"


class Tone(str, Enum):
    PROFESSIONAL = "professional"
    STUDENT = "student"
    BEGINNER = "beginner"
    TECHNICAL = "technical"


class SummarySettings(BaseModel):
    style: SummaryStyle = SummaryStyle.STANDARD
    length: SummaryLength = SummaryLength.MEDIUM
    tone: Tone = Tone.PROFESSIONAL
    language: str = "English"


class TimelineItem(BaseModel):
    title: str
    summary: str


class YouTubeSummaryRequest(BaseModel):
    youtube_url: HttpUrl
    settings: SummarySettings = Field(
        default_factory=SummarySettings
    )


class YouTubeSummaryResponse(BaseModel):
    success: bool = True

    summary: str

    key_points: List[str]

    timeline: List[TimelineItem]

    important_quotes: List[str]

    action_items: List[str]

    keywords: List[str]

    processing_time: float