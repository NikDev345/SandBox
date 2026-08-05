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
import re
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

# Minimum weighted score required to assign an OCR item to a cell during
# the primary matching pass.
MIN_MATCH_SCORE: float = 0.20

# Minimum score required during the second-chance recovery pass (see
# TableParser._second_chance_match). This pass only ever runs against
# cells that are still completely empty after the primary pass and
# after column rebalancing, so a much lower bar is acceptable here: the
# alternative to a low-confidence match is not "a better match elsewhere"
# but "silently losing the text entirely" (e.g. a missing SKU value).
SECOND_CHANCE_MIN_SCORE: float = 0.05

# Minimum OCR confidence to be considered for matching at all.
MIN_OCR_CONFIDENCE: float = 0.0

# Normalization divisor for the distance penalty term, expressed as a
# fraction of the cell's diagonal length. Larger values soften the penalty.
DISTANCE_PENALTY_DIAGONAL_FACTOR: float = 1.5

PARSER_VERSION: str = "2.2"

# A row whose only non-empty cell reads like "Table 1: ..." / "Table 2: ..."
# is a caption/title banner, not a header or data row. SLANet sometimes
# allocates it its own grid row (spanning all columns), which would
# otherwise get mistaken for the header row by naive "row 0 is the
# header" inference. This pattern is intentionally narrow (requires the
# literal "Table <number>:" prefix used by this document family) rather
# than a broad heuristic, to avoid accidentally stripping a legitimate
# data row that happens to be alone in its row.
_CAPTION_PATTERN = re.compile(r"^\s*Table\s+\d+\s*:", re.IGNORECASE)

