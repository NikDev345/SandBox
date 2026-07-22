"""
Table Parser

Pure, deterministic domain service that converts already-normalized OCR
items and table structure geometry into an internal, strongly typed table
model (ParsedTable).

This module has exactly one responsibility: reconstruct table layout from
normalized input and match OCR text to cells. It has no knowledge of
PaddleOCR, HTML, file I/O, AI models, or API/response schemas. All of that
normalization is assumed to have already happened upstream (in
PaddleTableClient); this parser only ever sees domain types defined here.
"""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass, field, replace
from enum import Enum
from typing import Dict, List, Optional, Sequence, Tuple

logger = logging.getLogger(__name__)


# ------------------------------------------------------------------------------
# Configuration Constants
# ------------------------------------------------------------------------------

# Matching weights. Primary signal is intersection-over-ocr-area (how much of
# the OCR box's own area falls inside a candidate cell), not IoU, since OCR
# boxes are usually much smaller than cells and IoU under-rewards a fully
# contained OCR box next to a large cell.
WEIGHT_INTERSECTION_RATIO: float = 0.40
WEIGHT_CENTER_INSIDE: float = 0.20
WEIGHT_HORIZONTAL_OVERLAP: float = 0.10
WEIGHT_VERTICAL_OVERLAP: float = 0.15
WEIGHT_CONFIDENCE: float = 0.10
WEIGHT_DISTANCE_PENALTY: float = 0.05

# Minimum weighted score required to assign an OCR item to a cell.
MIN_MATCH_SCORE: float = 0.20

# Minimum OCR confidence to be considered for matching at all.
MIN_OCR_CONFIDENCE: float = 0.0

# Normalization divisor for the distance penalty term, expressed as a
# fraction of the cell's diagonal length. Larger values soften the penalty.
DISTANCE_PENALTY_DIAGONAL_FACTOR: float = 1.5

PARSER_VERSION: str = "2.0"


class HeaderMode(str, Enum):
    """Strategy used to determine which rows of a table are headers."""

    EXPLICIT = "explicit"
    INFER_FIRST_ROW = "infer_first_row"
    NONE = "none"
    AUTO = "auto"


@dataclass(frozen=True)
class ParserConfig:
    """Injectable configuration for TableParser."""

    weight_intersection_ratio: float = WEIGHT_INTERSECTION_RATIO
    weight_center_inside: float = WEIGHT_CENTER_INSIDE
    weight_horizontal_overlap: float = WEIGHT_HORIZONTAL_OVERLAP
    weight_vertical_overlap: float = WEIGHT_VERTICAL_OVERLAP
    weight_confidence: float = WEIGHT_CONFIDENCE
    weight_distance_penalty: float = WEIGHT_DISTANCE_PENALTY
    min_match_score: float = MIN_MATCH_SCORE
    min_ocr_confidence: float = MIN_OCR_CONFIDENCE
    distance_penalty_diagonal_factor: float = DISTANCE_PENALTY_DIAGONAL_FACTOR
    header_mode: HeaderMode = HeaderMode.AUTO


DEFAULT_PARSER_CONFIG = ParserConfig()


# ------------------------------------------------------------------------------
# Exceptions
# ------------------------------------------------------------------------------


class TableParsingError(Exception):
    """Base exception for parser failures."""


class InvalidGeometryError(TableParsingError):
    """Raised when cell or bounding box geometry is invalid."""


class InvalidStructureError(TableParsingError):
    """Raised when the overall table structure is invalid."""


# ------------------------------------------------------------------------------
# Geometry
# ------------------------------------------------------------------------------


