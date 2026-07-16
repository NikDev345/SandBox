from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


# ==========================================================
# Modes
# ==========================================================

class EmailMode(str, Enum):
    REWRITE = "rewrite"
    GENERATE = "generate"


# ==========================================================
# Rewrite Style
# ==========================================================

class RewriteStyle(str, Enum):
    IMPROVE = "improve"
    PROFESSIONAL = "professional"
    FORMAL = "formal"
    FRIENDLY = "friendly"
    POLITE = "polite"
    CONFIDENT = "confident"
    PERSUASIVE = "persuasive"
    CONCISE = "concise"
    EXPAND = "expand"
    SIMPLIFY = "simplify"
    GRAMMAR = "grammar"
    EXECUTIVE = "executive"
    CUSTOMER_SUPPORT = "customer_support"
    SALES = "sales"
    MARKETING = "marketing"


# ==========================================================
# Tone
# ==========================================================

class Tone(str, Enum):
    PROFESSIONAL = "professional"
    FORMAL = "formal"
    FRIENDLY = "friendly"
    CASUAL = "casual"
    CONFIDENT = "confident"
    EMPATHETIC = "empathetic"
    RESPECTFUL = "respectful"
    PERSUASIVE = "persuasive"
    ENTHUSIASTIC = "enthusiastic"
    NEUTRAL = "neutral"


# ==========================================================
# Email Length
# ==========================================================

class EmailLength(str, Enum):
    PRESERVE = "preserve"
    SHORT = "short"
    MEDIUM = "medium"
    LONG = "long"


# ==========================================================
# Language
# ==========================================================

class Language(str, Enum):
    ENGLISH = "English"


# ==========================================================
# AI Settings
# ==========================================================

class EmailSettings(BaseModel):
    """
    Controls how Gemini generates or rewrites emails.
    """

    style: RewriteStyle = RewriteStyle.IMPROVE

    tone: Tone = Tone.PROFESSIONAL

    length: EmailLength = EmailLength.PRESERVE

    language: Language = Language.ENGLISH

    preserve_intent: bool = True

    improve_subject: bool = True

    improve_greeting: bool = True

    improve_closing: bool = True

    fix_grammar: bool = True

    improve_clarity: bool = True

    improve_readability: bool = True


# ==========================================================
# Request
# ==========================================================

class EmailStudioRequest(BaseModel):
    """
    Universal request model.

    Supports

    • Rewrite
    • Generate

    Future

    • Reply
    • Translate
    • Summarize
    """

    mode: EmailMode = EmailMode.REWRITE

    subject: Optional[str] = Field(
        default=None,
        max_length=200,
        description="Optional email subject.",
    )

    email: Optional[str] = Field(
        default=None,
        max_length=30000,
        description="Existing email used for Rewrite mode.",
    )

    instruction: Optional[str] = Field(
        default=None,
        max_length=30000,
        description="Prompt used for Generate mode.",
    )

    settings: EmailSettings = Field(
        default_factory=EmailSettings
    )


# ==========================================================
# Response
# ==========================================================

class EmailStudioResponse(BaseModel):
    """
    Unified response model.
    """

    subject: str

    greeting: str

    body: str

    closing: str

    full_email: str

    suggestions: List[str] = Field(
        default_factory=list
    )

    model_config = ConfigDict(
        from_attributes=True
    )