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
        
    async def generate_code_review(self, batch, local_report, dependency_graph):
        """
        Generic Gemini generation.
        Used by Code Reviewer, SQL Generator,
        Regex Generator, Unit Test Generator, etc.
        """
        if self._use_mock:
          return {
              "model": "mock",
              "batch_files": batch["files"],
              "review": {}
          }
        def filter_local_report(local_report, batch_files):

          filtered = {}

          batch_files = set(batch_files)

          for key, value in local_report.items():

              if isinstance(value, list):

                  filtered[key] = []

                  for item in value:

                      files = {
                          item.get("file"),
                          item.get("file1"),
                          item.get("file2"),
                          item.get("filename"),
                      }

                      files.discard(None)

                      if files & batch_files:
                          filtered[key].append(item)

              elif isinstance(value, dict):

                  filename = value.get("filename")

                  if filename is None or filename in batch_files:
                      filtered[key] = value

              else:
                  filtered[key] = value

          return filtered
        
        filtered_local_report = filter_local_report(
            local_report,
            batch["files"]
        )

        filtered_dependency_graph = {
            file: dependency_graph.get(file, [])
            for file in batch["files"]
        }
        
        system_prompt = """
You are an expert software engineer reviewing a software project.

Input:
- Source code chunks
- Dependency graph
- Local static analysis

The local analyzer has already completed:
- Syntax validation
- File statistics
- Security analysis
- Duplicate detection
- Complexity analysis
- Dependency analysis
- Project structure analysis

Treat the local analysis as the source of truth.

Do NOT:
- Repeat local analysis.
- Recompute syntax, security, complexity, duplicates, dependencies, statistics or project structure.
- Invent issues not supported by the code.

Instead, explain why reported issues matter and suggest improvements.

Analyze only the supplied code.

Review:

1. Project Summary
2. Logic Bugs
3. Performance
4. Readability
5. Best Practices
6. Refactoring
7. Production Readiness (0-100)
8. Documentation
9. Unit Test Suggestions
10. Improved Code (only when worthwhile)

Return ONLY valid JSON.
"""

        '''
        Here We will not send full project or full source code to AI, as it will massively
        increase the API cost. What we will do is first we will filter the important files
        from the project based on the score calculated. The score is calculated based on
        various factors like dependency grpah, functions, etc.
        Then from the filtered_files Eg: [main.py, api.py, auth.py]
        We will modified the code to functions and classes. That means each file is 
        combination of functions and classes
        Eg auth.py -> login() + create_token()
        It will remove uncessary lines 
        Then we will not send every files to AI, we will create batches from filtered files
        Each batch will consist of 2-3 files(for eg)
        
        Gemini will recieve only system prompt, current batch[from batches], filtered 
        local report and dependecy graph, instead of whole project. It will reduce API
        cost massively
        
        Then we will merge the response of all batches into one response and return it to 
        frontend....
        '''
        ai_chunks = [
            {
                "file": chunk["file"],
                "code": chunk["code"]
            }
            for chunk in batch["chunks"]
        ]

        ai_dependencies = filtered_dependency_graph

        ai_report = {}

        for section, findings in filtered_local_report.items():

            if not findings:
                continue

            if isinstance(findings, list):

                ai_report[section] = []

                for item in findings:

                    summary = {}

                    for key in (
                        "file",
                        "filename",
                        "severity",
                        "title",
                        "issue",
                        "line",
                    ):
                        if key in item:
                            summary[key] = item[key]

                    if summary:
                        ai_report[section].append(summary)

            else:
              if findings:
                  ai_report[section] = findings
                  
        ai_report = {
            key: value
            for key, value in ai_report.items()
            if value
        }
                
        prompt = json.dumps(
              {
                  "code": ai_chunks,
                  "dependencies": ai_dependencies,
                  "local_analysis": ai_report,
              },
              ensure_ascii=False,
              separators=(",",":")
          )
        
        try:
            response = await self.client.aio.models.generate_content(
                model=config.GEMINI_MODE,
                contents=[system_prompt, prompt],
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.2,
                    max_output_tokens=4096
                )
            )
            text = response.text.strip()

            if text.startswith("```"):
                text = (
                    text.replace("```json", "")
                        .replace("```", "")
                        .strip()
                )

            try:
                review = json.loads(text)
            except json.JSONDecodeError as e:
                raise RuntimeError(
                    f"Gemini returned invalid JSON:\n{text}"
                ) from e

            return {
                "model": config.GEMINI_MODEL,
                "batch_files": batch["files"],
                "review": review,
            }

        except Exception as e:
            raise RuntimeError(f"Gemini api error: {e}")
        

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