@dataclass(frozen=True)
class BoundingBox:
    """Immutable axis-aligned bounding box."""

    x1: float
    y1: float
    x2: float
    y2: float

    def __post_init__(self) -> None:
        if self.x1 > self.x2 or self.y1 > self.y2:
            raise InvalidGeometryError(
                f"Invalid bounding box: x1={self.x1}, y1={self.y1}, "
                f"x2={self.x2}, y2={self.y2}"
            )

    @property
    def width(self) -> float:
        return self.x2 - self.x1

    @property
    def height(self) -> float:
        return self.y2 - self.y1

    @property
    def area(self) -> float:
        return max(0.0, self.width * self.height)

    @property
    def center(self) -> Tuple[float, float]:
        return ((self.x1 + self.x2) / 2.0, (self.y1 + self.y2) / 2.0)

    @property
    def diagonal(self) -> float:
        return math.hypot(self.width, self.height)

    def contains_point(self, x: float, y: float) -> bool:
        return self.x1 <= x <= self.x2 and self.y1 <= y <= self.y2

    def intersection_area(self, other: "BoundingBox") -> float:
        xl = max(self.x1, other.x1)
        xr = min(self.x2, other.x2)
        yb = max(self.y1, other.y1)
        yt = min(self.y2, other.y2)
        if xr <= xl or yt <= yb:
            return 0.0
        return (xr - xl) * (yt - yb)

    def intersection_ratio(self, other: "BoundingBox") -> float:
        """Fraction of THIS box's area that overlaps with ``other``."""
        if self.area == 0.0:
            return 0.0
        return self.intersection_area(other) / self.area

    def horizontal_overlap(self, other: "BoundingBox") -> float:
        overlap = max(0.0, min(self.x2, other.x2) - max(self.x1, other.x1))
        min_width = min(self.width, other.width)
        if min_width == 0.0:
            return 0.0
        return overlap / min_width

    def vertical_overlap(self, other: "BoundingBox") -> float:
        overlap = max(0.0, min(self.y2, other.y2) - max(self.y1, other.y1))
        min_height = min(self.height, other.height)
        if min_height == 0.0:
            return 0.0
        return overlap / min_height

    def expand(self, margin: float) -> "BoundingBox":
        return BoundingBox(
            self.x1 - margin, self.y1 - margin, self.x2 + margin, self.y2 + margin
        )

    def distance(self, other: "BoundingBox") -> float:
        cx1, cy1 = self.center
        cx2, cy2 = other.center
        return math.hypot(cx1 - cx2, cy1 - cy2)

    def union(self, other: "BoundingBox") -> "BoundingBox":
        return BoundingBox(
            min(self.x1, other.x1),
            min(self.y1, other.y1),
            max(self.x2, other.x2),
            max(self.y2, other.y2),
        )


# ------------------------------------------------------------------------------
# Input Domain Models (already normalized upstream)
# ------------------------------------------------------------------------------


@dataclass(frozen=True)
class OCRItem:
    """A single normalized OCR detection."""

    text: str
    confidence: float
    bbox: BoundingBox


@dataclass(frozen=True)
class TableCellGeometry:
    """
    Normalized geometry and grid placement for one table cell.

    Indices are zero-based and inclusive on both ends. ``is_header``, when
    provided by the upstream structure model, marks an explicit header
    cell and takes precedence over any header inference.
    """

    bbox: BoundingBox
    row_start: int
    row_end: int
    col_start: int
    col_end: int
    is_header: Optional[bool] = None

    def __post_init__(self) -> None:
        if self.row_start < 0 or self.col_start < 0:
            raise InvalidGeometryError(
                f"Negative grid index: row_start={self.row_start}, "
                f"col_start={self.col_start}"
            )
        if self.row_end < self.row_start or self.col_end < self.col_start:
            raise InvalidGeometryError(
                f"Invalid span: row {self.row_start}-{self.row_end}, "
                f"col {self.col_start}-{self.col_end}"
            )

    @property
    def row_span(self) -> int:
        return self.row_end - self.row_start + 1

    @property
    def col_span(self) -> int:
        return self.col_end - self.col_start + 1

    @property
    def is_merged(self) -> bool:
        return self.row_span > 1 or self.col_span > 1


@dataclass(frozen=True)
class TableStructure:
    """Normalized table structure: a flat collection of cell geometries."""

    cells: Sequence[TableCellGeometry]
    row_count: Optional[int] = None
    col_count: Optional[int] = None
    header_row_indices: Optional[Sequence[int]] = None


# ------------------------------------------------------------------------------
# Output Domain Models
# ------------------------------------------------------------------------------


@dataclass(frozen=True)
class TableCell:
    """A finalized cell: geometry plus matched, aggregated OCR text."""

    row_start: int
    row_end: int
    col_start: int
    col_end: int
    bbox: BoundingBox
    text: str
    confidence: float
    ocr_item_count: int
    is_header: bool
    is_merged: bool
    is_synthetic: bool = False

    @property
    def row_span(self) -> int:
        return self.row_end - self.row_start + 1

    @property
    def col_span(self) -> int:
        return self.col_end - self.col_start + 1


