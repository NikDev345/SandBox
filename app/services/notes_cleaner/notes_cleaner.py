from app.models.notes_cleaner import NotesCleanerRequest, NotesCleanerResponse
from fastapi import UploadFile
from pathlib import Path
from pypdf import PdfReader
from io import BytesIO
from docx import Document
import re, asyncio
from app.services.gemini_service import GeminiService

class NotesCleaner:
    
    SUPPORTED_EXTENSIONS = {
        ".pdf",
        ".txt",
        ".docx",
    }
    MAX_SIZE_LIMIT = 50 * 1024 * 1024
    client = GeminiService()
    
    @staticmethod
    async def _validate_request(request: NotesCleanerRequest, doc: UploadFile | None):
        
        has_text = bool(request.text and request.text.strip())
        has_file = doc is not None
        
        if has_text == has_file:
            raise ValueError("Provide either pasted text or an uploaded file, but not both.")
        
        if has_text:
            request.text = request.text.strip()
            return "text", None
        
        file_name = doc.filename or ""
        ext = Path(file_name).suffix.lower()
        
        if ext not in NotesCleaner.SUPPORTED_EXTENSIONS:
            raise ValueError("Unsupported file format. Allowed: pdf, txt, doc, docx.")
        
        content = await doc.read()
        if len(content) > NotesCleaner.MAX_SIZE_LIMIT:
            raise ValueError("File exceeds the maximum size of 50 MB.")
        
        return "file", {
            "extension": ext,
            "content": content,
        }
        
    @staticmethod
    def _extract_text(content: bytes, ext: str):
        
        if ext == '.txt':
           return content.decode("utf-8", errors="replace")
        
        elif ext == '.pdf':
            reader = PdfReader(BytesIO(content))
            return "\n".join(
                page.extract_text() or ""
                for page in reader.pages
            )
            
        elif ext == '.docx':
            document = Document(BytesIO(content))
            return "\n".join(
                para.text
                for para in document.paragraphs
            )
            
        raise ValueError("Unsupported file type.")
    
    @staticmethod
    def _preprocess_text(text: str):
        # remove trailing space
        text = text.strip()
        # remove tab spaces
        text = text.replace("\t", " ")
        # remove invisible unicode chars
        text = re.sub(r"[\u200B-\u200D\uFEFF\u2060]", "", text)
        # normalize quotes
        text = (
            text.replace("“", '"')
                .replace("”", '"')
                .replace("‘", "'")
                .replace("’", "'")
        )
        # normalize hyphen/dashes
        text = (
            text.replace("–", "-")
                .replace("—", "-")
                .replace("−", "-")
        )
        # normalize multiple spaces
        text = re.sub(r" {2,}", " ", text)
        # normalize blank lines
        text = re.sub(r"\n\s*\n+", "\n\n", text)
        # merge ocr-broken words
        text = re.sub(r"(\w)-\n(\w)", r"\1\2", text)
        # normalize line endings
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        # final trim
        text = text.strip()
        return text
    
    @staticmethod
    def _split_into_chunks(text, chunk_size = 2000, offset = 200):
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + chunk_size
            chunks.append(text[start:end])
            
            if end >= len(text):
                break
            
            start = end - offset
            
        return chunks
    
    @staticmethod
    def _build_prompt():
        return """
        You are an expert notes editor.

        Clean the provided notes while preserving the original meaning and structure.

        Instructions:

        - Correct spelling and grammar mistakes.
        - Improve readability and sentence flow.
        - Preserve the original meaning.
        - Do not summarize or omit substantive information.
        - Do not add or invent new information.
        - Preserve the logical structure of headings, subheadings, and sections —
          but express them as plain, clearly formatted text. Do not keep raw
          markdown symbols such as #, ##, *, **, _, or backticks used purely for
          styling.
        - Preserve bullet points and numbered lists as clean lists, without
          leading markdown bullet characters like * or -.
        - Preserve tables in their original layout whenever possible.
        - Preserve code blocks exactly as written, including their content.
        - Remove decorative divider lines such as ---, ***, ___, or any other
          horizontal rule used only for visual separation.
        - Remove document chrome that is not part of the actual notes: footers,
          page numbers, watermarks, boilerplate labels (e.g. "Footer:", "Page 1
          of 5"), and repeated titles used as running headers.
        - Remove OCR artifacts and scanning errors.
        - Remove duplicated lines caused by OCR.
        - Remove unnecessary extra spaces and blank lines.
        - Normalize punctuation and quotation marks.
        - Keep the same language as the input.
        - Return only the cleaned notes as plain readable text — no markdown
          syntax, no raw symbols used for formatting.
        """
            
    @staticmethod
    def _clean_chunk(chunk, prompt):
        final_prompt = f"{prompt}\n\nNotes:\n{chunk}"
        
        try:
            response = NotesCleaner.client.generate(final_prompt)
            if not response or not response.strip():
                raise ValueError("Gemini returned an empty response.")
            return response.strip()
        except Exception as e:
            raise ValueError(f"API Failed: {e}") from e
        
    @staticmethod
    async def _clean_chunks_parallel(chunks: list[str], prompt: str):
        tasks = [asyncio.to_thread(NotesCleaner._clean_chunk, chunk, prompt) for chunk in chunks]
        
        cleaned_chunks = await asyncio.gather(*tasks)
        return cleaned_chunks
    
    @staticmethod
    def _merge_chunks(cleaned_chunks):
        return "\n\n".join(chunk.strip() for chunk in cleaned_chunks if chunk.strip())
    
    @staticmethod
    def _final_clean(response):
        prompt = f"""
        The following document has already been cleaned.

        Your task:

        • Remove duplicated headings

        • Make formatting consistent

        • Improve document flow

        • Do not rewrite unnecessarily

        • Do not remove information

        Return only the final cleaned notes.
        
        Document:
        {response}
        """
        
        try:
            final_result = NotesCleaner.client.generate(prompt)
            if not final_result or not final_result.strip():
                raise ValueError("Gemini returned an empty response.")
            return final_result.strip()
        
        except Exception as e:
            raise ValueError(f"API Failed: {e}") from e
        
    @staticmethod
    def _parse_response(cleaned_notes: str) -> NotesCleanerResponse:

        if not cleaned_notes or not cleaned_notes.strip():
            raise ValueError("Cleaned notes cannot be empty.")

        lines = cleaned_notes.strip().splitlines()

        title = "Cleaned Notes"

        for line in lines:
            line = line.strip()
            if line:
                title = line
                break

        return NotesCleanerResponse(
            title=title,
            cleaned_notes=cleaned_notes.strip()
        )
        
    @staticmethod
    async def _clean_notes(user: None, request: NotesCleanerRequest, file: UploadFile | None = None) -> NotesCleanerResponse:
        source, data = await NotesCleaner._validate_request(request, file)
        
        if source != "text":
            text = NotesCleaner._extract_text(data['content'], data['extension'])
        else:
            text = request.text
            
        text = NotesCleaner._preprocess_text(text)
        
        chunks = NotesCleaner._split_into_chunks(text)
        
        prompt = NotesCleaner._build_prompt()
        
        cleaned_chunks = await NotesCleaner._clean_chunks_parallel(chunks, prompt)
        
        merged_text = NotesCleaner._merge_chunks(cleaned_chunks)
        
        final_text = NotesCleaner._final_clean(merged_text)
        
        return NotesCleaner._parse_response(final_text)