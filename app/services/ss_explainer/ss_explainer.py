from fastapi import UploadFile
from app.models.ss_explainer import ScreenshotExplainerRequest, ExplanationAction, ScreenshotExplainerResponse, ScreenshotMetadata, ScreenshotExplainerLLMResponse
from PIL import Image, UnidentifiedImageError, ImageOps
from io import BytesIO
from app.services.LLM_Gateway.llm_config import gateway
from app.router_llm.gateway import LLMRequest
from google.genai import types
from app.services.tool_executor import ExecutionService
from app.services.tool_service import ToolService
from sqlalchemy.orm import Session
import json

class SSExplainer:
    
    PROMPTS = {
        ExplanationAction.GENERAL_EXPLANATION: (
            """
            Analyze the uploaded screenshot and provide a clear explanation.

            Include:
            - The main purpose of the screenshot
            - Important visible elements
            - Relevant visible text
            - Overall observations

            Do not assume or infer information that is not visible.
            Return ONLY valid JSON in this format:

{
  "title": "string",
  "explanation": "string"
}

Do not include markdown or extra text.
            """
        ),

        ExplanationAction.QUICK_SUMMARY: (
            """
            Provide a concise summary of the screenshot in 3–5 sentences.

            Focus only on the most important information visible in the image.
            Do not include unnecessary details or assumptions.
            Return ONLY valid JSON in this format:

{
  "title": "string",
  "explanation": "string"
}

Do not include markdown or extra text.
            """
        ),

        ExplanationAction.DETAILED_ANALYSIS: (
            """
            Perform a detailed analysis of the screenshot.

            Include:
            - Overall purpose
            - Layout and structure
            - Important UI elements or content
            - Visible text and its significance
            - Relationships between different sections
            - Key observations

            Base your explanation only on what is visible.
            Return ONLY valid JSON in this format:

{
  "title": "string",
  "explanation": "string"
}

Do not include markdown or extra text.
            """
        ),

        ExplanationAction.STEP_BY_STEP_WALKTHROUGH: (
            """
            Explain the screenshot as if guiding a first-time user.

            Describe:
            - The overall screen
            - Each important section
            - The purpose of visible buttons, menus, fields, or controls
            - The likely workflow from top to bottom

            Only describe what is visible.
            Return ONLY valid JSON in this format:

{
  "title": "string",
  "explanation": "string"
}

Do not include markdown or extra text.
            """
        ),

        ExplanationAction.ERROR_ANALYSIS: (
            """
            Analyze the screenshot for visible errors, warnings, or problems.

            Include:
            - The detected error or issue
            - What it means
            - Possible causes based on the screenshot
            - Recommended solutions or next steps

            If no error is visible, clearly state that.
            Return ONLY valid JSON in this format:

{
  "title": "string",
  "explanation": "string"
}

Do not include markdown or extra text.
            """
        ),

        ExplanationAction.TEXT_EXTRACTION: (
            """
            Extract all readable text from the screenshot.

            Then:
            - Organize the extracted text logically
            - Explain its meaning or purpose
            - Highlight any important information

            Preserve the original wording whenever possible.
            Return ONLY valid JSON in this format:

{
  "title": "string",
  "explanation": "string"
}

Do not include markdown or extra text.
            """
        ),

        ExplanationAction.UI_UX_REVIEW: (
            """
            Review the user interface shown in the screenshot.

            Evaluate:
            - Layout and organization
            - Visual hierarchy
            - Clarity of navigation
            - Ease of use
            - Design consistency

            Provide strengths, weaknesses, and practical improvement suggestions.
            Return ONLY valid JSON in this format:

{
  "title": "string",
  "explanation": "string"
}

Do not include markdown or extra text.
            """
        ),

        ExplanationAction.ACCESSIBILITY_REVIEW: (
            """
            Review the screenshot from an accessibility perspective.

            Evaluate:
            - Readability
            - Color contrast (only if visually apparent)
            - Font size
            - Button visibility
            - Labels and icons
            - Overall usability

            Suggest improvements that would make the interface more accessible.
            Return ONLY valid JSON in this format:

{
  "title": "string",
  "explanation": "string"
}

Do not include markdown or extra text.
            """
        ),

        ExplanationAction.EDUCATIONAL_EXPLANATION: (
            """
            Explain the screenshot in a beginner-friendly manner.

            Assume the reader has little or no prior knowledge.

            Define technical terms, explain concepts simply, and provide enough context for understanding.
            Return ONLY valid JSON in this format:

{
  "title": "string",
  "explanation": "string"
}

Do not include markdown or extra text.
            """
        ),

        ExplanationAction.TROUBLESHOOTING: (
            """
            Analyze the screenshot to identify any visible problems or potential issues.

            Include:
            - What appears to be wrong
            - Possible reasons
            - Recommended troubleshooting steps
            - Information that may be missing to fully diagnose the issue

            Do not make assumptions beyond what is visible.
            Return ONLY valid JSON in this format:

{
  "title": "string",
  "explanation": "string"
}

Do not include markdown or extra text.
            """
        ),
    }
    
    @staticmethod
    def _validate_request(request: ScreenshotExplainerRequest):
        
        if request.action == ExplanationAction.OTHER:
            custom = (request.custom_action or "").strip()
            
            if not custom:
                raise ValueError("Action cannot be empty")
            
            word_count = len(custom.split())
            
            if word_count > 200:
                raise ValueError("Custom action cannot exceed 200 words.")
            
            request.custom_action = custom
            
        else:
            request.custom_action = None
            
        return request
    
    @staticmethod
    async def _validate_image(img: UploadFile):
        MAX_FILE_SIZE = 50 * 1024 * 1024
        ALLOWED_MIME_TYPES = {
            "image/png",
            "image/jpeg",
            "image/jpg",
            "image/webp",
        }
        
        if img is None:
            raise ValueError("No image was uploaded")
        
        if img.content_type not in ALLOWED_MIME_TYPES:
            raise ValueError("Unsupported image format. Allowed formats: PNG, JPEG, JPG, WEBP.")

        image_bytes = await img.read()
        
        if len(image_bytes) > MAX_FILE_SIZE:
            raise ValueError("Image size exceeds the maximum limit of 50 MB.")
        
        try:
            image = Image.open(BytesIO(image_bytes))
            image.verify()
            
            image = Image.open(BytesIO(image_bytes))
            image.load()
            
        except (UnidentifiedImageError, OSError) as e:
            raise ValueError(f"Error: {e}")
            
        return image, len(image_bytes)
        
    @staticmethod
    def _extract_metadata(image: Image.Image, filename: str, mime_type: str, file_size: int):
        return ScreenshotMetadata(
            filename=filename,
            content_type=mime_type,
            file_size=file_size,
            width=image.width,
            height=image.height,
        )
        
    @staticmethod
    def _process_image(image: Image.Image, max_dimension: int = 2048, jpeg_quality: int = 95):
        image = ImageOps.exif_transpose(image)

        # Convert unsupported modes
        if image.mode not in ("RGB",):
            image = image.convert("RGB")

        # Resize while preserving aspect ratio
        image.thumbnail((max_dimension, max_dimension), Image.Resampling.LANCZOS)

        buffer = BytesIO()

        # Save as JPEG to reduce upload size
        image.save(
            buffer,
            format="JPEG",
            quality=jpeg_quality,
            optimize=True,
        )

        data = buffer.getvalue()
        buffer.close()
        
        return data
    
    @staticmethod
    def _build_prompt(action: ExplanationAction, custom_action: str | None = None):

        if action == ExplanationAction.OTHER:
            return (
                "Analyze the uploaded screenshot according to the following instruction.\n\n"
                f"Instruction:\n{custom_action}\n\n"
                "Only use information visible in the screenshot. "
                "If additional information is required, clearly state that it is not visible."
            )

        try:
            return SSExplainer.PROMPTS[action]
        except KeyError:
            raise ValueError(f"Unsupported action: {action}")
        
    @staticmethod
    def _upload_image(image_bytes: bytes, mime_type: str):
        """
        Upload the processed image using LLM.
        """
        try:
            return types.Part.from_bytes(data=image_bytes, mime_type=mime_type)

        except Exception as e:
            raise RuntimeError(f"Failed to upload image: {e}") from e
        
    @staticmethod
    async def _generate_explanation(
        uploaded_image,
        prompt: str,
    ):
        try:
            response = await gateway.generate(
                LLMRequest(
                    prompt=prompt,
                    files=[uploaded_image],
                    temperature=0.3,
                    max_output_tokens=2000,
                    tool_slug="screenshot_explainer",
                    response_schema=ScreenshotExplainerLLMResponse
                )
            )

            if not response or not response.text:
                raise RuntimeError("Empty response from LLM")

            if not isinstance(response.text, dict):
                raise RuntimeError("Invalid structured response")

            return ScreenshotExplainerLLMResponse(**response.text)

        except Exception as e:
            raise RuntimeError(f"Gemini explanation failed: {e}")
        
    @staticmethod
    async def explain(
        request: ScreenshotExplainerRequest,
        image: UploadFile,
        db: Session,
        user=None
    ):
        from app.services.credit_service import enforce_credit_limit
        enforce_credit_limit(db, user['sub'])
        
        # 1. Validate request
        request = SSExplainer._validate_request(request)

        # 2. Validate image
        validated_image, file_size = await SSExplainer._validate_image(image)

        # 4. Extract metadata
        metadata = SSExplainer._extract_metadata(
            image=validated_image,
            filename=image.filename,
            mime_type=image.content_type,
            file_size=file_size,
        )

        # Metadata can be logged if required

        # 5. Process image
        processed_image = SSExplainer._process_image(validated_image)

        # 6. Build prompt
        prompt = SSExplainer._build_prompt(
            action=request.action,
            custom_action=request.custom_action,
        )

        # 7. Upload image
        uploaded_image = SSExplainer._upload_image(
            image_bytes=processed_image,
            mime_type='image/jpeg',
        )

        data = await SSExplainer._generate_explanation(
            uploaded_image=uploaded_image,
            prompt=prompt,
        )
        
        tool = ToolService.get_tool_by_slug(
                db=db,
                slug="ss_explainer",
            )
        tool_id = tool.id if tool else "ss_explainer"
        
        execution_id = None
        
        try:
            execution = ExecutionService.create_execution(
                db=db,
                user_id=user['sub'],
                tool_id=tool_id,
                user_input=request.model_dump_json(),
                output=data.model_dump_json(),
            )
            execution_id = execution.id
        except Exception:
            pass

        final = ScreenshotExplainerResponse(
            title=data.title,
            explanation=data.explanation
        )

        final.execution_id = execution_id
        return final