@dataclass(frozen=True)
class TableRow:
    """A row of finalized cells with row-level aggregate confidence."""

    index: int
    cells: Sequence[TableCell]
    is_header: bool
    confidence: float

    @property
    def text_values(self) -> List[str]:
        return [cell.text for cell in self.cells]


@dataclass(frozen=True)
class TableColumn:
    """A column of finalized cells with column-level aggregate confidence."""

    index: int
    cells: Sequence[TableCell]
    confidence: float

    @property
    def text_values(self) -> List[str]:
        return [cell.text for cell in self.cells]


@dataclass(frozen=True)
class TableMetadata:
    """Diagnostic and provenance information about a parsed table."""

    merged_cell_count: int
    synthetic_cell_count: int
    total_ocr_items: int
    matched_ocr_items: int
    unmatched_ocr_items: int
    header_row_count: int
    row_count: int
    col_count: int
    parser_version: str = PARSER_VERSION


@dataclass(frozen=True)
class ParsedTable:
    """Canonical, strongly typed parsed table."""

    page: int
    table_index: int
    rows: Sequence[TableRow]
    columns: Sequence[TableColumn]
    headers: Sequence[str]
    bbox: BoundingBox
    confidence: float
    metadata: TableMetadata


# ------------------------------------------------------------------------------
# Internal mutable working model (parser-private, never exposed)
# ------------------------------------------------------------------------------


@dataclass
class _WorkingCell:
    """Mutable accumulator used while matching OCR items to cell geometry."""

    geometry: TableCellGeometry
    matched_items: List[OCRItem] = field(default_factory=list)
    is_synthetic: bool = False

    def add(self, item: OCRItem) -> None:
        self.matched_items.append(item)

    def finalize_text(self) -> Tuple[str, float]:
        if not self.matched_items:
            return "", 0.0
        ordered = sorted(self.matched_items, key=lambda i: i.bbox.center[0])
        text = " ".join(item.text for item in ordered if item.text)
        confidence = sum(item.confidence for item in ordered) / len(ordered)
        confidence = max(0.0, min(1.0, confidence))
        return text, confidence


# ------------------------------------------------------------------------------
# Parser
# ------------------------------------------------------------------------------


