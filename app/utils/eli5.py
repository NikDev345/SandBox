"""
ELI5 Utility Functions
----------------------
Reusable helper functions for the ELI5 tool.
"""

import re


def normalize_topic(topic: str) -> str:
    """
    Normalize the input topic by trimming whitespace
    and collapsing multiple spaces.
    """
    return re.sub(r"\s+", " ", topic.strip())


def clean_text(text: str) -> str:
    """
    Clean AI-generated text by removing extra whitespace.
    """
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def word_count(text: str) -> int:
    """
    Return the number of words.
    """
    return len(text.split())


def character_count(text: str) -> int:
    """
    Return the number of characters.
    """
    return len(text)


def estimate_reading_time(text: str, words_per_minute: int = 200) -> int:
    """
    Estimate reading time in minutes.
    """
    words = word_count(text)
    return max(1, round(words / words_per_minute))


def truncate_text(text: str, max_length: int) -> str:
    """
    Truncate text without breaking words.
    """
    if len(text) <= max_length:
        return text

    truncated = text[:max_length].rsplit(" ", 1)[0]
    return truncated + "..."


def title_case(topic: str) -> str:
    """
    Convert a topic into title case.
    """
    return normalize_topic(topic).title()