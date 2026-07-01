import os

from dotenv import load_dotenv
from google import genai

load_dotenv()


class GeminiService:
    """
    Service responsible for communicating with the Google Gemini API.
    """

    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")

        if not api_key:
            raise ValueError("GEMINI_API_KEY not found.")

        self.client = genai.Client(api_key=api_key)

    def generate(self, prompt: str) -> str:
        """
        Generate a response from Gemini.

        Args:
            prompt: Prompt to send to Gemini.

        Returns:
            Generated response text.

        Raises:
            RuntimeError: If the Gemini API request fails.
        """
        try:
            response = self.client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
            )

            return response.text.strip()

        except Exception as e:
            raise RuntimeError(f"Gemini API Error: {str(e)}")

