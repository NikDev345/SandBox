import os
import re

from dotenv import load_dotenv
from google import genai
from google.genai import types
import json, asyncio
from typing import Optional
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
                model=config.GEMINI_MODEL,
                contents=prompt,
            )
            return response.text.strip()

        except Exception as e:
            raise RuntimeError(f"Gemini API Error: {str(e)}")
    
    async def generate_json(
    self,
    prompt: str,
    temperature: float = 0.3,
    max_output_tokens: int = 4096,
    ) -> dict:
        """
        Generate a JSON response from Gemini or a local fallback.
        """
        if self._use_mock:
            # Return a mock JSON response for testing purposes
            return {"mock": "response"}

        try:
            response = await self.client.aio.models.generate_content(
                model=config.GEMINI_MODEL,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=temperature,
                    max_output_tokens=max_output_tokens,
                ),
            )
            text = response.text.strip()

            if text.startswith("```"):
                text = (
                    text.replace("```json", "")
                        .replace("```", "")
                        .strip()
                )

            try:
                return json.loads(text)

            except json.JSONDecodeError as e:
                print("=" * 80)
                print(text)
                print("=" * 80)
                raise RuntimeError(
                    f"Gemini returned invalid JSON:\n{text}"
                ) from e

        except Exception as e:
            raise RuntimeError(f"Gemini API Error: {str(e)}")
        

    async def generate_explanation(
        self,
        uploaded_image,
        prompt: str,
        temperature: float = 0.3,
        max_output_tokens: int = 10000,
    ):
        
        if self._use_mock:
            return "Mock screenshot explanation."

        try:
            response = await self.client.aio.models.generate_content(
                model=config.GEMINI_MODEL,
                contents=[
                    uploaded_image,
                    types.Part.from_text(text=prompt),
                ],
                config=types.GenerateContentConfig(
                    temperature=temperature,
                    max_output_tokens=max_output_tokens,
                ),
            )

            text = response.text
            if not text:
                candidates = getattr(response, "candidates", [])
                finish = candidates[0].finish_reason if candidates else "unknown"
                raise RuntimeError(f"Gemini returned no text. Finish reason: {finish}")

            return text.strip()
        
        except RuntimeError:
            raise
        except Exception as e:
            raise RuntimeError(f"Gemini API error during explanation: {e}") from e
    
    async def generate_image_json(
        self,
        uploaded_image,
        prompt: str,
        temperature: float = 0.3,
        max_output_tokens: int = 10000,
    ):
        """
        Generate a structured JSON response from Gemini Vision.
        Used by Chart Explainer and future image-based AI tools.
        """

        if self._use_mock:
            return {
                "chart_type": "Bar Chart",
                "executive_summary": "Mock summary.",
                "axis_explanation": "Mock axis explanation.",
                "key_insights": [
                    "Mock insight 1",
                    "Mock insight 2"
                ],
                "trend_analysis": "Mock trend analysis.",
                "outliers": [],
                "business_insights": "Mock business insight.",
                "recommendations": [
                    "Mock recommendation."
                ],
                "questions_answered": [
                    "Mock question."
                ],
                "limitations": [],
                "eli5_explanation": "Mock ELI5 explanation.",
                "confidence_score": 95,
            }

        try:
            response = await self.client.aio.models.generate_content(
                model=config.GEMINI_MODEL,
                contents=[
                    uploaded_image,
                    types.Part.from_text(text=prompt),
                ],
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=temperature,
                    max_output_tokens=max_output_tokens,
                ),
            )

            text = response.text.strip()

            if text.startswith("```"):
                text = (
                    text.replace("```json", "")
                        .replace("```", "")
                        .strip()
                )

            return json.loads(text)

        except json.JSONDecodeError as e:
            raise RuntimeError(
                f"Gemini returned invalid JSON:\n{text}"
            ) from e

        except Exception as e:
            raise RuntimeError(
                f"Gemini Vision JSON Error: {e}"
            ) from e
            
    async def generate_for_text_and_files(self, prompt, files: Optional[list[str]] = None) ->str:
        # -------------------------
        # Mock mode
        # -------------------------
        if self._use_mock:
            match = re.search(
                r"Source Text:\s*-{10,}\s*(.*?)\s*-{10,}",
                prompt,
                re.DOTALL,
            )

            if match:
                source = match.group(1).strip()
            else:
                blocks = [
                    b.strip()
                    for b in prompt.split("\n\n")
                    if b.strip()
                ]
                source = blocks[-1] if blocks else prompt.strip()

            sentences = re.split(r"(?<=[.!?])\s+", source)

            if len(sentences) <= 3:
                return " ".join(sentences).strip()

            return " ".join(sentences[:3]).strip()
        
        uploaded_files = []
        
        try:
            contents = [prompt]
            
            if files:
                for path in files:
                    uploaded = self.client.files.upload(file=path)
                    uploaded_files.append(uploaded)
                    contents.append(uploaded)
                    
            response = await asyncio.to_thread(
                self.client.models.generate_content,
                model=config.GEMINI_MODEL,
                contents=contents,
            )
            return response.text.strip()
        
        except Exception as e:
            raise RuntimeError(f"Gemini API Error: {e}")
        
        finally:
            for uploaded in uploaded_files:
                try:
                    self.client.files.delete(name=uploaded.name)
                except Exception:
                    pass
                
            if files:
                for path in files:
                    try:
                        if os.path.exists(path):
                            os.remove(path)
                    except Exception:
                        pass