from app.models.code_reviewer import *
from fastapi import UploadFile, HTTPException, status
from typing import Optional
from pathlib import Path
import re, tempfile, lizard, json, os
from app.services.LLM_Gateway.llm_config import gateway
from app.models.gateway import LLMRequest
from pydantic import ValidationError
from sqlalchemy.orm import Session
from app.services.tool_executor import ExecutionService
from app.services.tool_service import ToolService

class CodeReview:
    
    SUPPORTED_FILE_TYPES = ['py', 'java', 'cpp', 'c', 'js', 'jsx', 'rs']
    MAX_FILE_SIZE = 10 * 1024 * 1024
    MAX_SNIPPET_LENGTH = 50_000
    chunk_size = 150
    overlap = 20
    AI_MAX_CHARS = 50_000
    client = gateway
    
    EXTENSION_TO_LANGUAGE = {
        "py": "python",
        "java": "java",
        "c": "c",
        "cpp": "cpp",
        "js": "javascript",
        "jsx": "javascript",
        "rs": "rust",
    }
    
    @staticmethod
    async def _validate_input(request: CodeReviewRequest, uploaded_file: Optional[UploadFile] = None):
        
        normalized_code = request.code.strip() if request.code else None
        
        has_snippet = bool(request.code and request.code.strip())
        has_file = uploaded_file is not None
        
        if has_snippet and has_file:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Provide either a code snippet or a single source file, not both."
            )
        
        if not has_snippet and not has_file:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A code snippet or a single source file is required."
            )
            
        # Snippet 
        if has_snippet:
            if len(normalized_code) > CodeReview.MAX_SNIPPET_LENGTH:
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail=f"Code snippet exceeds the maximum length of {CodeReview.MAX_SNIPPET_LENGTH:,} characters.",
                )

            return {
                "input_type": ReviewInputType.SNIPPET,
                "code": normalized_code,
                "file": None,
                "filename": None,
                "extension": None,
                "file_size": None,
                "language": request.language,
            }

        # File Uploading
        if not uploaded_file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Uploaded file must have a valid filename.",
            )
        
        extension = Path(uploaded_file.filename).suffix.lower().lstrip(".")
        
        if extension not in CodeReview.SUPPORTED_FILE_TYPES:
            supported = ", ".join(
                f".{ext}" for ext in sorted(CodeReview.SUPPORTED_FILE_TYPES)
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported file type. Supported file types: {supported}.",
            )

        contents = await uploaded_file.read()
        file_size = len(contents)
        await uploaded_file.seek(0)

        if file_size > CodeReview.MAX_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"Uploaded file exceeds the maximum size of {CodeReview.MAX_FILE_SIZE // (1024 * 1024)} MB.",
            )
            
        return {
            "input_type": ReviewInputType.FILE,
            "code": None,
            "file": uploaded_file,
            "filename": uploaded_file.filename,
            "extension": extension,
            "file_size": file_size,
            "language": request.language,
        }
        
    @staticmethod
    async def _read_source(validated_input: dict) -> dict:
        """
        Reads the source code and returns a normalized source descriptor.
        This method performs NO analysis.
        """

        if validated_input["input_type"] == ReviewInputType.SNIPPET:
            return {
                "input_type": validated_input["input_type"],
                "source_code": validated_input["code"],
                "filename": None,
                "extension": None,
                "file_size": len(validated_input["code"].encode("utf-8")),
                "language": validated_input["language"],
            }

        uploaded_file = validated_input["file"]

        try:
            source_code = (await uploaded_file.read()).decode("utf-8")
        except UnicodeDecodeError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unsupported file encoding. Please upload a UTF-8 encoded source file.",
            )
        finally:
            await uploaded_file.seek(0)

        return {
            "input_type": validated_input["input_type"],
            "source_code": source_code,
            "filename": validated_input["filename"],
            "extension": validated_input["extension"],
            "file_size": validated_input["file_size"],
            "language": validated_input["language"],
        }
        
    @staticmethod
    def _detect_lang_from_snippet(code: str) -> str:
        lower = code.lower()  # use 'lower' separately, keep original 'code' for regex

        # Python — check FIRST since it's most common and has strong signals
        if (
            re.search(r"^\s*def\s+\w+", code, re.MULTILINE)
            or re.search(r"^\s*class\s+\w+", code, re.MULTILINE)
            or "__name__" in code
            or "self." in lower
            or re.search(r"^\s*import\s+\w+", code, re.MULTILINE)
            or re.search(r"^\s*from\s+\w+\s+import", code, re.MULTILINE)
        ):
            return "python"

        # Java
        if (
            "public class" in lower
            or "import java" in lower
            or "system.out.println" in lower
            or re.search(r"\bpackage\s+[a-z0-9_.]+;", lower)
        ):
            return "java"

        # Rust
        if (
            re.search(r"\bfn\s+\w+", code)
            or "println!" in code
            or "let mut " in lower
            or "use std::" in lower
        ):
            return "rust"

        # JavaScript
        if (
            "=>" in code
            or "console.log" in lower
            or "function " in lower
            or "const " in lower
            or "let " in lower
            or "var " in lower
        ):
            return "javascript"

        # C++
        if (
            "#include <iostream>" in lower
            or "std::" in lower
            or "cout <<" in lower
            or "cin >>" in lower
        ):
            return "cpp"

        # C
        if (
            "#include <stdio.h>" in lower
            or "printf(" in lower
            or "scanf(" in lower
        ):
            return "c"

        return "unknown"
    
    @staticmethod
    def _detect_language_and_collect_metadata(data: dict):
        if data["language"] != ProgrammingLanguage.AUTO:
            lang = data["language"]
        
        elif data["input_type"] == ReviewInputType.FILE:
            lang = CodeReview.EXTENSION_TO_LANGUAGE[data["extension"]]
            
        elif data["input_type"] == ReviewInputType.SNIPPET:
            lang = CodeReview._detect_lang_from_snippet(data["source_code"])
            
        LOC = len((data["source_code"] or "").splitlines())
        
        file_size = data["file_size"]
        file_size_in_KB = file_size / 1024
        file_size_in_MB = file_size / (1024*1024)
        
        return {
            "source_code": data["source_code"],
            "filename": data["filename"],
            "extension": data["extension"],
            "input_type": data["input_type"],
            "language": lang,
            "LOC": LOC,
            "File_Size": file_size,
            "File_Size_in_MB": file_size_in_MB,
        }
        
    @staticmethod
    def _split_into_chunks(metadata: dict):
        chunks = []
        code_by_line = (metadata['source_code']).splitlines()
        chunk_id = 1
        start = 0
        L = len(code_by_line)
        
        while start < L:
            end = min(start + CodeReview.chunk_size, L)
            code_chunk = code_by_line[start:end]
            chunk = '\n'.join(code_chunk)
            chunks.append(
                {
                    "id": f"c{chunk_id}",
                    "start_line": start + 1,
                    "end_line": end,
                    "chunk": chunk
                }
            )
            start += CodeReview.chunk_size - CodeReview.overlap
            chunk_id += 1
        print(len(chunks))
        return {
            **metadata,
            "chunks": chunks
        }
        
    @staticmethod
    def _cyclomatic_complexity(metadata: dict):
        extension = metadata["extension"]
        
        if extension is None:
            LANGUAGE_TO_EXT = {
                "python": "py",
                "javascript": "js",
                "java": "java",
                "c": "c",
                "cpp": "cpp",
                "rust": "rs",
            }
            lang = str(metadata.get("language", "")).lower()
            extension = LANGUAGE_TO_EXT.get(lang, "py")  # default to .py if truly unknown

        
        with tempfile.NamedTemporaryFile(
            suffix=f".{extension.lstrip('.')}",
            mode="w",
            encoding="utf-8",
            delete=False,
        ) as temp:

            temp.write(metadata["source_code"])
            temp_path = temp.name
        try:
            analysis = lizard.analyze_file(temp.name)
        finally:
            os.unlink(temp_path) 

        functions = []

        total_complexity = 0

        for func in analysis.function_list:

            complexity = func.cyclomatic_complexity

            total_complexity += complexity

            functions.append(
                {
                    "name": func.name,
                    "start_line": func.start_line,
                    "end_line": func.end_line,
                    "cyclomatic_complexity": complexity,
                }
            )

        max_complexity = (
            max(f["cyclomatic_complexity"] for f in functions)
            if functions
            else 0
        )

        average_complexity = (
            round(total_complexity / len(functions), 2)
            if functions
            else 0
        )

        return {
            "functions": functions,
            "max_complexity": max_complexity,
            "average_complexity": average_complexity,
        }
        
    @staticmethod
    def _build_local_report(
        metadata: dict,
        cyclomatic: dict,
    ) -> dict:
        """
        Builds the deterministic local analysis report.
        """

        return {
            "language": metadata["language"],
            "lines_of_code": metadata["LOC"],
            "file_size": round(metadata["File_Size_in_MB"], 2),
            "cyclomatic_complexity": {
                "maximum": cyclomatic["max_complexity"],
                "average": cyclomatic["average_complexity"],
            },
        }
        
    @staticmethod
    def _build_prompt(local_report: dict, chunks: list[dict]):
        AI_REVIEW_PROMPT = """
            You are an expert senior software engineer performing a professional code review.

            Review the provided source code using both:
            1. The local analysis report.
            2. The complete source code chunks.

            Instructions:

            - Explain what the code does and its overall approach.
            - Estimate the overall Time Complexity.
            - Estimate the overall Space Complexity.
            - Identify logical bugs, runtime issues, edge cases, bad practices, potential syntax mistakes, security concerns, performance problems, and maintainability issues.
            - Return ONLY the most important findings.
            - Do NOT rewrite or fix the code.
            - Do NOT generate corrected code.
            - Do NOT mention the local analysis report.
            - Do NOT repeat information already provided in the local report unless it is necessary for your reasoning.

            Limits:

            - Summary: One concise but detailed paragraph(maximum 5 sentences) explaining what the code does and its overall approach.
            - Errors: Minimum 0, Maximum 5. Each error description must be exactly of 6-7 words.
            - Suggestions: Minimum 0, Maximum 5. Each suggestion description must be exactly of 6-7 words.
            - Time and space complexity: only return the value as O(...) not the whole explanation.
            Return ONLY valid JSON matching this schema:

            {
                "summary": "string",
                "time_complexity": "string",
                "space_complexity": "string",
                "errors": [
                    {
                        "title": "string",
                        "description": "string"
                    }
                ],
                "suggestions": [
                    {
                        "title": "string",
                        "description": "string"
                    }
                ]
            }

            Do not include markdown.
            Do not wrap the JSON in backticks.
            Do not return any explanation outside the JSON.
            """.strip()

        prompt = [
            AI_REVIEW_PROMPT,
            "",
            "========== LOCAL ANALYSIS ==========",
            f"Language: {local_report['language']}",
            f"Lines of Code: {local_report['lines_of_code']}",
            f"File Size: {local_report['file_size']} MB",
            (
                "Cyclomatic Complexity: "
                f"Maximum={local_report['cyclomatic_complexity']['maximum']}, "
                f"Average={local_report['cyclomatic_complexity']['average']}"
            ),
            "",
            "========== SOURCE CODE ==========",
        ]

        for chunk in chunks:
            prompt.extend(
                [
                    "",
                    f"===== Chunk {chunk['id']} "
                    f"(Lines {chunk['start_line']}-{chunk['end_line']}) =====",
                    chunk["chunk"],
                ]
            )

        return "\n".join(prompt)
    
    @staticmethod
    async def _call_ai(prompt):
        try:
            # Use generate_json instead of generate
            request = LLMRequest(
                prompt=prompt,
                temperature=0.3,
                max_tokens=10000,
                response_schema="json" ,
                tool_slug="code_reviewer", # important for your schema
            )
            data = await CodeReview.client.generate(request)
            if not data:
                raise ValueError("AI returned an empty response.")
            return data  # already a dict, no need to json.loads
        except Exception as e:
            raise ValueError(f"Error: {e}") from e
        
    @staticmethod
    def _parse_ai_review(raw_response: str) -> AIReviewResult:

        if not raw_response:
            raise ValueError("AI returned an empty response.")
        
        if isinstance(raw_response, str):
            raw_response = raw_response.strip()
            if not raw_response:
                raise ValueError("AI returned an empty response.")
            try:
                data = json.loads(raw_response)
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON returned by AI: {e}") from e
        else:
            data = raw_response

        try:
            review = AIReviewResult.model_validate(data)  # ← was CodeReviewResponse
        except ValidationError as e:
            raise ValueError(f"AI response does not match the expected schema: {e}") from e

        if len(review.errors) > 10:
            review.errors = review.errors[:10]

        if len(review.suggestions) > 5:
            review.suggestions = review.suggestions[:5]

        return review

    @staticmethod
    async def _generate_ai_review(
        local_report: dict,
        chunks: list[dict],
    ) -> AIReviewResult:

        # Merge all chunks into one single code block
        full_code = "\n".join(chunk["chunk"] for chunk in chunks)

        prompt = CodeReview._build_prompt(
            local_report=local_report,
            chunks=[{
                "id": "full",
                "start_line": chunks[0]["start_line"],
                "end_line": chunks[-1]["end_line"],
                "chunk": full_code,
            }],
        )

        raw = await CodeReview._call_ai(prompt)
        return CodeReview._parse_ai_review(raw)
        
    @staticmethod
    async def generate_review(
        request: CodeReviewRequest,
        user_id: str,
        db: Session,
        uploaded_file: UploadFile | None = None,
        
    ) -> CodeReviewResponse:

        # Task 1
        validated_input = await CodeReview._validate_input(
            request,
            uploaded_file,
        )

        # Task 2
        source = await CodeReview._read_source(
            validated_input,
        )

        # Task 3
        metadata = CodeReview._detect_language_and_collect_metadata(
            source,
        )

        # Task 4
        cyclomatic = CodeReview._cyclomatic_complexity(
            metadata,
        )

        # Task 5
        local_report = CodeReview._build_local_report(
            metadata,
            cyclomatic,
        )

        # Task 6
        lines = metadata["source_code"].splitlines()
        chunks = [{"id": "full", "start_line": 1, "end_line": len(lines), "chunk": metadata["source_code"]}]
        ai_review = await CodeReview._generate_ai_review(
            local_report,
            chunks,
        )
        
        user_output = json.dumps({
            "summary":ai_review.summary,
            "errors": ai_review.errors,
            "suggestions": ai_review.suggestions,
            "time complexity": ai_review.time_complexity,
            "space complexity": ai_review.space_complexity,
        })
        
        tool = ToolService.get_tool_by_slug(
                db=db,
                slug="code_reviewer",
            )
        tool_id = tool.id if tool else "code_reviewer"
        execution_id = None
        try:
            execution = ExecutionService.create_execution(
                db=db,
                user_id=user_id,
                tool_id=tool_id,
                user_input=json.dumps(validated_input, default=str),
                output=user_output,
            )
            execution_id = execution.id 
        except Exception:
            pass

        # Final Response
        return CodeReviewResponse(
            language=local_report["language"],
            lines_of_code=local_report["lines_of_code"],
            file_size=local_report["file_size"],
            cyclomatic_complexity=local_report["cyclomatic_complexity"],
            time_complexity=ai_review.time_complexity,
            space_complexity=ai_review.space_complexity,
            summary=ai_review.summary,
            errors=ai_review.errors,
            suggestions=ai_review.suggestions,
            execution_id = execution_id
        )