"""
app/services/table_extractor/paddle_client.py
---------------------------------------------
Singleton wrapper around PaddleOCR's table structure recognition and
general-purpose OCR engines.

Responsibilities
----------------
- Own the model lifecycle (lazy init, singleton reuse)
- Run table structure recognition on a PIL image
- Run OCR on a PIL image
- Normalize all raw Paddle predictions into domain types
  (TableStructure, OCRItem, OcrResult) so that extractor.py and
  parser.py are completely insulated from PaddleOCR internals

No business logic, no formatting, no file I/O.
"""

from __future__ import annotations

import logging
import os
import re
import time
import unicodedata
from typing import List, Optional, Sequence, Tuple

import numpy as np
from PIL import Image

from app.models.table_extractor import OcrResult
from app.services.table_extractor.parser import (
    BoundingBox,
    OCRItem,
    TableCellGeometry,
    TableStructure,
)

logger = logging.getLogger(__name__)

# Use most of the available cores, leaving headroom for the web server's
# own request handling threads.
DEFAULT_CPU_THREADS: int = max(1, (os.cpu_count() or 4) - 1)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _pil_to_numpy(image: Image.Image) -> np.ndarray:
    """Convert a PIL Image to a uint8 numpy array (RGB)."""
    return np.array(image.convert("RGB"), dtype=np.uint8)


# UI-icon glyphs that OCR occasionally misreads from graphical elements
# (Excel AutoFilter dropdown arrows, checkbox/checkmark icons, sort
# indicators) rather than actual text content. Rather than enumerate
# specific codepoints (different OCR runs can produce different Unicode
# characters for the same visual icon — triangle variants, checkmark
# variants, etc. — enumeration reliably misses some), filter by Unicode
# general category instead: virtually all such icon glyphs fall under
# "So" (Symbol, other) — arrows, triangles, checkmarks, dingbats,
# geometric shapes. Real table content never uses this category: currency
# symbols are "Sc", percent/comma/period/apostrophe are "Po", hyphens are
# "Pd", letters are "L*", digits are "Nd". "\u221A" (square root, "Sm")
# is added explicitly since it's the one common exception — PaddleOCR
# sometimes misreads checkmark-style icons as it despite the different
# category.
_DECORATIVE_GLYPH_CATEGORIES = frozenset({"So"})
_DECORATIVE_GLYPH_CHARS = frozenset({"\u221A"})  # square root, checkmark misreads


def _strip_decorative_glyphs(text: str) -> str:
    """Remove UI-icon glyphs from OCR text and collapse resulting whitespace."""
    if not text:
        return text
    cleaned = "".join(
        ch for ch in text
        if ch not in _DECORATIVE_GLYPH_CHARS
        and unicodedata.category(ch) not in _DECORATIVE_GLYPH_CATEGORIES
    )
    return " ".join(cleaned.split())


def _bbox_from_points(
    points: Sequence[Sequence[float]],
) -> Optional[BoundingBox]:
    """
    Build an axis-aligned BoundingBox from four polygon points.

    Supports:
    - list[list[float]]
    - tuple[tuple[float]]
    - numpy.ndarray (PaddleOCR 3.x)
    """
    try:
        if points is None or len(points) < 4:
            return None

        xs = [float(point[0]) for point in points]
        ys = [float(point[1]) for point in points]

        x1 = min(xs)
        y1 = min(ys)
        x2 = max(xs)
        y2 = max(ys)

        if x2 <= x1 or y2 <= y1:
            return None

        return BoundingBox(
            x1=x1,
            y1=y1,
            x2=x2,
            y2=y2,
        )

    except Exception:
        return None


def _bbox_from_xyxy(coords: Sequence[float]) -> Optional[BoundingBox]:
    """
    Build a BoundingBox from PaddleOCR cell coordinates.

    Supported formats
    -----------------
    PaddleOCR 2.x:
        [x1, y1, x2, y2]

    PaddleOCR 3.x:
        [x1, y1, x2, y2, x3, y3, x4, y4]
    """
    try:
        coords = [float(v) for v in coords]

        # --------------------------------------------------
        # PaddleOCR 2.x
        # --------------------------------------------------
        if len(coords) == 4:
            x1, y1, x2, y2 = coords

        # --------------------------------------------------
        # PaddleOCR 3.x
        # --------------------------------------------------
        elif len(coords) == 8:
            xs = coords[0::2]
            ys = coords[1::2]

            x1 = min(xs)
            y1 = min(ys)
            x2 = max(xs)
            y2 = max(ys)

        else:
            return None

        if x2 <= x1 or y2 <= y1:
            return None

        return BoundingBox(
            x1=x1,
            y1=y1,
            x2=x2,
            y2=y2,
        )

    except Exception:  # noqa: BLE001
        return None


