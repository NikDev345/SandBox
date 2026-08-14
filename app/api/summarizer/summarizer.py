from __future__ import annotations

import io
from datetime import datetime

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    UploadFile,
)
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.database.engine import get_db
from app.models.summarizer import (
    SummarizeRequest,
    SummarizeResponse,
    ExtractResponse,
    DownloadRequest,
)
from app.utils.auth import get_current_user


router = APIRouter(
    prefix="/summarizer",
    tags=["AI - Text Summarizer"],
)


# ============================================================
# GENERATE SUMMARY
# ============================================================

@router.post(
    "/generate",
    response_model=SummarizeResponse,
)
async def generate_summary(
    request: SummarizeRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Generate an AI summary for the authenticated user.
    """

    text = request.text.strip()

    if not text:
        raise HTTPException(
            status_code=400,
            detail="Text cannot be empty.",
        )

    try:
        # Lazy import:
        # The summarizer service and LLM gateway are not loaded
        # during application startup.
        from app.services.summarizer.summarizer_service import (
            SummarizerService,
        )

        summary, execution_id = await SummarizerService.summarize(
            db=db,
            user_id=current_user["sub"],
            text=text,
            length=request.length,
            instructions=request.instructions,
        )

        return SummarizeResponse(
            summary=summary,
            execution_id=execution_id,
        )
        
    except HTTPException as e:
        raise e

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

    except Exception as exc:
        print(
            "[SUMMARIZER] Generation failed:",
            repr(exc),
        )

        raise HTTPException(
            status_code=500,
            detail="Failed to generate summary.",
        )


# ============================================================
# DOCUMENT EXTRACTION
# ============================================================

@router.post(
    "/extract",
    response_model=ExtractResponse,
)
async def extract_text_from_file(
    file: UploadFile = File(...),
):
    """
    Extract text from PDF, DOCX, or TXT files.

    Heavy document libraries are imported only when this
    endpoint is actually used.
    """

    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="No file provided.",
        )

    filename = file.filename.lower()

    allowed_extensions = (
        ".pdf",
        ".docx",
        ".txt",
    )

    if not filename.endswith(allowed_extensions):
        raise HTTPException(
            status_code=400,
            detail="Unsupported file type.",
        )

    try:
        content = await file.read()

        if not content:
            raise HTTPException(
                status_code=400,
                detail="Uploaded file is empty.",
            )

        # ----------------------------------------------------
        # PDF
        # ----------------------------------------------------

        if filename.endswith(".pdf"):

            # Lazy import
            from pypdf import PdfReader

            reader = PdfReader(
                io.BytesIO(content)
            )

            pages = []

            for page in reader.pages:
                try:
                    text = page.extract_text() or ""

                    if text.strip():
                        pages.append(text.strip())

                except Exception:
                    continue

            extracted = "\n\n".join(pages).strip()

            # Optional fallback only when necessary.
            #
            # pdfplumber is intentionally NOT imported during
            # application startup.
            if len(extracted) < 100:

                try:
                    import pdfplumber

                    with pdfplumber.open(
                        io.BytesIO(content)
                    ) as pdf:

                        fallback_pages = []

                        for page in pdf.pages:

                            try:
                                text = page.extract_text() or ""

                                if text.strip():
                                    fallback_pages.append(
                                        text.strip()
                                    )

                            except Exception:
                                continue

                        fallback_text = "\n\n".join(
                            fallback_pages
                        ).strip()

                        if len(fallback_text) > len(extracted):
                            extracted = fallback_text

                except Exception:
                    pass

        # ----------------------------------------------------
        # DOCX
        # ----------------------------------------------------

        elif filename.endswith(".docx"):

            # Lazy import
            from docx import Document

            document = Document(
                io.BytesIO(content)
            )

            paragraphs = [
                paragraph.text.strip()
                for paragraph in document.paragraphs
                if paragraph.text.strip()
            ]

            extracted = "\n\n".join(
                paragraphs
            ).strip()

        # ----------------------------------------------------
        # TXT
        # ----------------------------------------------------

        else:

            extracted = content.decode(
                "utf-8",
                errors="ignore",
            ).strip()

        if not extracted:

            raise HTTPException(
                status_code=422,
                detail="Could not extract any text from the file.",
            )

        return ExtractResponse(
            text=extracted,
        )

    except HTTPException:
        raise

    except Exception as exc:

        print(
            "[SUMMARIZER] File extraction failed:",
            repr(exc),
        )

        raise HTTPException(
            status_code=500,
            detail="Failed to extract text from file.",
        )


# ============================================================
# DOWNLOAD SUMMARY AS PDF
# ============================================================

@router.post(
    "/download",
)
def download_summary_pdf(
    request: DownloadRequest,
):
    """
    Convert a generated summary into a PDF.

    ReportLab is imported only when the user clicks
    Download PDF.
    """

    summary = request.summary.strip()

    if not summary:
        raise HTTPException(
            status_code=400,
            detail="Summary cannot be empty.",
        )

    try:

        # Lazy import
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import letter

        buffer = io.BytesIO()

        pdf = canvas.Canvas(
            buffer,
            pagesize=letter,
        )

        width, height = letter

        margin = 72
        max_width = width - (margin * 2)

        y = height - margin

        pdf.setFont(
            "Helvetica",
            11,
        )

        for paragraph in summary.split("\n"):

            words = paragraph.split()

            line = ""

            for word in words:

                test_line = (
                    f"{line} {word}"
                ).strip()

                if pdf.stringWidth(
                    test_line,
                    "Helvetica",
                    11,
                ) <= max_width:

                    line = test_line

                else:

                    if line:

                        if y < margin + 30:
                            pdf.showPage()
                            pdf.setFont(
                                "Helvetica",
                                11,
                            )
                            y = height - margin

                        pdf.drawString(
                            margin,
                            y,
                            line,
                        )

                        y -= 14

                    line = word

            if line:

                if y < margin + 30:
                    pdf.showPage()
                    pdf.setFont(
                        "Helvetica",
                        11,
                    )
                    y = height - margin

                pdf.drawString(
                    margin,
                    y,
                    line,
                )

                y -= 14

            # Paragraph spacing
            y -= 6

        # Footer
        pdf.setFont(
            "Helvetica",
            8,
        )

        timestamp = datetime.utcnow().strftime(
            "%Y-%m-%d %H:%M UTC"
        )

        pdf.drawRightString(
            width - margin,
            margin - 20,
            f"Generated by AI SandBox — {timestamp}",
        )

        pdf.save()

        buffer.seek(0)

        filename = (
            f"summary-"
            f"{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
            f".pdf"
        )

        return StreamingResponse(
            buffer,
            media_type="application/pdf",
            headers={
                "Content-Disposition":
                    f'attachment; filename="{filename}"'
            },
        )

    except Exception as exc:

        print(
            "[SUMMARIZER] PDF generation failed:",
            repr(exc),
        )

        raise HTTPException(
            status_code=500,
            detail="Failed to generate PDF.",
        )