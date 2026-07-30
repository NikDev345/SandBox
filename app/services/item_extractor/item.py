from app.models.item import *
from pathlib import Path
from docx import Document
import fitz, re, json, spacy
from spacy.language import Language
from app.services.gemini_service import GeminiService
from pydantic import ValidationError
from sqlalchemy.orm import Session
from app.services.tool_executor import ExecutionService
from app.services.tool_service import ToolService

class ActionItemService:
    ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt"}
    MAX_FILE_SIZE = 25 * 1024 * 1024
    client = GeminiService()
    nlp = spacy.load("en_core_web_sm")
    # Action verbs
    _ACTION_VERBS = re.compile(
        r"\b(update|fix|review|deploy|implement|create|write|prepare|schedule|"
        r"complete|finish|submit|assign|send|merge|test)\b",
        re.IGNORECASE,
    )

    # Modal verbs / obligation
    _MODAL_VERBS = re.compile(
        r"\b(should|must|need to|needs to|have to|has to|will|i'll|we'll|please)\b",
        re.IGNORECASE,
    )

    # Deadlines
    _DEADLINES = re.compile(
        r"\b(today|tomorrow|monday|tuesday|wednesday|thursday|friday|"
        r"saturday|sunday|next week|next month|by|before|deadline|eod|eow)\b",
        re.IGNORECASE,
    )

    # Request patterns
    _REQUESTS = re.compile(
        r"^(can you|could you|please|let's)\b",
        re.IGNORECASE,
    )

    # TODO markers
    _TODO = re.compile(
        r"\b(todo|action item|follow-?up|next step|pending)\b",
        re.IGNORECASE,
    )

    @staticmethod
    def _validate_request(request: ActionItemExtractorRequest) -> None:
        has_text = bool(request.text and request.text.strip())
        has_file = bool(request.file_path)
        
        if has_text and has_file:
            raise ValueError(
                "Provide either text or file, not both!"
            )
            
        if not has_text and not has_file:
            raise ValueError(
                "Input field cannot be empty"
            )
            
        if has_text:
            return
        
        elif has_file:
            if not isinstance(request.file_path, str):
                raise ValueError("file_path must be a string.")
            file_path = Path(request.file_path)
            
            if not file_path.exists():
                raise FileNotFoundError("No such file exists")
            
            if not file_path.is_file():
                raise ValueError("Not a valid file")
            
            if file_path.suffix.lower() not in ActionItemService.ALLOWED_EXTENSIONS:
                raise ValueError(
                    f"Unsupported file type '{file_path.suffix}'. "
                    f"Supported types: {', '.join(sorted(ActionItemService.ALLOWED_EXTENSIONS))}" 
                    )
            
            file_size = file_path.stat().st_size
            if file_size > ActionItemService.MAX_FILE_SIZE:
                raise ValueError(
                    f"File size exceeds the maximum allowed limit of "
                    f"{ActionItemService.MAX_FILE_SIZE // (1024 * 1024)} MB."
                )
                
    @staticmethod
    def _extract_text(request: ActionItemExtractorRequest) -> str:
        
        if request.text and request.text.strip():
            return request.text.strip()
        
        path = Path(request.file_path)
        extension = path.suffix.lower()
        
        if extension == ".txt":
            try:
                txt = path.read_text(encoding='utf-8')
            except UnicodeDecodeError:
                try:
                    txt = path.read_text(encoding='latin-1')
                except Exception as e:
                    raise ValueError(f"Failed to read text file: {e}")
            except Exception as e:
                raise ValueError(f"Failed to read text file: {e}")
            
        elif extension == ".pdf":
            try:
                pages: list[str] = []
                
                with fitz.open(path) as pdf:
                    for page in pdf:
                        pagetxt = page.get_text("text")
                        if pagetxt.strip():
                            pages.append(pagetxt)
                        
                txt = "\n\n".join(pages)
            except Exception as e:
                raise ValueError("Failed to read PDF.") from e
            
        elif extension == ".docx":
            try:
                doc = Document(path)
                paragraphs = [
                    paragraph.text.strip()
                    for paragraph in doc.paragraphs
                    if paragraph.text.strip()
                ]

                txt = "\n".join(paragraphs)

            except Exception as e:
                raise ValueError(f"Failed to read DOCX: {e}")
            
        else:
            raise ValueError("Unsupported file type.")
            
        txt = txt.replace("\r\n", "\n")
        txt = txt.replace("\r", "\n")
        if not txt.strip():
            raise ValueError("No readable text found.")
        return txt.strip()

    @staticmethod
    def _preprocess_text(text: str) -> str:
        # Normalize line endings
        text = text.replace("\r\n", "\n").replace("\r", "\n")

        # Collapse repeated spaces and tabs (preserve newlines)
        text = re.sub(r"[ \t]+", " ", text)

        # Remove trailing whitespace from each line
        text = "\n".join(line.strip() for line in text.split("\n"))

        # Collapse excessive blank lines (keep at most one blank line)
        text = re.sub(r"\n{3,}", "\n\n", text)

        # Remove leading/trailing whitespace
        return text.strip()
    
    @staticmethod
    def _split_sentences(text: str, nlp: Language) -> list[str]:
        doc = nlp(text)

        return [
            sentence.text.strip()
            for sentence in doc.sents
            if sentence.text.strip()
        ]
        
    @staticmethod
    def _is_candidate(sentence: str) -> bool:
        """Return True if a sentence is likely to contain an action item."""

        return any(
            pattern.search(sentence)
            for pattern in (
                ActionItemService._ACTION_VERBS,
                ActionItemService._MODAL_VERBS,
                ActionItemService._DEADLINES,
                ActionItemService._REQUESTS,
                ActionItemService._TODO,
            )
        )
        
    @staticmethod
    def _extract_candidate_sentences(sentences: list[str]) -> list[str]:
        selected_indices: set[int] = set()
        
        for i, sentence in enumerate(sentences):
            result = ActionItemService._is_candidate(sentence)
            if result:
                if i > 0:
                    selected_indices.add(i-1)
                selected_indices.add(i)
                
                if i < len(sentences) - 1:
                    selected_indices.add(i + 1)
                    
        return [sentences[i] for i in sorted(selected_indices)]
    
    @staticmethod
    def _build_prompt(candidate_sentences: list[str]) -> str:

        schema = {
            "action_items":[
            {
                "task": "string",
                "assignee": "string | null",
                "deadline": "string | null",
            },
            ]
        }

        prompt = f"""You are an Action Item Extraction assistant.

    Extract every actionable task from the candidate sentences.

    Return ONLY valid JSON.

    Schema:
    {json.dumps(schema, indent=2)}

    Rules:
    - Extract only actionable tasks.
    - Ignore informational, descriptive, historical, or completed statements.
    - Do not invent or infer tasks.
    - Infer the assignee only if clearly stated; otherwise use null.
    - Infer the deadline only if explicitly mentioned; otherwise use null.
    - Preserve the original wording of each task as much as possible and dont make the task to longer.
    - Paraphrase the task so that it contains 12-17 words without changing its meaning.
    - Return [] if there are no action items.
    - If there are no action items, return: 
        {{
        "action_items": []
        }}

    Candidate Sentences:
    {chr(10).join(candidate_sentences)}
    """

        return prompt
    
    @staticmethod
    async def _call_ai(prompt: str):
        try:
            response = await ActionItemService.client.generate_json(prompt=prompt, max_output_tokens=8000)
            if not response:
                raise ValueError("The AI returned an empty response.")
            return response
        except Exception as e:
            raise ValueError(f"Failed to generate response: {e}") from e
        
    @staticmethod
    def _parse_response(response: dict) -> list[ActionItem]:
        try:
            parsed = ActionItemExtractorResponse.model_validate(response)
            return parsed.action_items  
        except ValidationError as e:
            raise ValueError(f"Invalid AI response schema: {e}") from e
        
    @staticmethod
    def _remove_duplicates(action_items: list[ActionItem]) -> list[ActionItem]:

        seen: set[str] = set()
        unique_items: list[ActionItem] = []

        for item in action_items:
            # Normalize task text
            key = re.sub(r"[^\w\s]", "", item.task.lower())
            key = re.sub(r"\s+", " ", key).strip()

            if key not in seen:
                seen.add(key)
                unique_items.append(item)

        return unique_items
    
    @staticmethod
    def _build_response(
        action_items: list[ActionItem],
    ) -> ActionItemExtractorResponse:
        
        return ActionItemExtractorResponse(
            action_items=action_items,
        )
    
    @staticmethod
    async def generate(
        request: ActionItemExtractorRequest,
        user_id: str,
        db: Session
    ) -> ActionItemExtractorResponse:

        ActionItemService._validate_request(request)

        text = ActionItemService._extract_text(request)

        text = ActionItemService._preprocess_text(text)

        sentences = ActionItemService._split_sentences(text, ActionItemService.nlp)

        candidate_sentences = ActionItemService._extract_candidate_sentences(sentences)
        if not candidate_sentences:
            return ActionItemService._build_response([])

        prompt = ActionItemService._build_prompt(candidate_sentences)

        ai_response = await ActionItemService._call_ai(prompt)

        action_items = ActionItemService._parse_response(ai_response)

        action_items = ActionItemService._remove_duplicates(action_items)
        
        tool = ToolService.get_tool_by_slug(
                db=db,
                slug="ITEM-EXTRACTOR",
            )
        tool_id = tool.id if tool else "ITEM-EXTRACTOR"
        
        try:
            ExecutionService.create_execution(
                db=db,
                user_id=user_id,
                tool_id=tool_id,
                user_input=text,
                output=str(ai_response),
            )
        except Exception:
            pass

        return ActionItemService._build_response(action_items)