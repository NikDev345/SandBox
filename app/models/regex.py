from enum import Enum
from pydantic import BaseModel, Field
from typing import List, Optional


class RegexEngine(str, Enum):
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    JAVA = "java"
    CSHARP = "csharp"
    PCRE = "pcre"
    GO = "go"


class RegexMode(str, Enum):
    AUTO = "auto"          # Cache -> AI
    AI = "ai"              # Force AI
    CACHE = "cache"        # Force cache


class RegexGeneratorRequest(BaseModel):
    prompt: str = Field(
        ...,
        description="Natural language description of the regex."
    )

    engine: RegexEngine = Field(
        default=RegexEngine.PYTHON,
        description="Target regex engine."
    )

    mode: RegexMode = Field(
        default=RegexMode.AUTO,
        description="Generation strategy."
    )

    test_strings: Optional[List[str]] = Field(
        default=None,
        description="Optional strings to test the generated regex."
    )
    
class RegexMatchResult(BaseModel):
    text: str
    matched: bool


class RegexGeneratorResponse(BaseModel):
    regex: str

    explanation: str

    source: str
    # cache | ai

    engine: RegexEngine

    matches: Optional[List[RegexMatchResult]] = None