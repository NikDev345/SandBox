from app.models.error_explainer import ErrorExplainerRequest, ErrorExplainerResponse
import tempfile, textwrap, json, asyncio
from app.services.gemini_service import GeminiService
from typing import Optional
from pydantic import ValidationError

class ErrorExplainer:
    client = GeminiService()
    @staticmethod
    def _validate_input(request: ErrorExplainerRequest):
        thres = 1500
        
        # helper for creating txt file
        def create_temp_file(content: str):
            with tempfile.NamedTemporaryFile(
                mode='w',
                suffix='.txt',
                delete=False,
                encoding='utf-8'
            ) as temp_file:
                temp_file.write(content)
                return temp_file.name
        
        if not request.error or not request.error.strip():
            raise ValueError("Give the error!")
        error = request.error.strip()
        code = request.code.strip() if request.code and request.code.strip() else None
        error_file_path = None
        code_file_path = None
        if len(error) > thres:
            error_file_path = create_temp_file(error)
            
        if code is not None and len(code) > thres:
            code_file_path = create_temp_file(code) 
        use_file = error_file_path is not None or code_file_path is not None
        
        return (error, code, use_file, error_file_path, code_file_path)
            
        
    @staticmethod
    def _build_prompt():
        return textwrap.dedent("""
    You are an expert software debugging assistant.

Your task is to analyze the provided error message, stack trace, log, and optional source code to determine the actual issue.

Instructions:
- Read the provided error carefully.
- If source code is provided, use it to identify the root cause.
- If no source code is provided, explain the error using only the available information.
- Keep the explanation clear, concise, and beginner-friendly.
- If a corrected code snippet, terminal command, or configuration is helpful, include it in the "code" field.
- If no code is required, return null for the "code" field.
- Do not make up information that is not supported by the provided input.

Return ONLY valid JSON matching this schema:

{
  "title": "string",
  "explanation": "string",
  "code": "string | null"
}

Rules:
- Do not wrap the JSON in markdown.
- Do not include any additional text before or after the JSON.
- Ensure the response is valid JSON.
    """)
    
    @staticmethod
    async def _call_ai(
        prompt: str,
        error: str,
        code: Optional[str],
        use_file: bool,
        error_file_path: Optional[str],
        code_file_path: Optional[str],
    ):
        files = []

        if use_file:
            if error_file_path:
                files.append(error_file_path)

            if code_file_path:
                files.append(code_file_path)

            user_prompt = prompt

            if not error_file_path:
                user_prompt += f"\n\nError:\n{error}"

            if code and not code_file_path:
                user_prompt += f"\n\nSource Code:\n{code}"

            response = await ErrorExplainer.client.generate_for_text_and_files(
                prompt=user_prompt,
                files=files,
            )

        else:
            user_prompt = f"{prompt}\n\nError:\n{error}"

            if code:
                user_prompt += f"\n\nSource Code:\n{code}"

            response = await ErrorExplainer.client.generate_for_text_and_files(
                prompt=user_prompt,
            )

        if isinstance(response, str):
            return response.strip()

        return response.text.strip()
    
    @staticmethod
    def _parse_response(raw_text) -> ErrorExplainerResponse:
        raw_text = raw_text.strip()
        # Remove markdown code fences if present
        if raw_text.startswith("```"):
            lines = raw_text.splitlines()

            # Remove opening fence (``` or ```json)
            lines = lines[1:]

            # Remove closing fence
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]

            raw_text = "\n".join(lines).strip()

        try:
            data = json.loads(raw_text)
        except json.JSONDecodeError as e:
            raise ValueError(f"AI returned invalid JSON: {e}") from e
        
        try:
            return ErrorExplainerResponse.model_validate(data)
        except ValidationError as e:
            raise ValueError(f"AI response does not match the expected schema: {e}") from e
     
    @staticmethod
    async def explain_error(request: ErrorExplainerRequest,) -> ErrorExplainerResponse:
        (
            error,
            code,
            use_file,
            error_file_path,
            code_file_path,
        ) = ErrorExplainer._validate_input(request)
        
        prompt = ErrorExplainer._build_prompt()
        
        raw_response = await ErrorExplainer._call_ai(
            prompt=prompt,
            error=error,
            code=code,
            use_file=use_file,
            error_file_path=error_file_path,
            code_file_path=code_file_path,
        )
        
        return ErrorExplainer._parse_response(raw_response)