# ---------------------------------------------------------------------------
# HTML → TableStructure
# ---------------------------------------------------------------------------

# Pattern that matches a <td> or <th> tag with optional rowspan/colspan attrs.
_TD_PATTERN = re.compile(
    r"<(td|th)([^>]*)>",
    re.IGNORECASE,
)
_ROWSPAN_PATTERN = re.compile(r'rowspan=["\']?(\d+)["\']?', re.IGNORECASE)
_COLSPAN_PATTERN = re.compile(r'colspan=["\']?(\d+)["\']?', re.IGNORECASE)


def _parse_html_to_structure(
    html: str,
    bboxes: Sequence[Sequence[float]],
) -> Optional[TableStructure]:
    """
    Convert the HTML string produced by SLANet and the parallel list of
    cell bounding boxes into a TableStructure understood by TableParser.

    SLANet returns:
      html  – a string like "<table><tr><td></td><td></td></tr>...</table>"
      bboxes – a list of [x1, y1, x2, y2] boxes, one per <td>/<th> in order

    We reconstruct the grid by replaying the HTML row-by-row and tracking
    which (row, col) slots are already occupied by previous rowspan cells.
    """
    cells: List[TableCellGeometry] = []
    occupied: dict[Tuple[int, int], bool] = {}  # tracks rowspan carry-overs
    bbox_iter = iter(bboxes)

    row_idx = 0
    for row_match in re.finditer(r"<tr[^>]*>(.*?)</tr>", html, re.IGNORECASE | re.DOTALL):
        row_html = row_match.group(1)
        col_idx = 0

        for td_match in _TD_PATTERN.finditer(row_html):
            attrs = td_match.group(2)
            is_header = td_match.group(1).lower() == "th"

            rowspan_m = _ROWSPAN_PATTERN.search(attrs)
            colspan_m = _COLSPAN_PATTERN.search(attrs)
            rowspan = int(rowspan_m.group(1)) if rowspan_m else 1
            colspan = int(colspan_m.group(1)) if colspan_m else 1

            # Advance col_idx past any slots already occupied by a rowspan
            while occupied.get((row_idx, col_idx)):
                col_idx += 1

            try:
                raw_bbox = next(bbox_iter)
                bbox = _bbox_from_xyxy(raw_bbox)
            except StopIteration:
                bbox = None

            if bbox is None:
                bbox = BoundingBox(0.0, 0.0, 0.0, 0.0)

            row_end = row_idx + rowspan - 1
            col_end = col_idx + colspan - 1

            cells.append(
                TableCellGeometry(
                    bbox=bbox,
                    row_start=row_idx,
                    row_end=row_end,
                    col_start=col_idx,
                    col_end=col_end,
                    is_header=is_header if is_header else None,
                )
            )

            # Mark all (row, col) slots this cell occupies as taken
            for dr in range(rowspan):
                for dc in range(colspan):
                    occupied[(row_idx + dr, col_idx + dc)] = True

            col_idx += colspan

        row_idx += 1

    if not cells:
        logger.debug("HTML parser produced no cells from table HTML.")
        return None

    return TableStructure(cells=cells)


# ---------------------------------------------------------------------------
# Singleton Client
# ---------------------------------------------------------------------------


