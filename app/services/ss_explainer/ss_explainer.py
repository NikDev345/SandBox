from fastapi import UploadFile
from app.models.ss_explainer import ScreenshotExplainerRequest, ExplanationAction, ScreenshotMetadata
from PIL import Image, UnidentifiedImageError
from io import BytesIO
from app.services.gemini_service import GeminiService

class SSExplainer:
    
    @staticmethod
    def _validate_request(request: ScreenshotExplainerRequest):
        if request.action not in ExplanationAction:
            raise ValueError("Invalid action selected!")
        
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
            
        return image
        
    @staticmethod
    def _extract_metadata(image: Image.Image, filename: str, mime_type: str, file_size: int):
        return ScreenshotMetadata(
            filename=filename,
            mime_type=mime_type,
            file_size=file_size,
            width=image.width,
            height=image.height,
        )
        
    @staticmethod
    def _process_image(image: Image.Image):
        buffer = BytesIO()
        
        image_format = image.format or "PNG"
        
        image.save(buffer, format=image_format)
        
        return buffer.getvalue()
    
    @staticmethod
    def _build_prompt(action: ExplanationAction, custom_action: str | None = None):
        PROMPTS = {
            ExplanationAction.GENERAL_EXPLANATION: (
                "Explain everything visible in this screenshot in a clear and structured manner."
            ),

            ExplanationAction.QUICK_SUMMARY: (
                "Provide a concise summary of the uploaded screenshot, highlighting the most important information."
            ),

            ExplanationAction.STEP_BY_STEP: (
                "Explain the screenshot step by step, describing each visible section or process in order."
            ),

            ExplanationAction.ERROR_ANALYSIS: (
                "Identify and explain any visible errors, warnings, or issues in the screenshot. "
                "Suggest possible causes and solutions based only on the visible information."
            ),

            ExplanationAction.UI_EXPLANATION: (
                "Explain the user interface shown in the screenshot, including the purpose of visible controls, menus, buttons, and panels."
            ),

            ExplanationAction.CODE_EXPLANATION: (
                "Explain the code visible in the screenshot, including what it does, how it works, and any important observations."
            ),
        }

        if action == ExplanationAction.OTHER:
            return (
                "Analyze the uploaded screenshot according to the following instruction.\n\n"
                f"Instruction:\n{custom_action}\n\n"
                "Only use information visible in the screenshot. "
                "If additional information is required, clearly state that it is not visible."
            )

        try:
            return PROMPTS[action]
        except KeyError:
            raise ValueError(f"Unsupported action: {action}")
        
    @staticmethod
    def _upload_image(image_bytes, mime_type):
        client = GeminiService()
        
        try:
            pass
        except:
            pass