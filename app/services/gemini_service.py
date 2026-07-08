import os
import re

from dotenv import load_dotenv
from google import genai

load_dotenv()

import config


class GeminiService:
    """
    Service responsible for communicating with the Google Gemini API.

    Falls back to a lightweight local summarizer when no GEMINI_API_KEY is configured,
    allowing end-to-end tests to run locally without external API access.
    """

    def __init__(self):
        api_key = config.GEMINI_API_KEY

        if api_key:
            self.client = genai.Client(api_key=api_key)
            self._use_mock = False
        else:
            self.client = None
            self._use_mock = True

    def generate(self, prompt: str) -> str:
        """
        Generate a response from Gemini or a local fallback.
        """
        if self._use_mock:
            # Extract only the source text from between the delimiters
            # that PromptEngine always wraps it in:
            #   Source Text:\n--------------------\n<text>\n--------------------
            match = re.search(
                r'Source Text:\s*-{10,}\s*(.*?)\s*-{10,}',
                prompt,
                re.DOTALL,
            )
            if match:
                source = match.group(1).strip()
            else:
                # Fallback: use the last non-empty block of the prompt
                # (avoids returning instruction lines)
                blocks = [b.strip() for b in prompt.split('\n\n') if b.strip()]
                source = blocks[-1] if blocks else prompt.strip()

            sentences = re.split(r'(?<=[.!?])\s+', source)
            if len(sentences) <= 3:
                return ' '.join(sentences).strip()
            return ' '.join(sentences[:3]).strip()

        try:
            response = self.client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
            )
            return response.text.strip()

        except Exception as e:
            raise RuntimeError(f"Gemini API Error: {str(e)}")
        
    def generate_code_review(self, prompt: str):
        """
        Generic Gemini generation.
        Used by Code Reviewer, SQL Generator,
        Regex Generator, Unit Test Generator, etc.
        """
        
        try:
            response = self.client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt
            )
            return response.text.strip()
        
        except Exception as e:
            raise RuntimeError(f"Gemini api error: {e}")