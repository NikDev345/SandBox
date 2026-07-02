from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.engine import get_db
from app.schemas.ai.summarizer import (
    SummarizeRequest,
    SummarizeResponse,
    ExtractResponse,
    DownloadRequest,
)
from app.services.ai.summarizer_service import SummarizerService
from fastapi import UploadFile, File, HTTPException
from fastapi.responses import StreamingResponse
import io
from pypdf import PdfReader
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from datetime import datetime

router = APIRouter(
    prefix="/summarizer",
    tags=["AI - Text Summarizer"],
)


@router.post(
    "/generate",
    response_model=SummarizeResponse,
)
def generate_summary(
    request: SummarizeRequest,
    db: Session = Depends(get_db),
):
    """
    Generate AI summary.
    """

    try:
        summary = SummarizerService.summarize(
            db=db,
            user_id='anonymous',
            text=request.text,
            length=request.length,
            instructions=request.instructions,
        )

        return SummarizeResponse(
            summary=summary
        )

    except Exception as e:
        print("Summarizer Error:", repr(e))
        raise



@router.post(
    "/extract",
    response_model=ExtractResponse,
)
def extract_text_from_file(
    file: UploadFile = File(...),
):
    """
    Extract text from uploaded document (PDF/TXT/DOCX).
    """

    try:
        content = file.file.read()

        filename = (file.filename or '').lower()
        extracted = ""
        print(f"[extract] received file={file.filename} size={len(content)} bytes")

        # PDF handling with fallbacks
        if filename.endswith('.pdf'):
            try:
                reader = PdfReader(io.BytesIO(content))
                texts = []
                for i, page in enumerate(reader.pages):
                    try:
                        t = page.extract_text() or ""
                        texts.append(t)
                        print(f"[extract][pypdf] page={i} len={len(t)}")
                    except Exception as e:
                        print(f"[extract][pypdf] page={i} error={e}")
                        texts.append("")
                extracted = "\n\n".join(texts).strip()
                print(f"[extract][pypdf] total_len={len(extracted)}")
            except Exception as e:
                print('[extract][pypdf] failed', e)
                extracted = ""

            # If extraction yielded little/no text, try pdfplumber if available
            if (not extracted or len(extracted) < 100):
                try:
                    import pdfplumber
                    print('[extract][pdfplumber] trying fallback')
                    with pdfplumber.open(io.BytesIO(content)) as pdf:
                        pages = []
                        for i, p in enumerate(pdf.pages):
                            try:
                                t = p.extract_text() or ""
                                pages.append(t)
                                print(f"[extract][pdfplumber] page={i} len={len(t)}")
                            except Exception as e:
                                print(f"[extract][pdfplumber] page={i} error={e}")
                                pages.append("")
                        extracted = "\n\n".join(pages).strip()
                    print(f"[extract][pdfplumber] total_len={len(extracted)}")
                except Exception:
                    # pdfplumber not available or failed — leave extracted as-is
                    pass

        # DOCX handling
        elif filename.endswith('.docx'):
            try:
                from docx import Document
                doc = Document(io.BytesIO(content))
                paragraphs = [p.text for p in doc.paragraphs if p.text]
                extracted = "\n\n".join(paragraphs).strip()
            except Exception:
                extracted = ""

        # Plain text fallback
        else:
            try:
                extracted = content.decode('utf-8', errors='ignore')
            except Exception:
                extracted = ""

        return ExtractResponse(text=extracted)

    except Exception as e:
        print('Extract Error:', repr(e))
        raise HTTPException(status_code=500, detail='Failed to extract file')



@router.post("/download")
def download_summary_pdf(
    request: DownloadRequest,
):
    """
    Render provided summary text into a simple PDF and return it.
    """

    try:
        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=letter)
        width, height = letter

        margin = 72
        max_width = width - margin * 2
        y = height - margin

        lines = []
        # Simple wrapping by splitting words
        for paragraph in request.summary.split('\n'):
            words = paragraph.split(' ')
            line = ''
            for w in words:
                test = (line + ' ' + w).strip()
                if c.stringWidth(test, 'Helvetica', 11) <= max_width:
                    line = test
                else:
                    lines.append(line)
                    line = w
            if line:
                lines.append(line)
            lines.append('')

        c.setFont('Helvetica', 11)
        for line in lines:
            if y < margin + 20:
                c.showPage()
                c.setFont('Helvetica', 11)
                y = height - margin
            c.drawString(margin, y, line)
            y -= 14

        # Footer
        c.setFont('Helvetica', 9)
        footer = f"Generated by AI SandBox — {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}"
        c.drawRightString(width - margin, margin - 20, footer)

        c.save()
        buffer.seek(0)

        filename = f"summary-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}.pdf"
        return StreamingResponse(buffer, media_type='application/pdf', headers={
            'Content-Disposition': f'attachment; filename="{filename}"'
        })

    except Exception as e:
        print('PDF Generation Error:', repr(e))
        raise HTTPException(status_code=500, detail='Failed to generate PDF')