class TableParser:
    """
    Reconstructs table layout and matches OCR to cells.

    Stateless and deterministic aside from the injected configuration.
    Never loads models, performs OCR, reads files, or builds API
    responses.
    """

    def __init__(self, config: ParserConfig = DEFAULT_PARSER_CONFIG) -> None:
        self._config = config

    # --------------------------------------------------------------------------
    # Public API
    # --------------------------------------------------------------------------

    def parse(
        self,
        ocr_items: Sequence[OCRItem],
        table_structure: TableStructure,
        page_number: int = 1,
        table_index: int = 1,
        header_mode: Optional[HeaderMode] = None,
    ) -> List[ParsedTable]:
        """
        Convert normalized OCR items and table structure into a
        ParsedTable. Returns an empty list if the input cannot yield a usable
        table; raises TableParsingError on structurally invalid input.
        """
        effective_header_mode = header_mode or self._config.header_mode

        self._validate_input(ocr_items, table_structure)

        eligible_ocr_items = self._filter_ocr_items(ocr_items)
        if not eligible_ocr_items:
            logger.warning(
                "No eligible OCR items for page %d, table %d.", page_number, table_index
            )

        working_cells = self._create_working_cells(table_structure.cells)
        working_cells = self._sort_cells(working_cells)

        matched_count, unmatched_count = self._match_ocr_to_cells(
            eligible_ocr_items, working_cells
        )

        grid, row_count, col_count = self._build_grid(working_cells)
        working_cells = self._fill_missing_cells(grid, working_cells, row_count, col_count)

        header_row_indices = self._detect_headers(
            table_structure, working_cells, row_count, effective_header_mode
        )

        finalized_cells = self._finalize_cells(working_cells, header_row_indices)
        finalized_grid = self._rebuild_grid_from_finalized(finalized_cells, row_count, col_count)

        rows = self._build_rows(finalized_grid, header_row_indices)
        rows = self._merge_fragmented_rows(rows)
        columns = self._build_columns(finalized_grid)

        if not rows or not columns:
            logger.warning(
                "Table reconstruction produced no rows/columns for page %d, table %d.",
                page_number, table_index,
            )
            return []

        headers = self._extract_header_texts(rows)
        table_bbox = self._compute_table_bbox(finalized_cells)
        table_confidence = self._compute_table_confidence(rows)

        metadata = TableMetadata(
            merged_cell_count=sum(1 for c in finalized_cells if c.is_merged),
            synthetic_cell_count=sum(1 for c in finalized_cells if c.is_synthetic),
            total_ocr_items=len(ocr_items),
            matched_ocr_items=matched_count,
            unmatched_ocr_items=unmatched_count,
            header_row_count=len(header_row_indices),
            row_count=len(rows),
            col_count=col_count,
        )

        logger.info(
            "Parsed table page=%d index=%d rows=%d cols=%d cells=%d "
            "matched_ocr=%d/%d confidence=%.3f",
            page_number, table_index, row_count, col_count, len(finalized_cells),
            matched_count, len(ocr_items), table_confidence,
        )

        return [ParsedTable(
            page=page_number,
            table_index=table_index,
            rows=rows,
            columns=columns,
            headers=headers,
            bbox=table_bbox,
            confidence=table_confidence,
            metadata=metadata,
        )]

    # --------------------------------------------------------------------------
    # Validation
    # --------------------------------------------------------------------------

    def _validate_input(
        self, ocr_items: Sequence[OCRItem], table_structure: TableStructure
    ) -> None:
        if table_structure is None:
            raise InvalidStructureError("table_structure must not be None.")
        if not table_structure.cells:
            raise InvalidStructureError("table_structure.cells must not be empty.")

        seen: set[Tuple[int, int, int, int]] = set()
        for cell in table_structure.cells:
            key = (cell.row_start, cell.row_end, cell.col_start, cell.col_end)
            if key in seen:
                logger.warning("Duplicate cell geometry detected at %s.", key)
            seen.add(key)

            if cell.bbox.area <= 0:
                logger.warning(
                    "Cell at row %d-%d, col %d-%d has non-positive area.",
                    cell.row_start, cell.row_end, cell.col_start, cell.col_end,
                )

        for other in table_structure.cells:
            for candidate in table_structure.cells:
                if other is candidate:
                    continue
                if self._grids_overlap(other, candidate):
                    logger.debug(
                        "Overlapping grid spans: %s and %s.",
                        (other.row_start, other.row_end, other.col_start, other.col_end),
                        (candidate.row_start, candidate.row_end,
                         candidate.col_start, candidate.col_end),
                    )

        if ocr_items is None:
            raise InvalidStructureError("ocr_items must not be None.")

    @staticmethod
    def _grids_overlap(a: TableCellGeometry, b: TableCellGeometry) -> bool:
        row_overlap = a.row_start <= b.row_end and b.row_start <= a.row_end
        col_overlap = a.col_start <= b.col_end and b.col_start <= a.col_end
        return row_overlap and col_overlap

    # --------------------------------------------------------------------------
    # OCR Filtering
    # --------------------------------------------------------------------------

    def _filter_ocr_items(self, ocr_items: Sequence[OCRItem]) -> List[OCRItem]:
        eligible: List[OCRItem] = []
        for item in ocr_items:
            if not item.text or not item.text.strip():
                continue
            if item.confidence < self._config.min_ocr_confidence:
                continue
            eligible.append(item)
        return eligible

    # --------------------------------------------------------------------------
    # Working Cell Construction
    # --------------------------------------------------------------------------

    @staticmethod
    def _create_working_cells(
        geometries: Sequence[TableCellGeometry],
    ) -> List[_WorkingCell]:
        return [_WorkingCell(geometry=geometry) for geometry in geometries]

    def _sort_cells(self, cells: List[_WorkingCell]) -> List[_WorkingCell]:
        return sorted(
            cells,
            key=lambda c: (c.geometry.row_start, c.geometry.col_start),
        )

    # --------------------------------------------------------------------------
    # Matching
    # --------------------------------------------------------------------------

    def _match_ocr_to_cells(
        self, ocr_items: Sequence[OCRItem], cells: Sequence[_WorkingCell]
    ) -> Tuple[int, int]:
        """Assign each OCR item to its single best-scoring cell."""
        matched_count = 0

        for item in ocr_items:
            best_cell: Optional[_WorkingCell] = None
            best_score = 0.0

            for cell in cells:
                score = self._compute_match_score(item, cell.geometry)
                if score > best_score:
                    best_score = score
                    best_cell = cell

            if best_cell is not None and best_score >= self._config.min_match_score:

                logger.info(
                    "OCR '%s' -> row=%d col=%d score=%.3f OCR=%s CELL=%s",
                    item.text,
                    best_cell.geometry.row_start,
                    best_cell.geometry.col_start,
                    best_score,
                    item.bbox,
                    best_cell.geometry.bbox,
                )

                best_cell.add(item)
                matched_count += 1

        unmatched_count = len(ocr_items) - matched_count
        logger.debug(
            "OCR matching complete: %d matched, %d unmatched, %d cells.",
            matched_count, unmatched_count, len(cells),
        )
        return matched_count, unmatched_count

    def _compute_match_score(self, item: OCRItem, geometry: TableCellGeometry) -> float:
        cfg = self._config

        intersection_ratio = item.bbox.intersection_ratio(geometry.bbox)
        center_x, center_y = item.bbox.center
        center_inside = 1.0 if geometry.bbox.contains_point(center_x, center_y) else 0.0
        horizontal_overlap = item.bbox.horizontal_overlap(geometry.bbox)
        vertical_overlap = item.bbox.vertical_overlap(geometry.bbox)

        # Hard gate: an item must have genuine two-dimensional proximity to
        # this cell before it's considered a candidate at all — either real
        # geometric overlap/containment, or overlap on BOTH the vertical and
        # horizontal axes independently. Gating on only one axis (e.g. "same
        # row band" alone) still lets an item with no cell of its own bleed
        # into whichever neighboring cell happens to be closest along the
        # other axis. Requiring both closes that off: an unmatched item
        # (no true cell exists for it, e.g. a missing header cell) stays
        # unmatched instead of silently merging into a neighbor's text.
        has_real_overlap = intersection_ratio > 0.0 or center_inside == 1.0
        has_axis_alignment = vertical_overlap > 0.0 and horizontal_overlap > 0.0
        if not has_real_overlap and not has_axis_alignment:
            return 0.0

        confidence = max(0.0, min(1.0, item.confidence))

        diagonal = geometry.bbox.diagonal
        if diagonal <= 0:
            distance_penalty = 1.0
        else:
            normalized_distance = item.bbox.distance(geometry.bbox) / (
                diagonal * cfg.distance_penalty_diagonal_factor
            )
            distance_penalty = max(0.0, 1.0 - min(1.0, normalized_distance))

        score = (
            cfg.weight_intersection_ratio * intersection_ratio
            + cfg.weight_center_inside * center_inside
            + cfg.weight_horizontal_overlap * horizontal_overlap
            + cfg.weight_vertical_overlap * vertical_overlap
            + cfg.weight_confidence * confidence
            + cfg.weight_distance_penalty * distance_penalty
        )
        return score

    # --------------------------------------------------------------------------
    # Grid Construction
    # --------------------------------------------------------------------------

    def _build_grid(
        self, cells: Sequence[_WorkingCell]
    ) -> Tuple[Dict[Tuple[int, int], _WorkingCell], int, int]:
        """Build a sparse (row, col) -> _WorkingCell occupancy map."""
        if not cells:
            return {}, 0, 0

        row_count = max(c.geometry.row_end for c in cells) + 1
        col_count = max(c.geometry.col_end for c in cells) + 1

        grid: Dict[Tuple[int, int], _WorkingCell] = {}
        for cell in cells:
            for r in range(cell.geometry.row_start, cell.geometry.row_end + 1):
                for c in range(cell.geometry.col_start, cell.geometry.col_end + 1):
                    grid[(r, c)] = cell

        return grid, row_count, col_count

    def _fill_missing_cells(
        self,
        grid: Dict[Tuple[int, int], _WorkingCell],
        cells: List[_WorkingCell],
        row_count: int,
        col_count: int,
    ) -> List[_WorkingCell]:
        """Create synthetic empty cells for any uncovered grid positions."""
        synthetic_cells: List[_WorkingCell] = []

        for r in range(row_count):
            for c in range(col_count):
                if (r, c) in grid:
                    continue
                synthetic_geometry = TableCellGeometry(
                    bbox=BoundingBox(0.0, 0.0, 0.0, 0.0),
                    row_start=r,
                    row_end=r,
                    col_start=c,
                    col_end=c,
                )
                synthetic_cell = _WorkingCell(geometry=synthetic_geometry, is_synthetic=True)
                grid[(r, c)] = synthetic_cell
                synthetic_cells.append(synthetic_cell)

        if synthetic_cells:
            logger.debug("Filled %d missing grid position(s).", len(synthetic_cells))

        return cells + synthetic_cells

    def _rebuild_grid_from_finalized(
        self, cells: Sequence[TableCell], row_count: int, col_count: int
    ) -> Dict[Tuple[int, int], TableCell]:
        grid: Dict[Tuple[int, int], TableCell] = {}
        for cell in cells:
            for r in range(cell.row_start, cell.row_end + 1):
                for c in range(cell.col_start, cell.col_end + 1):
                    grid[(r, c)] = cell
        return grid

    # --------------------------------------------------------------------------
    # Header Detection
    # --------------------------------------------------------------------------

    def _detect_headers(
        self,
        table_structure: TableStructure,
        cells: Sequence[_WorkingCell],
        row_count: int,
        header_mode: HeaderMode,
    ) -> List[int]:
        if header_mode == HeaderMode.NONE:
            return []

        if table_structure.header_row_indices:
            return sorted(set(table_structure.header_row_indices))

        explicit_header_rows = {
            cell.geometry.row_start
            for cell in cells
            if cell.geometry.is_header is True
        }
        if explicit_header_rows:
            return sorted(explicit_header_rows)

        if header_mode in (HeaderMode.INFER_FIRST_ROW, HeaderMode.AUTO):
            if row_count > 1:
                return [0]

        return []

    # --------------------------------------------------------------------------
    # Cell Finalization
    # --------------------------------------------------------------------------

    def _finalize_cells(
        self, cells: Sequence[_WorkingCell], header_row_indices: Sequence[int]
    ) -> List[TableCell]:
        header_rows = set(header_row_indices)
        finalized: List[TableCell] = []

        for cell in cells:
            text, confidence = cell.finalize_text()
            is_header = (
                cell.geometry.is_header
                if cell.geometry.is_header is not None
                else cell.geometry.row_start in header_rows
            )
            finalized.append(
                TableCell(
                    row_start=cell.geometry.row_start,
                    row_end=cell.geometry.row_end,
                    col_start=cell.geometry.col_start,
                    col_end=cell.geometry.col_end,
                    bbox=cell.geometry.bbox,
                    text=text,
                    confidence=confidence,
                    ocr_item_count=len(cell.matched_items),
                    is_header=bool(is_header),
                    is_merged=cell.geometry.is_merged,
                    is_synthetic=cell.is_synthetic,
                )
            )

        return finalized

    # --------------------------------------------------------------------------
    # Row / Column Building
    # --------------------------------------------------------------------------

    def _build_rows(
        self, grid: Dict[Tuple[int, int], TableCell], header_row_indices: Sequence[int]
    ) -> List[TableRow]:
        if not grid:
            return []

        row_count = max(pos[0] for pos in grid) + 1
        header_rows = set(header_row_indices)
        rows: List[TableRow] = []

        for r in range(row_count):
            seen_ids: set[int] = set()
            row_cells: List[TableCell] = []
            col_positions = [pos[1] for pos in grid if pos[0] == r]
            if not col_positions:
                continue
            col_count = max(col_positions) + 1
            for c in range(col_count):
                cell = grid.get((r, c))
                if cell is None:
                    continue
                if id(cell) in seen_ids:
                    continue
                seen_ids.add(id(cell))
                row_cells.append(cell)

            confidence = self._average_confidence(row_cells)
            rows.append(
                TableRow(
                    index=r,
                    cells=row_cells,
                    is_header=r in header_rows,
                    confidence=confidence,
                )
            )

        return rows

    def _merge_fragmented_rows(self, rows: List[TableRow]) -> List[TableRow]:
        """
        Merge adjacent, non-header rows that are fragments of one logical
        row: the table structure model occasionally inserts an extra row
        boundary between a row's label and its own values (e.g. a product
        name lands alone in one row while its Qtr1/Qtr2/Total values land
        in the row above or below). Two adjacent rows whose non-empty
        columns are completely disjoint are almost certainly such a split,
        so they are recombined into a single row.
        """
        if len(rows) < 2:
            return list(rows)

        merged: List[TableRow] = []
        i = 0
        while i < len(rows):
            current = rows[i]
            has_next = i + 1 < len(rows)

            if (
                has_next
                and not current.is_header
                and not rows[i + 1].is_header
                and self._are_disjoint_row_fragments(current, rows[i + 1])
            ):
                merged.append(self._merge_two_rows(current, rows[i + 1], len(merged)))
                i += 2
            else:
                merged.append(replace(current, index=len(merged)))
                i += 1

        if len(merged) != len(rows):
            logger.info(
                "Merged fragmented rows: %d row(s) collapsed into %d row(s).",
                len(rows), len(merged),
            )

        return merged

    @staticmethod
    def _are_disjoint_row_fragments(row_a: TableRow, row_b: TableRow) -> bool:
        filled_a = {c.col_start for c in row_a.cells if c.text.strip()}
        filled_b = {c.col_start for c in row_b.cells if c.text.strip()}
        if not filled_a or not filled_b:
            return False
        return filled_a.isdisjoint(filled_b)

    def _merge_two_rows(self, row_a: TableRow, row_b: TableRow, new_index: int) -> TableRow:
        cells_by_col: Dict[int, TableCell] = {}
        for cell in row_a.cells:
            cells_by_col[cell.col_start] = cell
        for cell in row_b.cells:
            existing = cells_by_col.get(cell.col_start)
            if existing is None or (not existing.text.strip() and cell.text.strip()):
                cells_by_col[cell.col_start] = cell

        merged_cells = [cells_by_col[col] for col in sorted(cells_by_col)]
        confidence = self._average_confidence(merged_cells)
        return TableRow(
            index=new_index,
            cells=merged_cells,
            is_header=row_a.is_header or row_b.is_header,
            confidence=confidence,
        )

    def _build_columns(
        self, grid: Dict[Tuple[int, int], TableCell]
    ) -> List[TableColumn]:
        if not grid:
            return []

        col_count = max(pos[1] for pos in grid) + 1
        row_count = max(pos[0] for pos in grid) + 1
        columns: List[TableColumn] = []

        for c in range(col_count):
            seen_ids: set[int] = set()
            col_cells: List[TableCell] = []
            for r in range(row_count):
                cell = grid.get((r, c))
                if cell is None:
                    continue
                if id(cell) in seen_ids:
                    continue
                seen_ids.add(id(cell))
                col_cells.append(cell)

            confidence = self._average_confidence(col_cells)
            columns.append(
                TableColumn(index=c, cells=col_cells, confidence=confidence)
            )

        return columns

    @staticmethod
    def _average_confidence(cells: Sequence[TableCell]) -> float:
        scored = [c.confidence for c in cells if c.ocr_item_count > 0]
        if not scored:
            return 0.0
        return max(0.0, min(1.0, sum(scored) / len(scored)))

    @staticmethod
    def _extract_header_texts(rows: Sequence[TableRow]) -> List[str]:
        header_rows = [row for row in rows if row.is_header]
        if not header_rows:
            return []
        first_header_row = header_rows[0]
        return [cell.text for cell in first_header_row.cells]

    # --------------------------------------------------------------------------
    # Confidence / Bounding Box Aggregation
    # --------------------------------------------------------------------------

    @staticmethod
    def _compute_table_confidence(rows: Sequence[TableRow]) -> float:
        scored_rows = [row.confidence for row in rows if row.confidence > 0]
        if not scored_rows:
            return 0.0
        return max(0.0, min(1.0, sum(scored_rows) / len(scored_rows)))

    @staticmethod
    def _compute_table_bbox(cells: Sequence[TableCell]) -> BoundingBox:
        real_cells = [c for c in cells if not c.is_synthetic and c.bbox.area > 0]
        source_cells = real_cells or list(cells)
        if not source_cells:
            return BoundingBox(0.0, 0.0, 0.0, 0.0)

        bbox = source_cells[0].bbox
        for cell in source_cells[1:]:
            bbox = bbox.union(cell.bbox)
        return bbox