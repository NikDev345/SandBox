"""
app/services/table_extractor/paddle_client.py
---------------------------------------------
Singleton wrapper around PaddleOCR's layout detection, table structure
recognition, and general-purpose OCR engines.

Responsibilities
----------------
- Own the model lifecycle (lazy init, singleton reuse)
- Detect individual table regions on a page (layout detection)
- Run table structure recognition on each detected table region
- Run OCR on a PIL image
- Normalize all raw Paddle predictions into domain types
  (TableStructure, OCRItem, OcrResult) so that extractor.py and
  parser.py are completely insulated from PaddleOCR internals

No business logic, no formatting, no file I/O.
"""

from __future__ import annotations

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


# Use most of the available cores, leaving headroom for the web server's
# own request handling threads.
DEFAULT_CPU_THREADS: int = max(1, (os.cpu_count() or 4) - 1)

# Minimum confidence for a layout-detected region to be treated as a table.
MIN_LAYOUT_TABLE_SCORE: float = 0.5

# Pixel margin added around each detected table region before cropping,
# so structure recognition doesn't clip cell borders that sit right at
# the layout model's predicted edge.
TABLE_CROP_MARGIN_PX: float = 6.0


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
    Build a BoundingBox from PaddleOCR cell/region coordinates.

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
        # PaddleOCR 2.x / plain xyxy
        # --------------------------------------------------
        if len(coords) == 4:
            x1, y1, x2, y2 = coords

        # --------------------------------------------------
        # PaddleOCR 3.x (4-point polygon flattened)
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

    NOTE: bboxes here are in the coordinate space of whatever image was
    passed to SLANet. If that image was a cropped table region (as it now
    is, see PaddleTableClient.run_table_detection), the caller is
    responsible for translating these bboxes back into full-page
    coordinates before OCR matching happens — see _offset_structure.
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
        return None

    return TableStructure(cells=cells)


# ---------------------------------------------------------------------------
# Singleton Client
# ---------------------------------------------------------------------------