class PaddleTableClient:
    """
    Singleton wrapper around PaddleOCR's table structure and OCR engines.

    Both models are initialized lazily on first use so that import time
    stays fast and GPU memory is only claimed when actually needed.

    Public interface consumed by extractor.py
    -----------------------------------------
    run_table_detection(image) -> List[TableStructure]
    run_ocr(image)             -> OcrResult
    """

    _instance: Optional["PaddleTableClient"] = None
    _table_model = None  # TableStructureRecognition
    _ocr_model = None    # PaddleOCR (text + layout)

    # ------------------------------------------------------------------
    # Singleton
    # ------------------------------------------------------------------

    def __new__(cls) -> "PaddleTableClient":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    # ------------------------------------------------------------------
    # Lazy model accessors
    # ------------------------------------------------------------------

    @property
    def _table(self):
        """Lazily initialize SLANet table structure model."""
        if self._table_model is None:
            from paddleocr import TableStructureRecognition  # noqa: PLC0415

            logger.info("Initializing PaddleOCR TableStructureRecognition (SLANet)…")
            self._table_model = TableStructureRecognition(
                model_name="SLANet",
                enable_mkldnn=False,
                cpu_threads=DEFAULT_CPU_THREADS,
            )
            logger.info("TableStructureRecognition ready.")
        return self._table_model

    @property
    def _ocr(self):
        """Lazily initialize PaddleOCR text recognition engine."""
        if self._ocr_model is None:
            from paddleocr import PaddleOCR  # noqa: PLC0415

            logger.info("Initializing PaddleOCR text engine…")
            self._ocr_model = PaddleOCR(
                use_angle_cls=True,
                lang="en",
                enable_mkldnn=False,
                cpu_threads=DEFAULT_CPU_THREADS,
                text_detection_model_name="PP-OCRv5_mobile_det",
                text_recognition_model_name="PP-OCRv5_mobile_rec",
            )
            logger.info("PaddleOCR text engine ready.")
        return self._ocr_model

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def run_table_detection(self, image: Image.Image) -> List[TableStructure]:
        """
        Detect table structure in a PIL image.

        Runs SLANet table structure recognition and converts the raw
        HTML + bounding-box output into a list of TableStructure objects.
        One TableStructure is produced per table detected on the page.

        Returns an empty list if no tables are found or an error occurs.
        """
        img_array = _pil_to_numpy(image)
        start = time.monotonic()

        try:
            raw = self._table.predict(img_array)
        except Exception as exc:  # noqa: BLE001
            logger.error("SLANet prediction failed: %s", exc, exc_info=True)
            return []
        finally:
            logger.info("run_table_detection: predict() took %.3fs", time.monotonic() - start)

        structures: List[TableStructure] = []

        # raw is typically a list of result dicts, one per detected table.
        # Each dict has keys: "html" (str) and "bbox" (list of [x1,y1,x2,y2]).
        if not isinstance(raw, (list, tuple)):
            raw = [raw]

        for item in raw:
            structure = self._normalize_table_prediction(item)
            if structure is not None:
                structures.append(structure)

        logger.debug(
            "run_table_detection: %d table structure(s) extracted.", len(structures)
        )
        return structures

    def run_ocr(self, image: Image.Image, skip_preprocessing: bool = False) -> OcrResult:
        """
        Run general-purpose OCR on a PIL image.

        ``skip_preprocessing=True`` disables document-orientation
        classification, unwarping, and textline-orientation for this call
        only — these three extra models add significant latency and are
        wasted work on clean digital exports (screenshots, PDF exports).
        Leave it False for scanned/photographed pages, which may actually
        need them. The underlying model instance is unaffected either way;
        these are per-call PaddleOCR pipeline flags, not construction-time
        settings, so no model reload happens when this varies request to
        request.
        """
        img_array = _pil_to_numpy(image)
        start = time.monotonic()

        try:
            if skip_preprocessing:
                raw = self._ocr.predict(
                    img_array,
                    use_doc_orientation_classify=False,
                    use_doc_unwarping=False,
                    use_textline_orientation=False,
                )
            else:
                raw = self._ocr.predict(img_array)
        except Exception as exc:  # noqa: BLE001
            logger.error("PaddleOCR.ocr() failed: %s", exc, exc_info=True)
            return OcrResult(data=[], item_count=0)
        finally:
            logger.info(
                "run_ocr: predict() took %.3fs (skip_preprocessing=%s)",
                time.monotonic() - start, skip_preprocessing,
            )

        ocr_items = self._normalize_ocr_result(raw)
        logger.debug("run_ocr: %d OCR item(s) recognized.", len(ocr_items))
        return OcrResult(data=ocr_items, item_count=len(ocr_items))

    # ------------------------------------------------------------------
    # Normalization helpers
    # ------------------------------------------------------------------
    def _normalize_table_prediction(self, raw_item) -> Optional[TableStructure]:
        """
        Convert a single SLANet prediction into a TableStructure.

        Supports both PaddleOCR 2.x and 3.x outputs.

        PaddleOCR 2.x:
            {
                "html": "<table>...</table>",
                "bbox": [[x1,y1,x2,y2], ...]
            }

        PaddleOCR 3.x:
            {
                "structure": ["<html>", "<body>", ...],
                "bbox": [[x1,y1,x2,y2,x3,y3,x4,y4], ...],
                "structure_score": ...
            }

        Older versions may also return:
            (html, bbox)
        """
        try:
            html = ""
            bboxes = []

            if isinstance(raw_item, dict):

                # ----------------------------
                # PaddleOCR 2.x
                # ----------------------------
                if "html" in raw_item:
                    html = raw_item.get("html") or ""

                # ----------------------------
                # PaddleOCR 3.x
                # ----------------------------
                elif "structure" in raw_item:
                    structure = raw_item.get("structure") or []

                    if isinstance(structure, list):
                        html = "".join(str(token) for token in structure)
                    else:
                        html = str(structure)

                bboxes = raw_item.get("bbox") or []

            # ----------------------------------
            # Legacy tuple format
            # ----------------------------------
            elif isinstance(raw_item, (list, tuple)) and len(raw_item) == 2:

                html = str(raw_item[0]) if raw_item[0] else ""
                bboxes = list(raw_item[1]) if raw_item[1] else []

            else:
                logger.warning(
                    "Unexpected SLANet result type: %s",
                    type(raw_item).__name__,
                )
                return None

            if not html.strip():
                logger.debug("SLANet returned empty HTML.")
                return None

            logger.debug(
                "Normalized table prediction | html_length=%d | cells=%d",
                len(html),
                len(bboxes),
            )

            return _parse_html_to_structure(html, bboxes)

        except Exception as exc:  # noqa: BLE001
            logger.error(
                "Failed to normalize table prediction: %s",
                exc,
                exc_info=True,
            )
            return None

    def _normalize_ocr_result(self, raw) -> List[OCRItem]:
        """
        Normalize PaddleOCR results into a list of OCRItem objects.

        Supports:
        - PaddleOCR 3.x (predict())
        - PaddleOCR 2.x (ocr())
        """
        items: List[OCRItem] = []

        if not raw:
            return items

        try:
            # ==========================================================
            # PaddleOCR 3.x
            # ==========================================================
            if isinstance(raw, list) and raw and isinstance(raw[0], dict):

                result = raw[0]

                texts = result.get("rec_texts", [])
                scores = result.get("rec_scores", [])
                polys = result.get("dt_polys", [])

                for text, score, poly in zip(texts, scores, polys):

                    text = _strip_decorative_glyphs(str(text).strip())

                    if not text:
                        continue

                    bbox = _bbox_from_points(poly)
                    if bbox is None:
                        continue

                    items.append(
                        OCRItem(
                            text=text,
                            confidence=float(score),
                            bbox=bbox,
                        )
                    )

                return items

            # ==========================================================
            # PaddleOCR 2.x (legacy)
            # ==========================================================
            lines = raw[0] if isinstance(raw[0], list) else raw

            for detection in lines:

                try:
                    if not detection or len(detection) < 2:
                        continue

                    points = detection[0]
                    recognition = detection[1]

                    if not recognition or len(recognition) < 2:
                        continue

                    text = _strip_decorative_glyphs(str(recognition[0]).strip())

                    if not text:
                        continue

                    bbox = _bbox_from_points(points)
                    if bbox is None:
                        continue

                    items.append(
                        OCRItem(
                            text=text,
                            confidence=float(recognition[1]),
                            bbox=bbox,
                        )
                    )

                except Exception as exc:
                    logger.debug(
                        "Skipping malformed OCR detection: %s",
                        exc,
                    )

        except Exception as exc:
            logger.error(
                "Failed to normalize OCR results: %s",
                exc,
                exc_info=True,
            )

        logger.debug("Normalized %d OCR items.", len(items))
        return items