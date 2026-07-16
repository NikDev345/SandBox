from fastapi import UploadFile
from app.models.ss_explainer import ScreenshotExplainerRequest, ExplanationAction, ScreenshotMetadata, ScreenshotExplainerResponse
from PIL import Image, UnidentifiedImageError, ImageOps
from io import BytesIO
from app.services.gemini_service import GeminiService
from google.genai import types

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
            """
        ),

        ExplanationAction.QUICK_SUMMARY: (
            """
            Provide a concise summary of the screenshot in 3–5 sentences.

            Focus only on the most important information visible in the image.
            Do not include unnecessary details or assumptions.
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
            """
        ),

        ExplanationAction.EDUCATIONAL_EXPLANATION: (
            """
            Explain the screenshot in a beginner-friendly manner.

            Assume the reader has little or no prior knowledge.

            Define technical terms, explain concepts simply, and provide enough context for understanding.
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
    def _validate_image(img: UploadFile):
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

        image_bytes = img.file.read()
        
        if len(image_bytes) > MAX_FILE_SIZE:
            raise ValueError("Image size exceeds the maximum limit of 50 MB.")
        
        try:
            image = Image.open(BytesIO(image_bytes))
            image.verify()
            
            image = Image.open(BytesIO(image_bytes))
            image.load()
            
        except (UnidentifiedImageError, OSError) as e:
            raise ValueError(f"Error: {e}")
        
        finally:
            img.file.seek(0)
            
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
    def _upload_image(gemini, image_bytes: bytes, mime_type: str):
        """
        Upload the processed image using GeminiService.
        """
        try:
            return types.Part.from_bytes(data=image_bytes, mime_type=mime_type)

        except Exception as e:
            raise RuntimeError(f"Failed to upload image: {e}") from e
        
    @staticmethod
    async def _generate_explanation(
        gemini,
        uploaded_image,
        prompt: str,
        temperature: float = 0.3,
        max_output_tokens: int = 10000,
    ) -> str:
        """
        Generate an explanation for an uploaded image.
        """
        try:
            return await gemini.generate_explanation(
                uploaded_image=uploaded_image,
                prompt=prompt,
                temperature=temperature,
                max_output_tokens=max_output_tokens,
            )

        except Exception as e:
            raise RuntimeError(f"Gemini explanation failed: {e}") from e
        
    @staticmethod
    def _parse_response(raw_response: str):
        """
        Convert Gemini output into ScreenshotExplainerResponse.

        Responsibilities:
        - Validate response.
        - Handle empty responses.
        - Handle malformed responses.
        - Populate response model.
        """

        if raw_response is None:
            raise RuntimeError("Gemini returned no response.")

        explanation = raw_response.strip()

        if not explanation:
            raise RuntimeError("Gemini returned an empty response.")

        try:
            return ScreenshotExplainerResponse(
                title="Screenshot Explanation",
                explanation=explanation,
            )

        except Exception as e:
            raise RuntimeError(f"Failed to parse Gemini response: {e}") from e
        
    @staticmethod
    async def explain(
        request: ScreenshotExplainerRequest,
        image: UploadFile,
        user=None
    ):
        
        gemini = GeminiService()
        # 1. Validate request
        request = SSExplainer._validate_request(request)

        # 2. Validate image
        validated_image, file_size = SSExplainer._validate_image(image)

        # 4. Extract metadata
        metadata = SSExplainer._extract_metadata(
            image=validated_image,
            filename=image.filename,
            mime_type=image.content_type,
            file_size=file_size,
        )

        # Metadata can be logged if required
        # logger.info(metadata.model_dump())

        # 5. Process image
        processed_image = SSExplainer._process_image(validated_image)

        # 6. Build prompt
        prompt = SSExplainer._build_prompt(
            action=request.action,
            custom_action=request.custom_action,
        )

        # 7. Upload image
        uploaded_image = SSExplainer._upload_image(
            gemini,
            image_bytes=processed_image,
            mime_type='image/jpeg',
        )

        # 8. Generate explanation
        raw_response = await SSExplainer._generate_explanation(
            gemini,
            uploaded_image=uploaded_image,
            prompt=prompt,
        )

        # 9. Parse response
        response = SSExplainer._parse_response(raw_response)

        return response