class PaddleTableClient:
    """
    Singleton wrapper around PaddleOCR's layout detection, table structure,
    and OCR engines.

    All three models are initialized lazily on first use so that import
    time stays fast and GPU/CPU memory is only claimed when actually
    needed.

    Public interface consumed by extractor.py
    -----------------------------------------
    run_table_detection(image) -> List[TableStructure]
    run_ocr(image)             -> OcrResult
    """

    _instance: Optional["PaddleTableClient"] = None
    _layout_model = None  # LayoutDetection (finds table regions on a page)
    _table_model = None   # TableStructureRecognition (SLANet)
    _ocr_model = None     # PaddleOCR (text + layout)

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
    def _layout(self):
        """
        Lazily initialize the layout/table-region detector.

        This model finds bounding boxes of distinct table regions on a
        full page. It exists specifically so that a page containing
        multiple tables (e.g. two separate tables stacked vertically)
        gets split into per-table crops *before* structure recognition
        runs — SLANet itself has no notion of "multiple tables on one
        image" and will otherwise try to fit a single grid across
        everything it's given.
        """
        if self._layout_model is None:
            from paddleocr import LayoutDetection  # noqa: PLC0415

            self._layout_model = LayoutDetection(
                model_name="PP-DocLayout-L",
                enable_mkldnn=False,
                cpu_threads=DEFAULT_CPU_THREADS,
            )
        return self._layout_model

    @property
    def _table(self):
        """Lazily initialize SLANet table structure model."""
        if self._table_model is None:
            from paddleocr import TableStructureRecognition  # noqa: PLC0415

            self._table_model = TableStructureRecognition(
                model_name="SLANet",
                enable_mkldnn=False,
                cpu_threads=DEFAULT_CPU_THREADS,
            )
        return self._table_model

    @property
    def _ocr(self):
        """Lazily initialize PaddleOCR text recognition engine."""
        if self._ocr_model is None:
            from paddleocr import PaddleOCR  # noqa: PLC0415

            self._ocr_model = PaddleOCR(
                use_angle_cls=True,
                lang="en",
                enable_mkldnn=False,
                cpu_threads=DEFAULT_CPU_THREADS,
                text_detection_model_name="PP-OCRv5_mobile_det",
                text_recognition_model_name="PP-OCRv5_mobile_rec",
            )
        return self._ocr_model

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def run_table_detection(self, image: Image.Image) -> List[TableStructure]:
        """
        Detect table structure in a PIL image.

        First runs layout detection to find each distinct table region on
        the page. Then, for every detected region, crops the page down to
        just that region and runs SLANet structure recognition on the
        crop individually. Cell bounding boxes are translated back into
        full-page coordinates before being returned, since OCR (run
        separately, on the full page) produces bboxes in that same
        coordinate space — TableParser matches OCR items to cells purely
        by geometric overlap, so both must agree on coordinate space.

        If layout detection finds no table regions (model unavailable,
        prediction failure, or a page with no clearly boxed table), this
        falls back to treating the entire page as a single table region,
        which preserves the previous behavior for single-table pages.

        Returns an empty list if no tables are found or an error occurs.
        """
        start = time.monotonic()
        regions = self._detect_table_regions(image)

        if not regions:
            regions = [BoundingBox(0.0, 0.0, float(image.width), float(image.height))]
        else:
            print("Layout detection found %d table region(s).", len(regions))

        structures: List[TableStructure] = []

        for region_index, region in enumerate(regions, start=1):
            crop, offset_x, offset_y = self._crop_region(image, region)

            structure = self._run_structure_recognition(crop, region_index)
            if structure is None:
                continue

            structure = self._offset_structure(structure, offset_x, offset_y)
            structures.append(structure)

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

        OCR always runs on the full page image, regardless of how many
        table regions were detected — this keeps a single coordinate
        space for all OCR items, which run_table_detection's per-region
        structures are translated back into.
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
            return OcrResult(data=[], item_count=0)
        

        ocr_items = self._normalize_ocr_result(raw)
        return OcrResult(data=ocr_items, item_count=len(ocr_items))

    # ------------------------------------------------------------------
    # Layout / table-region detection
    # ------------------------------------------------------------------

    def _detect_table_regions(self, image: Image.Image) -> List[BoundingBox]:
        """
        Run layout detection and return one BoundingBox per detected
        table region, in full-page pixel coordinates, expanded by a small
        margin so structure recognition doesn't clip edge cells.

        Never raises — logs and returns an empty list on any failure so
        run_table_detection can fall back to whole-page behavior.
        """
        img_array = _pil_to_numpy(image)

        try:
            raw = self._layout.predict(img_array)
        except Exception as exc:  # noqa: BLE001
            return []

        if not isinstance(raw, (list, tuple)):
            raw = [raw]

        boxes: List[BoundingBox] = []

        for page_result in raw:
            boxes.extend(self._extract_table_boxes_from_layout_result(page_result))

        # Expand each box by a small margin and clip to page bounds so we
        # don't lose a cell border that sits exactly on the predicted edge.
        page_w, page_h = float(image.width), float(image.height)
        margined: List[BoundingBox] = []
        for box in boxes:
            expanded = box.expand(TABLE_CROP_MARGIN_PX)
            clipped = BoundingBox(
                x1=max(0.0, expanded.x1),
                y1=max(0.0, expanded.y1),
                x2=min(page_w, expanded.x2),
                y2=min(page_h, expanded.y2),
            )
            margined.append(clipped)

        return margined

    def _extract_table_boxes_from_layout_result(self, page_result) -> List[BoundingBox]:
        """
        Normalize a single LayoutDetection page result into table
        BoundingBoxes. Handles both dict-style ("boxes": [...]) and
        object-style (attribute-based) PaddleOCR result formats, since
        the exact shape varies across PaddleOCR/PaddleX versions.
        """
        boxes: List[BoundingBox] = []

        try:
            # Dict-style result (most PaddleOCR 3.x pipelines)
            if isinstance(page_result, dict):
                detections = page_result.get("boxes") or page_result.get("layout") or []
            else:
                # Object-style result — try common attribute names.
                detections = (
                    getattr(page_result, "boxes", None)
                    or getattr(page_result, "layout", None)
                    or []
                )

            for det in detections:
                label = self._get_field(det, "label", "cls_id", "category_name")
                if label is None:
                    continue
                if "table" not in str(label).lower():
                    continue

                score = self._get_field(det, "score", "confidence")
                if score is not None and float(score) < MIN_LAYOUT_TABLE_SCORE:
                    continue

                coords = self._get_field(det, "coordinate", "bbox", "coord")
                if coords is None:
                    continue

                bbox = _bbox_from_xyxy(coords)
                if bbox is not None:
                    boxes.append(bbox)

        except Exception as exc:  # noqa: BLE001
            raise ValueError(
                "Failed to normalize layout detection result: %s", exc, exc_info=True
            )

        return boxes

    @staticmethod
    def _get_field(obj, *names):
        """Fetch the first present field from a dict or object, by name."""
        for name in names:
            if isinstance(obj, dict):
                if name in obj and obj[name] is not None:
                    return obj[name]
            else:
                value = getattr(obj, name, None)
                if value is not None:
                    return value
        return None

    # ------------------------------------------------------------------
    # Cropping / coordinate translation
    # ------------------------------------------------------------------

    @staticmethod
    def _crop_region(
        image: Image.Image, region: BoundingBox
    ) -> Tuple[Image.Image, float, float]:
        """
        Crop the page image down to a single table region.

        Returns the crop plus the (x, y) offset of the crop's origin
        within the original full-page image, so cell geometry produced
        from the crop can later be translated back into page coordinates.
        """
        left = int(max(0, region.x1))
        top = int(max(0, region.y1))
        right = int(min(image.width, region.x2))
        bottom = int(min(image.height, region.y2))

        # Guard against a degenerate region collapsing to zero area.
        if right <= left or bottom <= top:
            return image, 0.0, 0.0

        crop = image.crop((left, top, right, bottom))
        return crop, float(left), float(top)

    @staticmethod
    def _offset_structure(
        structure: TableStructure, offset_x: float, offset_y: float
    ) -> TableStructure:
        """
        Translate every cell bbox in a TableStructure by (offset_x,
        offset_y), converting crop-local coordinates into full-page
        coordinates.

        This step is required whenever run_table_detection processes a
        cropped table region rather than the full page: OCR (run
        separately, see run_ocr) always produces item bboxes in full-page
        coordinates, and TableParser matches OCR items to cells purely by
        geometric overlap. Skipping this offset causes every OCR item in
        a cropped table to fail matching against its cells, since the
        two coordinate spaces would no longer agree.
        """
        if offset_x == 0.0 and offset_y == 0.0:
            return structure

        offset_cells = [
            TableCellGeometry(
                bbox=BoundingBox(
                    x1=cell.bbox.x1 + offset_x,
                    y1=cell.bbox.y1 + offset_y,
                    x2=cell.bbox.x2 + offset_x,
                    y2=cell.bbox.y2 + offset_y,
                ) if cell.bbox.area > 0 else cell.bbox,
                row_start=cell.row_start,
                row_end=cell.row_end,
                col_start=cell.col_start,
                col_end=cell.col_end,
                is_header=cell.is_header,
            )
            for cell in structure.cells
        ]

        return TableStructure(
            cells=offset_cells,
            row_count=structure.row_count,
            col_count=structure.col_count,
            header_row_indices=structure.header_row_indices,
        )

    # ------------------------------------------------------------------
    # Structure recognition (per cropped region)
    # ------------------------------------------------------------------

    def _run_structure_recognition(
        self, region_image: Image.Image, region_index: int
    ) -> Optional[TableStructure]:
        """
        Run SLANet on a single cropped table-region image and normalize
        the result into a TableStructure (still in crop-local
        coordinates — offsetting happens separately in
        run_table_detection via _offset_structure).
        """
        img_array = _pil_to_numpy(region_image)
        start = time.monotonic()

        try:
            raw = self._table.predict(img_array)
        except Exception as exc:  # noqa: BLE001
            return None

        if not isinstance(raw, (list, tuple)):
            raw = [raw]

        for item in raw:
            structure = self._normalize_table_prediction(item)
            if structure is not None:
                return structure

        return None

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
                return None

            if not html.strip():
                return None


            return _parse_html_to_structure(html, bboxes)

        except Exception as exc:  # noqa: BLE001
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
                    raise ValueError(
                        "Skipping malformed OCR detection: %s",
                        exc,
                    )

        except Exception as exc:
            raise ValueError(
                "Failed to normalize OCR results: %s",
                exc,
                exc_info=True,
            )

        return items