# Matches a cell whose text is a run-on of a text label followed by a
# numeric/currency value with no separating cell boundary, e.g.
# "Qty in Stock 178" or "Unit Price $73.43" or "Total Value $13,070.54".
# This happens when SLANet's structure model never allocated a distinct
# header row, so the header label and the first data row's value for
# that column both land inside the same cell and get concatenated by
# the OCR-to-cell text join.
_LABEL_VALUE_PATTERN = re.compile(r"^([A-Za-z][A-Za-z\s]*?)\s+(\$?-?[\d,]+\.?\d*)$")


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
    second_chance_min_score: float = SECOND_CHANCE_MIN_SCORE
    min_ocr_confidence: float = MIN_OCR_CONFIDENCE
    distance_penalty_diagonal_factor: float = DISTANCE_PENALTY_DIAGONAL_FACTOR
    header_mode: HeaderMode = HeaderMode.AUTO
    strip_caption_rows: bool = True
    split_glued_header_rows: bool = True
    split_stacked_rows: bool = True
    rebalance_empty_neighbor_columns: bool = True
    second_chance_matching: bool = True
    drop_empty_rows: bool = True
    min_stacked_row_gap_factor: float = 0.5


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
    caption_rows_stripped: int = 0
    glued_header_rows_split: int = 0
    columns_rebalanced: int = 0
    second_chance_recovered: int = 0
    empty_rows_dropped: int = 0
    stacked_rows_split: int = 0
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
            print(
                "No eligible OCR items for page %d, table %d.", page_number, table_index
            )

        working_cells = self._create_working_cells(table_structure.cells)
        working_cells = self._sort_cells(working_cells)

        matched_count, unmatched_items = self._match_ocr_to_cells(
            eligible_ocr_items, working_cells
        )

        grid, row_count, col_count = self._build_grid(working_cells)

        # --------------------------------------------------------------
        # Strip caption/title banner rows (e.g. "Table 2: Department
        # Project Allocations (8 Rows)") BEFORE header inference runs.
        # If left in place, naive "row 0 is the header" logic would
        # mistake the caption for the real header row, permanently
        # burying the actual column names one row down.
        # --------------------------------------------------------------
        caption_rows_stripped = 0
        if self._config.strip_caption_rows:
            working_cells, row_count, caption_rows_stripped = self._strip_caption_rows(
                working_cells, row_count
            )
            if caption_rows_stripped:
                grid, row_count, col_count = self._build_grid(working_cells)

        # --------------------------------------------------------------
        # Rebalance text that landed entirely in one cell when it really
        # belongs split across that cell and a genuinely empty neighbor
        # (e.g. "Project ID Department" glued into column 0's header
        # while column 1's header cell sits empty; or "Sales" glued onto
        # "PROJ-2026-03" while the Department column for that row sits
        # empty). This happens when SLANet's column boundary for that
        # row/column pair is drawn slightly off from where the OCR text
        # actually sits, so OCR items that belong in the neighbor get
        # matched to the crowded cell instead purely on geometric
        # overlap. Uses the actual midpoint between the two cells' real
        # bounding boxes to decide what should move, so it only touches
        # cases with real, empty neighbor geometry to redistribute into.
        # --------------------------------------------------------------
        columns_rebalanced = 0
        if self._config.rebalance_empty_neighbor_columns:
            columns_rebalanced = self._rebalance_empty_neighbor_columns(
                grid, row_count, col_count
            )

        # --------------------------------------------------------------
        # Second-chance matching: some OCR items score just under the
        # primary matching threshold for every candidate cell (e.g. a
        # SKU value that OCR did detect, but whose bounding box didn't
        # align cleanly enough with any cell to clear MIN_MATCH_SCORE)
        # and are otherwise silently discarded, leaving a real cell
        # blank. This pass retries only the leftover, still-unmatched
        # OCR items against cells that are still completely empty after
        # the primary pass and rebalancing, using a much lower
        # threshold — safe here because the alternative to a
        # lower-confidence match is not "a better match exists
        # elsewhere" but "this data is lost entirely".
        # --------------------------------------------------------------
        second_chance_recovered = 0
        if self._config.second_chance_matching and unmatched_items:
            second_chance_recovered = self._second_chance_match(
                unmatched_items, grid, row_count, col_count
            )
            matched_count += second_chance_recovered

        unmatched_count = len(unmatched_items) - second_chance_recovered

        # --------------------------------------------------------------
        # Split a grid row whose cells each hold two vertically stacked
        # OCR items into two real rows. This happens whenever the table
        # structure model collapses two physically distinct rows (two
        # people, or a header row fused with the first data row) into a
        # single grid row, so every column's cell is tall enough to
        # contain both lines and the OCR matcher correctly (by geometry)
        # assigns both items to the one cell it was given.
        # --------------------------------------------------------------
        stacked_rows_split = 0
        if self._config.split_stacked_rows:
            working_cells, row_count, col_count, stacked_rows_split = (
                self._split_stacked_grid_rows(working_cells, row_count, col_count)
            )
            if stacked_rows_split:
                grid, row_count, col_count = self._build_grid(working_cells)

        working_cells = self._fill_missing_cells(grid, working_cells, row_count, col_count)

        header_row_indices = self._detect_headers(
            table_structure, working_cells, row_count, effective_header_mode
        )

        finalized_cells = self._finalize_cells(working_cells, header_row_indices)
        finalized_grid = self._rebuild_grid_from_finalized(finalized_cells, row_count, col_count)

        rows = self._build_rows(finalized_grid, header_row_indices)
        rows = self._merge_fragmented_rows(rows)

        # --------------------------------------------------------------
        # Drop rows SLANet allocated grid space for but that carry no
        # data at all — a blank gap row between two real data rows,
        # rather than a real (if sparse) row of the table.
        # --------------------------------------------------------------
        empty_rows_dropped = 0
        if self._config.drop_empty_rows:
            rows, empty_rows_dropped = self._drop_empty_rows(rows)

        # --------------------------------------------------------------
        # Recover a header row that got fused with the first data row's
        # values (e.g. "Qty in Stock 178" as one cell, because SLANet
        # never allocated a distinct header row at all). Splits the
        # glued text into a synthesized header row plus a proper first
        # data row wherever a "<label> <value>" pattern is detected.
        # --------------------------------------------------------------
        glued_header_rows_split = 0
        if self._config.split_glued_header_rows:
            rows, glued_header_rows_split = self._split_glued_header_row(rows)

        columns = self._build_columns_from_rows(rows)

        if not rows or not columns:
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
            header_row_count=sum(1 for r in rows if r.is_header),
            row_count=len(rows),
            col_count=col_count,
            caption_rows_stripped=caption_rows_stripped,
            glued_header_rows_split=glued_header_rows_split,
            columns_rebalanced=columns_rebalanced,
            second_chance_recovered=second_chance_recovered,
            empty_rows_dropped=empty_rows_dropped,
            stacked_rows_split=stacked_rows_split,
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
    ) -> Tuple[int, List[OCRItem]]:
        """
        Assign each OCR item to its single best-scoring cell.

        Returns (matched_count, unmatched_items) — the leftover items are
        returned (not just counted) so a later second-chance pass can
        retry them against cells that remain empty, rather than losing
        them the moment they miss the primary threshold.
        """
        matched_count = 0
        unmatched_items: List[OCRItem] = []

        for item in ocr_items:
            best_cell: Optional[_WorkingCell] = None
            best_score = 0.0

            for cell in cells:
                score = self._compute_match_score(item, cell.geometry)
                if score > best_score:
                    best_score = score
                    best_cell = cell

            if best_cell is not None and best_score >= self._config.min_match_score:

                logger.debug(
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
            else:
                unmatched_items.append(item)

        logger.debug(
            "OCR matching complete: %d matched, %d unmatched, %d cells.",
            matched_count, len(unmatched_items), len(cells),
        )
        return matched_count, unmatched_items

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

    def _second_chance_match(
        self,
        unmatched_items: Sequence[OCRItem],
        grid: Dict[Tuple[int, int], _WorkingCell],
        row_count: int,
        col_count: int,
    ) -> int:
        """
        Retry previously-unmatched OCR items against cells that are still
        completely empty, using a much lower score threshold than the
        primary pass. Only ever considers cells with real (non-synthetic,
        non-zero-area) geometry and zero matched items, so this can only
        fill in genuinely missing data — it can never overwrite or
        compete with a cell that already matched something in the
        primary pass.
        """
        if not unmatched_items:
            return 0

        empty_cells: List[_WorkingCell] = []
        seen_ids: set[int] = set()
        for r in range(row_count):
            for c in range(col_count):
                cell = grid.get((r, c))
                if cell is None or id(cell) in seen_ids:
                    continue
                seen_ids.add(id(cell))
                if not cell.matched_items and cell.geometry.bbox.area > 0:
                    empty_cells.append(cell)

        if not empty_cells:
            return 0

        recovered = 0
        for item in unmatched_items:
            best_cell: Optional[_WorkingCell] = None
            best_score = 0.0

            for cell in empty_cells:
                if cell.matched_items:
                    # Filled by an earlier item in this same pass.
                    continue
                score = self._compute_match_score(item, cell.geometry)
                if score > best_score:
                    best_score = score
                    best_cell = cell

            if best_cell is not None and best_score >= self._config.second_chance_min_score:
                best_cell.add(item)
                recovered += 1

        if recovered:
            print(
                "Second-chance matching recovered %d previously-unmatched OCR item(s).",
                recovered,
            )
        return recovered

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

    # --------------------------------------------------------------------------
    # Column Rebalancing
    # --------------------------------------------------------------------------

    def _rebalance_empty_neighbor_columns(
        self,
        grid: Dict[Tuple[int, int], _WorkingCell],
        row_count: int,
        col_count: int,
    ) -> int:
        """
        For each row, check every pair of horizontally adjacent cells. If
        the left cell has multiple matched OCR items and the right cell
        is real (non-synthetic) geometry with zero matched items, some of
        those items likely belong in the right cell instead — SLANet's
        column boundary for that particular row was drawn slightly off
        from where the text actually sits, so items that visually belong
        in the empty neighbor still scored higher against the crowded
        cell purely on overlap.

        Uses the midpoint between the two cells' real bounding boxes as
        the split line: any matched item in the left cell whose
        horizontal center falls past that midpoint moves to the right
        cell. Always leaves at least one item behind in the left cell,
        so this can only redistribute, never fully empty out a cell that
        had real content.
        """
        rebalanced = 0

        for r in range(row_count):
            for c in range(col_count - 1):
                left = grid.get((r, c))
                right = grid.get((r, c + 1))

                if left is None or right is None or left is right:
                    continue
                if right.matched_items:
                    continue
                if right.geometry.bbox.area <= 0 or left.geometry.bbox.area <= 0:
                    # No reliable real geometry on one side to split against.
                    continue
                if len(left.matched_items) < 2:
                    continue

                boundary_x = (left.geometry.bbox.x2 + right.geometry.bbox.x1) / 2.0
                movable = [
                    item for item in left.matched_items
                    if item.bbox.center[0] > boundary_x
                ]

                if not movable or len(movable) >= len(left.matched_items):
                    # Either nothing crosses the boundary, or everything
                    # does (which would just empty the left cell instead
                    # of genuinely splitting it) — skip either way.
                    continue

                for item in movable:
                    left.matched_items.remove(item)
                    right.add(item)

                rebalanced += 1

        return rebalanced

    # --------------------------------------------------------------------------
    # Stacked Row Splitting
    # --------------------------------------------------------------------------

    def _split_stacked_grid_rows(
        self,
        cells: List[_WorkingCell],
        row_count: int,
        col_count: int,
    ) -> Tuple[List[_WorkingCell], int, int, int]:
        """
        Detect and split a grid row whose cells each contain two
        vertically stacked OCR items into two real rows.

        This targets a specific, generalizable failure mode of the
        upstream table structure model: when it fails to allocate a
        row boundary between two physically distinct rows (e.g. two
        people, or a header row fused with the first data row), every
        column's cell in that grid row ends up tall enough to contain
        both lines of text. OCR-to-cell matching is purely geometric,
        so it correctly assigns both items to the one oversized cell it
        was given — the loss happens entirely upstream of matching, in
        the structure grid itself.

        A row qualifies for splitting when at least half of its
        non-empty, single-row-span cells contain 2+ matched OCR items
        whose vertical centers separate into exactly two bands with a
        gap at least ``min_stacked_row_gap_factor`` times the table's
        typical single-line cell height. This is intentionally strict:
        a normal multi-word cell (e.g. "Product Management") still
        produces closely-spaced items on one line, not two widely
        separated bands, so it is left untouched. Cells with only one
        item are assigned to whichever band their center sits closer
        to, so no data is dropped either way.

        Returns (possibly-unchanged cells, possibly-unchanged
        row_count, possibly-unchanged col_count, rows_split_count).
        """
        if row_count <= 0 or col_count <= 0 or not cells:
            return cells, row_count, col_count, 0

        single_item_heights = [
            c.geometry.bbox.height
            for c in cells
            if len(c.matched_items) == 1 and c.geometry.bbox.area > 0
        ]
        if not single_item_heights:
            return cells, row_count, col_count, 0
        single_item_heights.sort()
        typical_height = single_item_heights[len(single_item_heights) // 2]
        if typical_height <= 0:
            return cells, row_count, col_count, 0

        min_gap = typical_height * self._config.min_stacked_row_gap_factor

        grid: Dict[Tuple[int, int], _WorkingCell] = {}
        for cell in cells:
            for r in range(cell.geometry.row_start, cell.geometry.row_end + 1):
                for c in range(cell.geometry.col_start, cell.geometry.col_end + 1):
                    grid[(r, c)] = cell

        # row -> {col -> (top_items, bottom_items)} for cells that split.
        rows_to_split: Dict[int, Dict[int, Tuple[List[OCRItem], List[OCRItem]]]] = {}

        for r in range(row_count):
            row_cells: Dict[int, _WorkingCell] = {}
            seen_ids: set = set()
            skip_row = False
            for c in range(col_count):
                cell = grid.get((r, c))
                if cell is None or id(cell) in seen_ids:
                    continue
                seen_ids.add(id(cell))
                if cell.geometry.row_start != cell.geometry.row_end:
                    # Already a genuine multi-row span; don't touch this row.
                    skip_row = True
                    break
                row_cells[c] = cell
            if skip_row or not row_cells:
                continue

            splits: Dict[int, Tuple[List[OCRItem], List[OCRItem]]] = {}
            for c, cell in row_cells.items():
                items = sorted(cell.matched_items, key=lambda i: i.bbox.center[1])
                if len(items) < 2:
                    continue
                best_gap, best_idx = -1.0, 0
                for i in range(1, len(items)):
                    gap = items[i].bbox.center[1] - items[i - 1].bbox.center[1]
                    if gap > best_gap:
                        best_gap, best_idx = gap, i
                if best_gap < min_gap:
                    continue
                top, bottom = items[:best_idx], items[best_idx:]
                if top and bottom:
                    splits[c] = (top, bottom)

            non_empty_cells = [c for c, cell in row_cells.items() if cell.matched_items]
            if not non_empty_cells:
                continue
            if len(splits) >= max(1, len(non_empty_cells) // 2):
                rows_to_split[r] = splits

        if not rows_to_split:
            return cells, row_count, col_count, 0

        new_cells: List[_WorkingCell] = []
        next_row = 0

        for r in range(row_count):
            seen_ids: set = set()
            col_positions = sorted(c for c in range(col_count) if (r, c) in grid)
            if not col_positions:
                continue

            if r not in rows_to_split:
                for c in col_positions:
                    cell = grid[(r, c)]
                    if id(cell) in seen_ids:
                        continue
                    seen_ids.add(id(cell))
                    row_span = cell.geometry.row_end - cell.geometry.row_start
                    new_geom = replace(
                        cell.geometry,
                        row_start=next_row,
                        row_end=next_row + row_span,
                    )
                    new_cells.append(
                        _WorkingCell(
                            geometry=new_geom,
                            matched_items=list(cell.matched_items),
                            is_synthetic=cell.is_synthetic,
                        )
                    )
                next_row += 1
                continue

            splits = rows_to_split[r]
            band_centers = [
                (
                    sum(i.bbox.center[1] for i in top) / len(top),
                    sum(i.bbox.center[1] for i in bottom) / len(bottom),
                )
                for top, bottom in splits.values()
            ]
            avg_top = sum(t for t, _ in band_centers) / len(band_centers)
            avg_bottom = sum(b for _, b in band_centers) / len(band_centers)

            for c in col_positions:
                cell = grid[(r, c)]
                if id(cell) in seen_ids:
                    continue
                seen_ids.add(id(cell))

                top_geom = replace(cell.geometry, row_start=next_row, row_end=next_row)
                # The bottom band is always the second physical row, never
                # the header, regardless of what the (now-split) original
                # cell was explicitly flagged as.
                bottom_geom = replace(
                    cell.geometry,
                    row_start=next_row + 1,
                    row_end=next_row + 1,
                    is_header=False if cell.geometry.is_header else cell.geometry.is_header,
                )

                if c in splits:
                    top_items, bottom_items = splits[c]
                    new_cells.append(_WorkingCell(geometry=top_geom, matched_items=list(top_items)))
                    new_cells.append(_WorkingCell(geometry=bottom_geom, matched_items=list(bottom_items)))
                    continue

                items = cell.matched_items
                if not items:
                    new_cells.append(_WorkingCell(geometry=top_geom, is_synthetic=cell.is_synthetic))
                    new_cells.append(_WorkingCell(geometry=bottom_geom, is_synthetic=cell.is_synthetic))
                    continue

                item_y = sum(i.bbox.center[1] for i in items) / len(items)
                if abs(item_y - avg_top) <= abs(item_y - avg_bottom):
                    new_cells.append(_WorkingCell(geometry=top_geom, matched_items=list(items)))
                    new_cells.append(_WorkingCell(geometry=bottom_geom))
                else:
                    new_cells.append(_WorkingCell(geometry=top_geom))
                    new_cells.append(_WorkingCell(geometry=bottom_geom, matched_items=list(items)))

            next_row += 2

        new_row_count = next_row
        return new_cells, new_row_count, col_count, len(rows_to_split)

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
    # Caption Row Stripping
    # --------------------------------------------------------------------------

    def _strip_caption_rows(
        self,
        cells: List[_WorkingCell],
        row_count: int,
    ) -> Tuple[List[_WorkingCell], int, int]:
        """
        Detect and remove caption/title banner rows (e.g. "Table 2:
        Department Project Allocations (8 Rows)") from the working cell
        set, renumbering all remaining row indices so downstream header
        inference sees the real header as row 0.

        A row qualifies as a caption row when it has exactly one
        non-row-spanning cell with non-empty text, and that text matches
        the "Table <number>:" prefix pattern. This is intentionally
        narrow: it only strips rows that are unambiguously title banners
        for this document family, never a legitimately sparse data row.

        Returns (possibly-unchanged cells, possibly-unchanged row_count,
        number of caption rows stripped).
        """
        if row_count <= 1:
            return cells, row_count, 0

        # Only consider single-row cells (row_start == row_end) when
        # deciding whether a row is a caption row; multi-row-spanning
        # cells crossing a caption row would be unusual and are left
        # alone rather than guessed at.
        texts_by_row: Dict[int, List[str]] = {}
        for cell in cells:
            if cell.geometry.row_start != cell.geometry.row_end:
                continue
            text, _ = cell.finalize_text()
            texts_by_row.setdefault(cell.geometry.row_start, []).append(text.strip())

        caption_rows = {
            r
            for r, texts in texts_by_row.items()
            if len([t for t in texts if t]) == 1
            and _CAPTION_PATTERN.match(next(t for t in texts if t))
        }

        if not caption_rows:
            return cells, row_count, 0

        kept_rows = sorted(r for r in range(row_count) if r not in caption_rows)
        remap = {old: new for new, old in enumerate(kept_rows)}

        new_cells: List[_WorkingCell] = []
        for cell in cells:
            rs, re_ = cell.geometry.row_start, cell.geometry.row_end
            # Drop any cell that starts or ends inside a stripped caption
            # row (this includes the caption cell itself).
            if rs in caption_rows or re_ in caption_rows:
                continue
            if rs not in remap or re_ not in remap:
                # Should not normally happen, but skip defensively rather
                # than raise on an unexpected multi-row span.
                continue
            new_geometry = replace(cell.geometry, row_start=remap[rs], row_end=remap[re_])
            new_cells.append(
                _WorkingCell(
                    geometry=new_geometry,
                    matched_items=list(cell.matched_items),
                    is_synthetic=cell.is_synthetic,
                )
            )

        new_row_count = len(kept_rows)
        return new_cells, new_row_count, len(caption_rows)

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
            print(
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
        if filled_a.isdisjoint(filled_b):
            return True

        # Narrow second case: a value that wraps onto its own visual line
        # (e.g. "North America" or "Cloud Subscriptions") can end up as an
        # entire extra grid row containing only that wrapped word, sharing
        # just the one or two columns it wrapped in with its real row —
        # while every other column in that extra row is empty. This is a
        # continuation of those columns, not a competing value for them,
        # so it's still safe to merge (with text concatenated, see
        # _merge_two_rows) even though the filled columns overlap.
        #
        # Deliberately strict to avoid merging two genuinely separate data
        # rows that happen to share one filled column (e.g. two rows both
        # showing "Active" status): one side must be sparse (at most 2
        # filled columns, and no more than half of the other row's filled
        # columns), and every column it shares with the other row must be
        # a true overlap rather than most of the row's own content.
        smaller, larger = (
            (filled_a, filled_b) if len(filled_a) <= len(filled_b) else (filled_b, filled_a)
        )
        if len(smaller) > 2 or len(smaller) > len(larger) // 2:
            return False
        shared = smaller & larger
        return len(shared) == len(smaller) and len(shared) < len(larger)

    def _merge_two_rows(self, row_a: TableRow, row_b: TableRow, new_index: int) -> TableRow:
        cells_by_col: Dict[int, TableCell] = {}
        for cell in row_a.cells:
            cells_by_col[cell.col_start] = cell
        for cell in row_b.cells:
            existing = cells_by_col.get(cell.col_start)
            if existing is None or not existing.text.strip():
                cells_by_col[cell.col_start] = cell
            elif cell.text.strip() and cell.text.strip() != existing.text.strip():
                # Both cells have real, different text for the same
                # column — most likely a wrapped value split across two
                # grid rows (e.g. "North" + "America"). Concatenate
                # rather than silently discarding one side's data.
                order = [existing, cell] if row_a.index <= row_b.index else [cell, existing]
                cells_by_col[cell.col_start] = replace(
                    existing, text=" ".join(c.text.strip() for c in order)
                )

        merged_cells = [cells_by_col[col] for col in sorted(cells_by_col)]
        confidence = self._average_confidence(merged_cells)
        return TableRow(
            index=new_index,
            cells=merged_cells,
            is_header=row_a.is_header or row_b.is_header,
            confidence=confidence,
        )

    def _drop_empty_rows(self, rows: List[TableRow]) -> Tuple[List[TableRow], int]:
        """
        Remove non-header rows where every cell's text is empty. SLANet
        occasionally allocates a full blank row of grid space between
        two real data rows (visible as a stray gap in the rendered
        table) rather than the structure model simply under-counting
        rows. Header rows are never dropped, even if empty, since an
        empty header is still meaningful structurally (see
        _split_glued_header_row, which can legitimately produce blank
        header cells for columns with no recoverable label).
        """
        kept: List[TableRow] = []
        dropped = 0

        for row in rows:
            if not row.is_header and not any(c.text.strip() for c in row.cells):
                dropped += 1
                continue
            kept.append(row)

        if dropped:
            kept = [replace(row, index=i) for i, row in enumerate(kept)]

        return kept, dropped

    # --------------------------------------------------------------------------
    # Glued Header/Data Row Splitting
    # --------------------------------------------------------------------------

    def _split_glued_header_row(
        self, rows: List[TableRow]
    ) -> Tuple[List[TableRow], int]:
        """
        Detect and repair a header row whose cells are actually a fusion
        of the true column label and the first data row's value for that
        column (e.g. "Qty in Stock 178", "Unit Price $73.43"). This
        happens when the table structure model never allocated a
        distinct header row at all — the row tagged as the header is
        really the first data row, and only *some* of its cells happen
        to carry a leftover label fragment glued to the front.

        For each cell in the row currently marked as header:
          - if its text matches "<label> <numeric/currency value>",
            split it: the label becomes the new header cell's text, and
            the value becomes the new first data row's cell text.
          - otherwise, we have no genuine label for that column at all
            (it was never captured by OCR), so the header cell is left
            blank rather than guessing, and the original text is kept
            as-is in the new data row — this preserves real data (e.g.
            a SKU value) instead of misclassifying it as a header label.

        Only triggers when at least half of the header row's non-empty
        cells match the glued label/value pattern, to avoid ever
        rewriting a row that is genuinely just a header with no glued
        data (which should be left untouched).
        """
        if not rows:
            return rows, 0

        header_rows = [r for r in rows if r.is_header]
        if not header_rows:
            return rows, 0

        target = header_rows[0]
        non_empty_cells = [c for c in target.cells if c.text.strip()]
        if not non_empty_cells:
            return rows, 0

        matched_cells = [
            c for c in non_empty_cells if _LABEL_VALUE_PATTERN.match(c.text.strip())
        ]
        if len(matched_cells) < max(1, len(non_empty_cells) // 2):
            # Not a glued row — likely a genuine, clean header. Leave as is.
            return rows, 0

        label_cells: List[TableCell] = []
        value_cells: List[TableCell] = []

        for cell in target.cells:
            stripped = cell.text.strip()
            match = _LABEL_VALUE_PATTERN.match(stripped) if stripped else None
            if match:
                label_text, value_text = match.group(1).strip(), match.group(2).strip()
                label_cells.append(replace(cell, text=label_text, is_header=True))
                value_cells.append(replace(cell, text=value_text, is_header=False))
            else:
                # No recoverable label for this column — don't invent one.
                # Keep the original text as real data instead of losing it
                # or mislabeling it as a header.
                label_cells.append(replace(cell, text="", is_header=True))
                value_cells.append(replace(cell, text=cell.text, is_header=False))

        new_header_row = TableRow(
            index=0, cells=label_cells, is_header=True, confidence=target.confidence
        )
        new_data_row = TableRow(
            index=1, cells=value_cells, is_header=False, confidence=target.confidence
        )

        result: List[TableRow] = [new_header_row, new_data_row]
        next_index = 2
        for row in rows:
            if row is target:
                continue
            result.append(replace(row, index=next_index))
            next_index += 1

        return result, 1

    def _build_columns_from_rows(self, rows: Sequence[TableRow]) -> List[TableColumn]:
        """
        Build columns from the final row list rather than the pre-split
        cell grid, so that any text changes made by row-level
        post-processing (rebalancing, second-chance matching, glued
        header splitting) are reflected consistently in both rows and
        columns.
        """
        col_map: Dict[int, List[TableCell]] = {}
        for row in rows:
            for cell in row.cells:
                col_map.setdefault(cell.col_start, []).append(cell)

        columns: List[TableColumn] = []
        for col_idx in sorted(col_map):
            cells = col_map[col_idx]
            confidence = self._average_confidence(cells)
            columns.append(TableColumn(index=col_idx, cells=cells, confidence=confidence))

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