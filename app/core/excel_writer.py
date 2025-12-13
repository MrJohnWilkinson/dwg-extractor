"""
Excel file generation for the DXF Block Extractor.

This module provides functionality to convert comprehensive CAD analysis data into
multi-sheet Excel workbooks with proper sorting, auto-filtering, and column widths.

Usage:
    from core.excel_writer import write_excel
    from core.extractor import ExtractionResult

    result: ExtractionResult = extract_blocks('/path/to/drawing.dxf')
    excel_path = write_excel(result, '/path/to/drawing.dxf')
    # Returns: '/path/to/drawing_blocks_20250117_143022.xlsx'
"""

from datetime import datetime
from pathlib import Path

import pandas as pd
from openpyxl import load_workbook

from .constants import (
    EXCEL_COLUMN_ANNOTATION_COLOR_B,
    EXCEL_COLUMN_ANNOTATION_COLOR_G,
    EXCEL_COLUMN_ANNOTATION_COLOR_R,
    EXCEL_COLUMN_ANNOTATION_COLOR_SAMPLE,
    EXCEL_COLUMN_ANNOTATION_CONTENTS,
    EXCEL_COLUMN_ANNOTATION_COUNT,
    EXCEL_COLUMN_ANNOTATION_LAYER_NAME,
    EXCEL_COLUMN_ANNOTATION_TYPE,
    EXCEL_COLUMN_BLOCK_CONTENT_ZONE_DETECTED,
    EXCEL_COLUMN_BLOCK_CONTENT_ZONE_HEIGHT,
    EXCEL_COLUMN_BLOCK_CONTENT_ZONE_WIDTH,
    EXCEL_COLUMN_BLOCK_ENTITY_COUNT,
    EXCEL_COLUMN_BLOCK_FILTERED_POLYGON_COUNT,
    EXCEL_COLUMN_BLOCK_HORIZONTAL_SEGMENTS,
    EXCEL_COLUMN_BLOCK_INSERTION_COUNT,
    EXCEL_COLUMN_BLOCK_INSERTION_STATUS,
    EXCEL_COLUMN_BLOCK_IS_NESTED,
    EXCEL_COLUMN_BLOCK_LAYER_COUNT,
    EXCEL_COLUMN_BLOCK_LAYER_NAME,
    EXCEL_COLUMN_BLOCK_LAYER_NAMES,
    EXCEL_COLUMN_BLOCK_NAME,
    EXCEL_COLUMN_BLOCK_NATIVE_HEIGHT,
    EXCEL_COLUMN_BLOCK_NATIVE_WIDTH,
    EXCEL_COLUMN_BLOCK_NESTED_PARENT_NAMES,
    EXCEL_COLUMN_BLOCK_POLYGON_COUNT,
    EXCEL_COLUMN_BLOCK_RAW_NAME,
    EXCEL_COLUMN_BLOCK_RESOLVED_NAME,
    EXCEL_COLUMN_BLOCK_ROTATION_0,
    EXCEL_COLUMN_BLOCK_ROTATION_90,
    EXCEL_COLUMN_BLOCK_ROTATION_180,
    EXCEL_COLUMN_BLOCK_ROTATION_270,
    EXCEL_COLUMN_BLOCK_ROTATION_OTHER,
    EXCEL_COLUMN_BLOCK_SCALE_X,
    EXCEL_COLUMN_BLOCK_SCALE_Y,
    EXCEL_COLUMN_BLOCK_SUGGESTED_TRIM_BOTTOM,
    EXCEL_COLUMN_BLOCK_SUGGESTED_TRIM_LEFT,
    EXCEL_COLUMN_BLOCK_SUGGESTED_TRIM_RIGHT,
    EXCEL_COLUMN_BLOCK_SUGGESTED_TRIM_TOP,
    EXCEL_COLUMN_BLOCK_VERTICAL_SEGMENTS,
    EXCEL_COLUMN_BLOCK_XDATA_APPS,
    EXCEL_COLUMN_COLOR_ANNOTATION_CONTENTS,
    EXCEL_COLUMN_COLOR_AUTOCAD_NAME,
    EXCEL_COLUMN_COLOR_BLUE,
    EXCEL_COLUMN_COLOR_ENTITY_COUNT,
    EXCEL_COLUMN_COLOR_ENTITY_TYPE,
    EXCEL_COLUMN_COLOR_GREEN,
    EXCEL_COLUMN_COLOR_LAYER_NAME,
    EXCEL_COLUMN_COLOR_RED,
    EXCEL_COLUMN_COLOR_SAMPLE,
    EXCEL_COLUMN_ENTITY_TYPE_COUNT,
    EXCEL_COLUMN_ENTITY_TYPE_NAME,
    EXCEL_COLUMN_ISSUE_BLOCK_NAME,
    EXCEL_COLUMN_ISSUE_DETAILS,
    EXCEL_COLUMN_ISSUE_INSERTION_COUNT,
    EXCEL_COLUMN_ISSUE_LAYER_NAME,
    EXCEL_COLUMN_ISSUE_TYPE,
    EXCEL_COLUMN_LAYER_ANNOTATION_COUNT,
    EXCEL_COLUMN_LAYER_BLOCK_INSERTION_COUNT,
    EXCEL_COLUMN_LAYER_ENTITY_COUNT,
    EXCEL_COLUMN_LAYER_NAME,
    EXCEL_COLUMN_LAYER_UNIQUE_COLOR_COUNT,
    EXCEL_SHEET_ALL_BLOCKS,
    EXCEL_SHEET_ANNOTATIONS_ANALYSIS,
    EXCEL_SHEET_BLOCK_ANALYSIS,
    EXCEL_SHEET_BLOCK_DEFINITIONS,
    EXCEL_SHEET_BLOCK_GEOMETRY_ANALYSIS,
    EXCEL_SHEET_COLOR_ANALYSIS,
    EXCEL_SHEET_ENTITY_SUMMARY,
    EXCEL_SHEET_EXTRACTION_ISSUES,
    EXCEL_SHEET_LAYER_ANALYSIS,
)
from .excel_formatting import (
    _format_all_blocks_sheet,
    _format_annotations_analysis_sheet,
    _format_block_analysis_sheet,
    _format_block_definitions_sheet,
    _format_block_geometry_analysis_sheet,
    _format_color_analysis_sheet,
    _format_entity_summary_sheet,
    _format_extraction_issues_sheet,
    _format_layer_analysis_sheet,
    format_header,
)
from .extractor import ExtractionResult
from .logger import setup_logger
from .types import BlockRotationKey


logger = setup_logger(__name__)


# Maximum display length for segment strings in Excel cells
SEGMENT_MAX_DISPLAY_LENGTH = 200


def _truncate_segment_string(
    segment_str: str, max_length: int = SEGMENT_MAX_DISPLAY_LENGTH
) -> str:
    """
    Truncate a segment string to a maximum length for Excel display.

    When segment lists are very long, they can cause Excel cells to become
    unwieldy. This function truncates the string and adds an ellipsis to
    indicate truncation occurred.

    Args:
        segment_str: The comma-separated segment string to truncate
        max_length: Maximum allowed length (default: SEGMENT_MAX_DISPLAY_LENGTH)

    Returns:
        Original string if within max_length, otherwise truncated with "..."

    Examples:
        >>> _truncate_segment_string("10, 20, 30", 200)
        '10, 20, 30'
        >>> _truncate_segment_string("a" * 250, 200)
        'aaaa...aaa...'  # 197 chars + "..."
    """
    if len(segment_str) <= max_length:
        return segment_str
    return segment_str[: max_length - 3] + "..."


# ACI (AutoCAD Color Index) named colors (1-7)
_ACI_NAMED_COLORS: dict[int, str] = {
    1: "Red",
    2: "Yellow",
    3: "Green",
    4: "Cyan",
    5: "Blue",
    6: "Magenta",
    7: "White",
}


def _get_aci_display_name(aci: int | None) -> str:
    """
    Map an ACI (AutoCAD Color Index) value to a human-readable display name.

    AutoCAD uses a standardized 256-color palette (ACI) where:
    - ACI 0: "ByBlock" - inherits color from parent block
    - ACI 1-7: Named primary colors (Red, Yellow, Green, Cyan, Blue, Magenta, White)
    - ACI 8-255: Numbered colors ("Color N" format)
    - ACI 256: "ByLayer" - inherits color from layer
    - ACI None: "True Color" - 24-bit RGB color that bypasses the ACI palette

    Args:
        aci: AutoCAD Color Index value (0-256) or None for True Color

    Returns:
        Human-readable display name for the color

    Examples:
        >>> _get_aci_display_name(None)
        'True Color'
        >>> _get_aci_display_name(0)
        'ByBlock'
        >>> _get_aci_display_name(1)
        'Red'
        >>> _get_aci_display_name(7)
        'White'
        >>> _get_aci_display_name(30)
        'Color 30'
        >>> _get_aci_display_name(256)
        'ByLayer'
    """
    # True Color (24-bit RGB, no ACI index)
    if aci is None:
        return "True Color"

    # ByBlock
    if aci == 0:
        return "ByBlock"

    # Named primary colors (1-7)
    if aci in _ACI_NAMED_COLORS:
        return _ACI_NAMED_COLORS[aci]

    # ByLayer
    if aci == 256:
        return "ByLayer"

    # Numbered colors (8-255)
    if 8 <= aci <= 255:
        return f"Color {aci}"

    # Fallback for invalid values (should not happen)
    return f"Unknown ({aci})"


def _has_x_scale_variance(scale_set: set[tuple[float, float]]) -> bool:
    """
    Check if a block has varying X scale values across its insertions.

    Args:
        scale_set: Set of unique (x_scale, y_scale) tuples for a block

    Returns:
        True if more than one unique X scale value exists, False otherwise

    Examples:
        >>> _has_x_scale_variance({(1.0, 1.0), (2.0, 1.0)})
        True
        >>> _has_x_scale_variance({(1.0, 1.0), (1.0, 2.0)})
        False
        >>> _has_x_scale_variance({(1.5, 1.5)})
        False
    """
    x_scales = {x for x, _ in scale_set}
    return len(x_scales) > 1


def _has_y_scale_variance(scale_set: set[tuple[float, float]]) -> bool:
    """
    Check if a block has varying Y scale values across its insertions.

    Args:
        scale_set: Set of unique (x_scale, y_scale) tuples for a block

    Returns:
        True if more than one unique Y scale value exists, False otherwise

    Examples:
        >>> _has_y_scale_variance({(1.0, 1.0), (1.0, 2.0)})
        True
        >>> _has_y_scale_variance({(1.0, 1.0), (2.0, 1.0)})
        False
        >>> _has_y_scale_variance({(1.5, 1.5)})
        False
    """
    y_scales = {y for _, y in scale_set}
    return len(y_scales) > 1


def _get_single_scale_value(scale_set: set[tuple[float, float]], axis: str) -> float:
    """
    Extract the single scale value for a given axis when no variance exists.

    Args:
        scale_set: Set of unique (x_scale, y_scale) tuples for a block
        axis: Either 'x' or 'y' to specify which axis to extract

    Returns:
        The single scale value for the specified axis

    Raises:
        ValueError: If axis is not 'x' or 'y', or if scale_set is empty

    Examples:
        >>> _get_single_scale_value({(1.5, 2.0), (1.5, 3.0)}, 'x')
        1.5
        >>> _get_single_scale_value({(1.0, 2.5), (2.0, 2.5)}, 'y')
        2.5
    """
    if not scale_set:
        raise ValueError("scale_set cannot be empty")

    if axis == "x":
        x_scales = {x for x, _ in scale_set}
        return next(iter(x_scales))
    elif axis == "y":
        y_scales = {y for _, y in scale_set}
        return next(iter(y_scales))
    else:
        raise ValueError(f"axis must be 'x' or 'y', got '{axis}'")


def _has_negative_scale_in_set(scale_set: set[tuple[float, float]], axis: str) -> bool:
    """
    Check if a block has any negative scale values for the specified axis.

    Args:
        scale_set: Set of unique (x_scale, y_scale) tuples for a block
        axis: Either 'x' or 'y' to specify which axis to check

    Returns:
        True if any negative scale value exists for the specified axis, False otherwise

    Raises:
        ValueError: If axis is not 'x' or 'y', or if scale_set is empty

    Examples:
        >>> _has_negative_scale_in_set({(1.0, 1.0), (-1.0, 1.0)}, 'x')
        True
        >>> _has_negative_scale_in_set({(1.0, 1.0), (2.0, 1.0)}, 'x')
        False
        >>> _has_negative_scale_in_set({(1.0, -1.0), (1.0, -2.0)}, 'y')
        True
    """
    if not scale_set:
        raise ValueError("scale_set cannot be empty")

    if axis == "x":
        x_scales = {x for x, _ in scale_set}
        return any(x < 0 for x in x_scales)
    elif axis == "y":
        y_scales = {y for _, y in scale_set}
        return any(y < 0 for y in y_scales)
    else:
        raise ValueError(f"axis must be 'x' or 'y', got '{axis}'")


def write_excel(
    extraction_data: ExtractionResult,
    input_file_path: str,
    output_path: str | Path | None = None,
) -> str:
    """
    Generate a multi-sheet Excel file from comprehensive CAD extraction data.

    This function creates an Excel workbook with nine sheets:
    1. All Blocks: Consolidated block-centric view with one row per block definition
    2. Block Analysis: Simplified inventory with block-layer pairs and insertion counts
    3. Layer Analysis: Layers with insertion counts and entity counts
    4. Entity Summary: Entity types with total counts
    5. Block Geometry Analysis: Consolidated transformations and geometry (rotations, scales, dimensions, segments)
    6. Annotations Analysis: Text annotations (TEXT/MTEXT) with contents, type, layer, color, and counts
    7. Color Analysis: Entity color breakdown by layer and type
    8. Extraction Issues: Unresolved anonymous blocks and other extraction issues
    9. Block Definitions: All block definitions with nesting status

    All sheets include headers, appropriate sorting, auto-filters, and proper column widths.
    The Block Geometry Analysis sheet includes red highlighting for mirrored blocks (negative scales).
    When output_path is not provided, the output filename is timestamped to prevent overwrites.

    Args:
        extraction_data: ExtractionResult TypedDict containing all CAD analysis data
        input_file_path: Path to the original DXF file (used for default output filename)
        output_path: Optional explicit output path. If provided, uses this exact path.
                    If None, generates timestamped filename in same directory as input.

    Returns:
        Full path to the created Excel file as a string

    Raises:
        ValueError: If extraction_data is None or invalid

    Examples:
        >>> result = extract_blocks('drawing.dxf')
        >>> excel_file = write_excel(result, 'drawing.dxf')
        >>> print(excel_file)
        '/path/to/drawing_blocks_20250117_143022.xlsx'

        >>> # With explicit output path
        >>> excel_file = write_excel(result, 'drawing.dxf', '/output/custom_name.xlsx')
    """
    logger.info("Starting multi-sheet Excel file generation")

    # Validate input
    if extraction_data is None:
        logger.error("extraction_data cannot be None")
        raise ValueError("extraction_data cannot be None")

    try:
        # Determine output path
        if output_path is not None:
            full_path = Path(output_path)
        else:
            # Generate timestamped filename (legacy behavior)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            input_path = Path(input_file_path)
            filename = f"{input_path.stem}_blocks_{timestamp}.xlsx"
            full_path = input_path.parent / filename

        # Create Excel writer
        with pd.ExcelWriter(full_path, engine="openpyxl") as writer:
            # Sheet 1: All Blocks (consolidated block-centric view)
            _create_all_blocks_sheet(extraction_data, writer)

            # Sheet 2: Block Analysis
            _create_block_analysis_sheet(extraction_data, writer)

            # Sheet 3: Layer Analysis
            _create_layer_analysis_sheet(extraction_data, writer)

            # Sheet 4: Entity Summary
            _create_entity_summary_sheet(extraction_data, writer)

            # Sheet 5: Block Geometry Analysis
            _create_block_geometry_analysis_sheet(extraction_data, writer)

            # Sheet 6: Annotations Analysis
            _create_annotations_analysis_sheet(extraction_data, writer)

            # Sheet 7: Color Analysis
            _create_color_analysis_sheet(extraction_data, writer)

            # Sheet 8: Extraction Issues
            _create_extraction_issues_sheet(extraction_data, writer)

            # Sheet 9: Block Definitions
            _create_block_definitions_sheet(extraction_data, writer)

        # Load workbook for post-processing (formatting)
        logger.debug("Loading workbook for formatting stage...")
        wb = load_workbook(full_path)

        # Apply formatting to all sheets
        logger.debug("Applying formatting to All Blocks sheet...")
        _format_all_blocks_sheet(wb)
        logger.debug("Applying formatting to Block Analysis sheet...")
        _format_block_analysis_sheet(wb)
        logger.debug("Applying formatting to Layer Analysis sheet...")
        _format_layer_analysis_sheet(wb)
        logger.debug("Applying formatting to Entity Summary sheet...")
        _format_entity_summary_sheet(wb)
        logger.debug("Applying formatting to Block Geometry Analysis sheet...")
        _format_block_geometry_analysis_sheet(wb)
        logger.debug("Applying formatting to Annotations Analysis sheet...")
        _format_annotations_analysis_sheet(wb)
        logger.debug("Applying formatting to Color Analysis sheet...")
        _format_color_analysis_sheet(wb)
        logger.debug("Applying formatting to Extraction Issues sheet...")
        _format_extraction_issues_sheet(wb)
        logger.debug("Applying formatting to Block Definitions sheet...")
        _format_block_definitions_sheet(wb)

        # Save workbook with formatting
        logger.debug("Saving workbook with formatting applied...")
        wb.save(full_path)

        logger.info(f"Multi-sheet Excel file created successfully at {full_path}")
        return str(full_path)

    except ValueError as e:
        logger.error(f"Invalid input data: {str(e)}")
        raise
    except Exception as e:
        logger.error(
            f"Unexpected error during Excel generation: {str(e)}", exc_info=True
        )
        raise


def _create_block_analysis_sheet(
    data: ExtractionResult, writer: pd.ExcelWriter
) -> None:
    """Create the Block Analysis sheet with simplified inventory data (no rotations)."""
    logger.info("Creating Block Analysis sheet...")

    block_layer_pairs = data["block_layer_pairs"]
    block_entities = data["block_entities"]
    block_xdata_apps = data["block_xdata_apps"]

    logger.debug(
        f"Block Analysis: {len(block_layer_pairs)} block-layer pairs to process"
    )

    if block_layer_pairs:
        # Unpack block-layer pairs into DataFrame rows (simplified - no rotations)
        rows = []
        for key, insertion_count in block_layer_pairs.items():
            entity_count = block_entities.get(key.block_name, 0)

            # Get XDATA apps for this block-layer pair
            xdata_apps = block_xdata_apps.get(key, set())
            xdata_apps_str = ", ".join(sorted(xdata_apps)) if xdata_apps else "-"

            logger.debug(
                f"Processing block-layer pair: {key.block_name}/{key.layer_name}, count={insertion_count}"
            )

            rows.append(
                {
                    EXCEL_COLUMN_BLOCK_NAME: key.block_name,
                    EXCEL_COLUMN_BLOCK_INSERTION_COUNT: insertion_count,
                    EXCEL_COLUMN_BLOCK_ENTITY_COUNT: entity_count,
                    EXCEL_COLUMN_BLOCK_LAYER_NAME: key.layer_name,
                    EXCEL_COLUMN_BLOCK_XDATA_APPS: xdata_apps_str,
                }
            )

        df = pd.DataFrame(rows)
        df.sort_values(
            by=EXCEL_COLUMN_BLOCK_INSERTION_COUNT, ascending=False, inplace=True
        )
    else:
        # Create empty DataFrame with headers only (5 columns)
        df = pd.DataFrame(
            columns=[
                EXCEL_COLUMN_BLOCK_NAME,
                EXCEL_COLUMN_BLOCK_INSERTION_COUNT,
                EXCEL_COLUMN_BLOCK_ENTITY_COUNT,
                EXCEL_COLUMN_BLOCK_LAYER_NAME,
                EXCEL_COLUMN_BLOCK_XDATA_APPS,
            ]
        )

    # Format column headers for Excel display
    df.columns = [format_header(col) for col in df.columns]

    df.to_excel(writer, sheet_name=EXCEL_SHEET_BLOCK_ANALYSIS, index=False)
    logger.info(f"Block Analysis sheet created with {len(df)} rows")


def _create_layer_analysis_sheet(
    data: ExtractionResult, writer: pd.ExcelWriter
) -> None:
    """Create the Layer Analysis sheet with layer-based metrics."""
    logger.info("Creating Layer Analysis sheet...")

    layer_block_insertion_counts = data["layer_block_insertion_counts"]
    layer_entity_counts = data["layer_entity_counts"]
    layer_unique_color_counts = data["layer_unique_color_counts"]
    layer_annotation_counts = data["layer_annotation_counts"]

    logger.debug(f"Layer Analysis: {len(layer_entity_counts)} layers to process")

    if layer_entity_counts:
        # Merge layer data into single DataFrame
        rows = []
        for layer_name, entity_count in layer_entity_counts.items():
            insertion_count = layer_block_insertion_counts.get(layer_name, 0)
            color_count = layer_unique_color_counts.get(layer_name, 0)
            annotation_count = layer_annotation_counts.get(layer_name, 0)
            rows.append(
                {
                    EXCEL_COLUMN_LAYER_NAME: layer_name,
                    EXCEL_COLUMN_LAYER_BLOCK_INSERTION_COUNT: insertion_count,
                    EXCEL_COLUMN_LAYER_ENTITY_COUNT: entity_count,
                    EXCEL_COLUMN_LAYER_UNIQUE_COLOR_COUNT: color_count,
                    EXCEL_COLUMN_LAYER_ANNOTATION_COUNT: annotation_count,
                }
            )

        df = pd.DataFrame(rows)
        df.sort_values(
            by=EXCEL_COLUMN_LAYER_ENTITY_COUNT, ascending=False, inplace=True
        )
    else:
        # Create empty DataFrame with headers only
        df = pd.DataFrame(
            columns=[
                EXCEL_COLUMN_LAYER_NAME,
                EXCEL_COLUMN_LAYER_BLOCK_INSERTION_COUNT,
                EXCEL_COLUMN_LAYER_ENTITY_COUNT,
                EXCEL_COLUMN_LAYER_UNIQUE_COLOR_COUNT,
                EXCEL_COLUMN_LAYER_ANNOTATION_COUNT,
            ]
        )

    # Format column headers for Excel display
    df.columns = [format_header(col) for col in df.columns]

    df.to_excel(writer, sheet_name=EXCEL_SHEET_LAYER_ANALYSIS, index=False)
    logger.info(f"Layer Analysis sheet created with {len(df)} rows")


def _create_entity_summary_sheet(
    data: ExtractionResult, writer: pd.ExcelWriter
) -> None:
    """Create the Entity Summary sheet with global entity type counts."""
    logger.info("Creating Entity Summary sheet...")

    entity_type_counts = data["entity_type_counts"]

    logger.debug(f"Entity Summary: {len(entity_type_counts)} entity types to process")

    if entity_type_counts:
        # Convert entity types to DataFrame
        df = pd.DataFrame(
            list(entity_type_counts.items()),
            columns=[EXCEL_COLUMN_ENTITY_TYPE_NAME, EXCEL_COLUMN_ENTITY_TYPE_COUNT],
        )
        df.sort_values(by=EXCEL_COLUMN_ENTITY_TYPE_COUNT, ascending=False, inplace=True)
    else:
        # Create empty DataFrame with headers only
        df = pd.DataFrame(
            columns=[EXCEL_COLUMN_ENTITY_TYPE_NAME, EXCEL_COLUMN_ENTITY_TYPE_COUNT]
        )

    # Format column headers for Excel display
    df.columns = [format_header(col) for col in df.columns]

    df.to_excel(writer, sheet_name=EXCEL_SHEET_ENTITY_SUMMARY, index=False)
    logger.info(f"Entity Summary sheet created with {len(df)} rows")


def _create_block_geometry_analysis_sheet(
    data: ExtractionResult, writer: pd.ExcelWriter
) -> None:
    """Create the Block Geometry Analysis sheet with consolidated transformations and geometry data."""
    logger.info("Creating Block Geometry Analysis sheet...")

    block_layer_pairs = data["block_layer_pairs"]
    block_trimming_data = data["block_trimming_data"]
    block_rotation_counts = data["block_rotation_counts"]
    block_scale_data = data["block_scale_data"]
    block_content_zone_data = data.get("block_content_zone_data", {})

    logger.debug(
        f"Block Geometry Analysis: {len(block_layer_pairs)} pairs, {len(block_trimming_data)} geometry records"
    )

    if block_layer_pairs:
        # Build DataFrame rows from block-layer pairs with all geometry data
        rows = []
        for key, _insertion_count in block_layer_pairs.items():
            # Look up geometry data for this block
            geometry_data = block_trimming_data.get(key.block_name)

            # Skip blocks without geometry data (anonymous blocks, etc.)
            if geometry_data is None:
                continue

            # Extract rotation counts for this block-layer pair
            rot_0 = block_rotation_counts.get(
                BlockRotationKey(
                    block_name=key.block_name,
                    layer_name=key.layer_name,
                    rotation_category="0",
                ),
                0,
            )
            rot_90 = block_rotation_counts.get(
                BlockRotationKey(
                    block_name=key.block_name,
                    layer_name=key.layer_name,
                    rotation_category="90",
                ),
                0,
            )
            rot_180 = block_rotation_counts.get(
                BlockRotationKey(
                    block_name=key.block_name,
                    layer_name=key.layer_name,
                    rotation_category="180",
                ),
                0,
            )
            rot_270 = block_rotation_counts.get(
                BlockRotationKey(
                    block_name=key.block_name,
                    layer_name=key.layer_name,
                    rotation_category="270",
                ),
                0,
            )
            rot_other = block_rotation_counts.get(
                BlockRotationKey(
                    block_name=key.block_name,
                    layer_name=key.layer_name,
                    rotation_category="other",
                ),
                0,
            )

            # Extract scale data for this block (all insertions across all layers)
            # Determine if X or Y scales vary, display "VARIES" or "VARIES (-)" or numeric value
            scale_set = block_scale_data.get(key.block_name, {(1.0, 1.0)})

            x_variance = _has_x_scale_variance(scale_set)
            y_variance = _has_y_scale_variance(scale_set)
            logger.debug(
                f"Scale variance for {key.block_name}: x_variance={x_variance}, y_variance={y_variance}"
            )

            if x_variance:
                if _has_negative_scale_in_set(scale_set, "x"):
                    x_scale: str | float = "VARIES (-)"
                else:
                    x_scale = "VARIES"
            else:
                x_scale = _get_single_scale_value(scale_set, "x")

            if y_variance:
                if _has_negative_scale_in_set(scale_set, "y"):
                    y_scale: str | float = "VARIES (-)"
                else:
                    y_scale = "VARIES"
            else:
                y_scale = _get_single_scale_value(scale_set, "y")

            # Extract dimension data
            native_width = geometry_data["native_width"]
            native_height = geometry_data["native_height"]
            vertical_segments = geometry_data["vertical_segments"]
            horizontal_segments = geometry_data["horizontal_segments"]

            # Convert segment lists to comma-separated strings (no decimals for whole numbers)
            def format_number(n: float) -> str:
                """Format number without decimals if it's a whole number."""
                return str(int(n)) if n == int(n) else str(n)

            vertical_segments_str = (
                ", ".join(map(format_number, vertical_segments))
                if vertical_segments
                else ""
            )
            vertical_segments_str = _truncate_segment_string(vertical_segments_str)

            horizontal_segments_str = (
                ", ".join(map(format_number, horizontal_segments))
                if horizontal_segments
                else ""
            )
            horizontal_segments_str = _truncate_segment_string(horizontal_segments_str)

            # Get content zone data for this block
            content_zone = block_content_zone_data.get(key.block_name)
            if content_zone and content_zone["content_zone_detected"]:
                trim_left: float | str = content_zone["suggested_trim_left"] or ""
                trim_right: float | str = content_zone["suggested_trim_right"] or ""
                trim_top: float | str = content_zone["suggested_trim_top"] or ""
                trim_bottom: float | str = content_zone["suggested_trim_bottom"] or ""
                detected = "TRUE"
                cz_width: float | str = content_zone["content_zone_width"] or ""
                cz_height: float | str = content_zone["content_zone_height"] or ""
                poly_count: int | str = content_zone["polygon_count"]
                filtered_poly_count: int | str = content_zone["filtered_polygon_count"]
            else:
                trim_left = ""
                trim_right = ""
                trim_top = ""
                trim_bottom = ""
                detected = "FALSE" if content_zone else ""
                cz_width = ""
                cz_height = ""
                poly_count = content_zone["polygon_count"] if content_zone else ""
                filtered_poly_count = (
                    content_zone["filtered_polygon_count"] if content_zone else ""
                )

            rows.append(
                {
                    EXCEL_COLUMN_BLOCK_NAME: key.block_name,
                    EXCEL_COLUMN_BLOCK_LAYER_NAME: key.layer_name,
                    EXCEL_COLUMN_BLOCK_ROTATION_0: rot_0,
                    EXCEL_COLUMN_BLOCK_ROTATION_90: rot_90,
                    EXCEL_COLUMN_BLOCK_ROTATION_180: rot_180,
                    EXCEL_COLUMN_BLOCK_ROTATION_270: rot_270,
                    EXCEL_COLUMN_BLOCK_ROTATION_OTHER: rot_other,
                    EXCEL_COLUMN_BLOCK_SCALE_X: x_scale,
                    EXCEL_COLUMN_BLOCK_SCALE_Y: y_scale,
                    EXCEL_COLUMN_BLOCK_NATIVE_WIDTH: native_width,
                    EXCEL_COLUMN_BLOCK_NATIVE_HEIGHT: native_height,
                    EXCEL_COLUMN_BLOCK_VERTICAL_SEGMENTS: vertical_segments_str,
                    EXCEL_COLUMN_BLOCK_HORIZONTAL_SEGMENTS: horizontal_segments_str,
                    EXCEL_COLUMN_BLOCK_SUGGESTED_TRIM_LEFT: trim_left,
                    EXCEL_COLUMN_BLOCK_SUGGESTED_TRIM_RIGHT: trim_right,
                    EXCEL_COLUMN_BLOCK_SUGGESTED_TRIM_TOP: trim_top,
                    EXCEL_COLUMN_BLOCK_SUGGESTED_TRIM_BOTTOM: trim_bottom,
                    EXCEL_COLUMN_BLOCK_CONTENT_ZONE_DETECTED: detected,
                    EXCEL_COLUMN_BLOCK_CONTENT_ZONE_WIDTH: cz_width,
                    EXCEL_COLUMN_BLOCK_CONTENT_ZONE_HEIGHT: cz_height,
                    EXCEL_COLUMN_BLOCK_POLYGON_COUNT: poly_count,
                    EXCEL_COLUMN_BLOCK_FILTERED_POLYGON_COUNT: filtered_poly_count,
                }
            )

        df = pd.DataFrame(rows)
        # Sort by block_name alphabetically
        df.sort_values(by=EXCEL_COLUMN_BLOCK_NAME, ascending=True, inplace=True)
    else:
        # Create empty DataFrame with headers only (all 21 columns)
        df = pd.DataFrame(
            columns=[
                EXCEL_COLUMN_BLOCK_NAME,
                EXCEL_COLUMN_BLOCK_LAYER_NAME,
                EXCEL_COLUMN_BLOCK_ROTATION_0,
                EXCEL_COLUMN_BLOCK_ROTATION_90,
                EXCEL_COLUMN_BLOCK_ROTATION_180,
                EXCEL_COLUMN_BLOCK_ROTATION_270,
                EXCEL_COLUMN_BLOCK_ROTATION_OTHER,
                EXCEL_COLUMN_BLOCK_SCALE_X,
                EXCEL_COLUMN_BLOCK_SCALE_Y,
                EXCEL_COLUMN_BLOCK_NATIVE_WIDTH,
                EXCEL_COLUMN_BLOCK_NATIVE_HEIGHT,
                EXCEL_COLUMN_BLOCK_VERTICAL_SEGMENTS,
                EXCEL_COLUMN_BLOCK_HORIZONTAL_SEGMENTS,
                EXCEL_COLUMN_BLOCK_SUGGESTED_TRIM_LEFT,
                EXCEL_COLUMN_BLOCK_SUGGESTED_TRIM_RIGHT,
                EXCEL_COLUMN_BLOCK_SUGGESTED_TRIM_TOP,
                EXCEL_COLUMN_BLOCK_SUGGESTED_TRIM_BOTTOM,
                EXCEL_COLUMN_BLOCK_CONTENT_ZONE_DETECTED,
                EXCEL_COLUMN_BLOCK_CONTENT_ZONE_WIDTH,
                EXCEL_COLUMN_BLOCK_CONTENT_ZONE_HEIGHT,
                EXCEL_COLUMN_BLOCK_POLYGON_COUNT,
                EXCEL_COLUMN_BLOCK_FILTERED_POLYGON_COUNT,
            ]
        )

    # Format column headers for Excel display
    df.columns = [format_header(col) for col in df.columns]

    df.to_excel(writer, sheet_name=EXCEL_SHEET_BLOCK_GEOMETRY_ANALYSIS, index=False)
    logger.info(f"Block Geometry Analysis sheet created with {len(df)} rows")


def _create_annotations_analysis_sheet(
    data: ExtractionResult, writer: pd.ExcelWriter
) -> None:
    """Create the Annotations Analysis sheet with text annotation details."""
    logger.info("Creating Annotations Analysis sheet...")

    annotation_data = data["annotation_data"]

    logger.debug(
        f"Annotations Analysis: {len(annotation_data)} annotation groups to process"
    )

    if annotation_data:
        # Build DataFrame rows from annotation data
        rows = []
        for key, count in annotation_data.items():
            rows.append(
                {
                    EXCEL_COLUMN_ANNOTATION_CONTENTS: key.annotation_contents,
                    EXCEL_COLUMN_ANNOTATION_TYPE: key.annotation_type,
                    EXCEL_COLUMN_ANNOTATION_LAYER_NAME: key.layer_name,
                    EXCEL_COLUMN_ANNOTATION_COLOR_R: key.color_r,
                    EXCEL_COLUMN_ANNOTATION_COLOR_G: key.color_g,
                    EXCEL_COLUMN_ANNOTATION_COLOR_B: key.color_b,
                    EXCEL_COLUMN_ANNOTATION_COLOR_SAMPLE: "",  # Placeholder for color fill
                    EXCEL_COLUMN_ANNOTATION_COUNT: count,
                }
            )

        df = pd.DataFrame(rows)
        # Sort by count descending
        df.sort_values(by=EXCEL_COLUMN_ANNOTATION_COUNT, ascending=False, inplace=True)
    else:
        # Create empty DataFrame with headers only
        df = pd.DataFrame(
            columns=[
                EXCEL_COLUMN_ANNOTATION_CONTENTS,
                EXCEL_COLUMN_ANNOTATION_TYPE,
                EXCEL_COLUMN_ANNOTATION_LAYER_NAME,
                EXCEL_COLUMN_ANNOTATION_COLOR_R,
                EXCEL_COLUMN_ANNOTATION_COLOR_G,
                EXCEL_COLUMN_ANNOTATION_COLOR_B,
                EXCEL_COLUMN_ANNOTATION_COLOR_SAMPLE,
                EXCEL_COLUMN_ANNOTATION_COUNT,
            ]
        )

    # Format column headers for Excel display
    df.columns = [format_header(col) for col in df.columns]

    df.to_excel(writer, sheet_name=EXCEL_SHEET_ANNOTATIONS_ANALYSIS, index=False)
    logger.info(f"Annotations Analysis sheet created with {len(df)} rows")


def _create_color_analysis_sheet(
    data: ExtractionResult, writer: pd.ExcelWriter
) -> None:
    """Create the Color Analysis sheet with entity color analysis data."""
    logger.info("Creating Color Analysis sheet...")

    color_analysis_data = data["color_analysis_data"]

    logger.debug(f"Color Analysis: {len(color_analysis_data)} records to process")

    if color_analysis_data:
        # Build DataFrame directly from color analysis data
        rows = []
        for record in color_analysis_data:
            # Map ACI value to human-readable display name
            aci_display_name = _get_aci_display_name(record["color_aci"])

            rows.append(
                {
                    EXCEL_COLUMN_COLOR_ANNOTATION_CONTENTS: record[
                        "annotation_contents"
                    ],
                    EXCEL_COLUMN_COLOR_LAYER_NAME: record["layer_name"],
                    EXCEL_COLUMN_COLOR_RED: record["color_r"],
                    EXCEL_COLUMN_COLOR_GREEN: record["color_g"],
                    EXCEL_COLUMN_COLOR_BLUE: record["color_b"],
                    EXCEL_COLUMN_COLOR_SAMPLE: "",  # Placeholder for color fill
                    EXCEL_COLUMN_COLOR_AUTOCAD_NAME: aci_display_name,
                    EXCEL_COLUMN_COLOR_ENTITY_TYPE: record["entity_type"],
                    EXCEL_COLUMN_COLOR_ENTITY_COUNT: record["entity_count"],
                }
            )

        df = pd.DataFrame(rows)
        # Data is already sorted from extract_color_analysis()
    else:
        # Create empty DataFrame with headers only (9 columns now)
        df = pd.DataFrame(
            columns=[
                EXCEL_COLUMN_COLOR_ANNOTATION_CONTENTS,
                EXCEL_COLUMN_COLOR_LAYER_NAME,
                EXCEL_COLUMN_COLOR_RED,
                EXCEL_COLUMN_COLOR_GREEN,
                EXCEL_COLUMN_COLOR_BLUE,
                EXCEL_COLUMN_COLOR_SAMPLE,
                EXCEL_COLUMN_COLOR_AUTOCAD_NAME,
                EXCEL_COLUMN_COLOR_ENTITY_TYPE,
                EXCEL_COLUMN_COLOR_ENTITY_COUNT,
            ]
        )

    # Format column headers for Excel display
    df.columns = [format_header(col) for col in df.columns]

    df.to_excel(writer, sheet_name=EXCEL_SHEET_COLOR_ANALYSIS, index=False)
    logger.info(f"Color Analysis sheet created with {len(df)} rows")


def _create_extraction_issues_sheet(
    data: ExtractionResult, writer: pd.ExcelWriter
) -> None:
    """Create the Extraction Issues sheet with unresolved anonymous blocks."""
    logger.info("Creating Extraction Issues sheet...")

    extraction_issues = data["extraction_issues"]

    logger.debug(f"Extraction Issues: {len(extraction_issues)} issues to process")

    if extraction_issues:
        # Build DataFrame rows from extraction issues
        rows = []
        for issue in extraction_issues:
            rows.append(
                {
                    EXCEL_COLUMN_ISSUE_TYPE: issue["issue_type"],
                    EXCEL_COLUMN_ISSUE_BLOCK_NAME: issue["block_name"],
                    EXCEL_COLUMN_ISSUE_LAYER_NAME: issue["layer_name"],
                    EXCEL_COLUMN_ISSUE_INSERTION_COUNT: issue["insertion_count"],
                    EXCEL_COLUMN_ISSUE_DETAILS: issue["details"],
                }
            )

        df = pd.DataFrame(rows)
        # Data is already sorted by insertion count descending from extractor
    else:
        # Create empty DataFrame with headers only
        df = pd.DataFrame(
            columns=[
                EXCEL_COLUMN_ISSUE_TYPE,
                EXCEL_COLUMN_ISSUE_BLOCK_NAME,
                EXCEL_COLUMN_ISSUE_LAYER_NAME,
                EXCEL_COLUMN_ISSUE_INSERTION_COUNT,
                EXCEL_COLUMN_ISSUE_DETAILS,
            ]
        )

    # Format column headers for Excel display
    df.columns = [format_header(col) for col in df.columns]

    df.to_excel(writer, sheet_name=EXCEL_SHEET_EXTRACTION_ISSUES, index=False)
    logger.info(f"Extraction Issues sheet created with {len(df)} rows")


def _create_block_definitions_sheet(
    data: ExtractionResult, writer: pd.ExcelWriter
) -> None:
    """Create the Block Definitions sheet with all block definitions and nesting status."""
    logger.info("Creating Block Definitions sheet...")

    all_block_definitions = data.get("all_block_definitions", {})

    if not all_block_definitions:
        logger.info("No block definitions found, skipping Block Definitions sheet")
        return

    # Build DataFrame rows
    rows = []
    for raw_name, record in all_block_definitions.items():
        parent_names_str = ", ".join(record["block_nested_parent_names"])

        rows.append(
            {
                EXCEL_COLUMN_BLOCK_RAW_NAME: record["block_raw_name"],
                EXCEL_COLUMN_BLOCK_RESOLVED_NAME: record["block_resolved_name"],
                EXCEL_COLUMN_BLOCK_INSERTION_STATUS: record["block_insertion_status"],
                EXCEL_COLUMN_BLOCK_IS_NESTED: record["block_is_nested"],
                EXCEL_COLUMN_BLOCK_NESTED_PARENT_NAMES: parent_names_str,
                EXCEL_COLUMN_BLOCK_ENTITY_COUNT: record["block_entity_count"],
            }
        )

    # Sort by insertion status (Inserted first, System last), then by resolved name
    status_order = {
        "Inserted": 0,
        "Nested Only": 1,
        "Unused": 2,
        "Unresolved (*U)": 3,
        "Unresolved (A$C)": 4,
        "System": 5,
        "System (Dimension)": 6,
        "System (Hatch)": 7,
    }
    rows.sort(
        key=lambda r: (
            status_order.get(str(r[EXCEL_COLUMN_BLOCK_INSERTION_STATUS]), 99),
            str(r[EXCEL_COLUMN_BLOCK_RESOLVED_NAME]).lower(),
        )
    )

    df = pd.DataFrame(rows)

    # Format column headers for Excel display
    df.columns = [format_header(col) for col in df.columns]

    df.to_excel(writer, sheet_name=EXCEL_SHEET_BLOCK_DEFINITIONS, index=False)
    logger.info(f"Block Definitions sheet created with {len(df)} rows")


def _create_all_blocks_sheet(data: ExtractionResult, writer: pd.ExcelWriter) -> None:
    """
    Create the All Blocks sheet with consolidated block data across all layers.

    This sheet provides a block-centric view with one row per block definition,
    aggregating data from multiple sources: block_counts, block_layer_pairs,
    block_rotation_counts, block_scale_data, block_trimming_data, and
    block_content_zone_data.

    System blocks (insertion_status starting with "System") are excluded.
    Rows are sorted by insertion_status (Inserted first), then by resolved_name.

    The sheet contains 29 columns covering:
    - Identity fields: raw_name, resolved_name, insertion_status, is_nested, etc.
    - Layer aggregation: layer_count, layer_names
    - Insertion count: aggregated from block_counts
    - Rotation counts: summed across all layers
    - Scale data: variance detection with "VARIES"/"VARIES (-)" display
    - Geometry data: native dimensions and segments
    - Content zone data: trim values and detection status

    Args:
        data: ExtractionResult containing all extraction data
        writer: pandas ExcelWriter object for output
    """
    logger.info("Creating All Blocks sheet...")

    all_block_definitions = data.get("all_block_definitions", {})
    block_counts = data.get("block_counts", {})
    block_layer_pairs = data.get("block_layer_pairs", {})
    block_rotation_counts = data.get("block_rotation_counts", {})
    block_scale_data = data.get("block_scale_data", {})
    block_trimming_data = data.get("block_trimming_data", {})
    block_content_zone_data = data.get("block_content_zone_data", {})

    if not all_block_definitions:
        logger.info("No block definitions found, creating empty All Blocks sheet")
        # Create empty DataFrame with all 29 column headers
        df = pd.DataFrame(
            columns=[
                EXCEL_COLUMN_BLOCK_RAW_NAME,
                EXCEL_COLUMN_BLOCK_RESOLVED_NAME,
                EXCEL_COLUMN_BLOCK_SUGGESTED_TRIM_LEFT,
                EXCEL_COLUMN_BLOCK_SUGGESTED_TRIM_RIGHT,
                EXCEL_COLUMN_BLOCK_SUGGESTED_TRIM_TOP,
                EXCEL_COLUMN_BLOCK_SUGGESTED_TRIM_BOTTOM,
                EXCEL_COLUMN_BLOCK_VERTICAL_SEGMENTS,
                EXCEL_COLUMN_BLOCK_HORIZONTAL_SEGMENTS,
                EXCEL_COLUMN_BLOCK_NATIVE_WIDTH,
                EXCEL_COLUMN_BLOCK_NATIVE_HEIGHT,
                EXCEL_COLUMN_BLOCK_CONTENT_ZONE_DETECTED,
                EXCEL_COLUMN_BLOCK_CONTENT_ZONE_WIDTH,
                EXCEL_COLUMN_BLOCK_CONTENT_ZONE_HEIGHT,
                EXCEL_COLUMN_BLOCK_POLYGON_COUNT,
                EXCEL_COLUMN_BLOCK_FILTERED_POLYGON_COUNT,
                EXCEL_COLUMN_BLOCK_INSERTION_STATUS,
                EXCEL_COLUMN_BLOCK_IS_NESTED,
                EXCEL_COLUMN_BLOCK_NESTED_PARENT_NAMES,
                EXCEL_COLUMN_BLOCK_ENTITY_COUNT,
                EXCEL_COLUMN_BLOCK_INSERTION_COUNT,
                EXCEL_COLUMN_BLOCK_LAYER_COUNT,
                EXCEL_COLUMN_BLOCK_LAYER_NAMES,
                EXCEL_COLUMN_BLOCK_ROTATION_0,
                EXCEL_COLUMN_BLOCK_ROTATION_90,
                EXCEL_COLUMN_BLOCK_ROTATION_180,
                EXCEL_COLUMN_BLOCK_ROTATION_270,
                EXCEL_COLUMN_BLOCK_ROTATION_OTHER,
                EXCEL_COLUMN_BLOCK_SCALE_X,
                EXCEL_COLUMN_BLOCK_SCALE_Y,
            ]
        )
        df.columns = [format_header(col) for col in df.columns]
        df.to_excel(writer, sheet_name=EXCEL_SHEET_ALL_BLOCKS, index=False)
        return

    # Build DataFrame rows
    rows = []
    for raw_name, record in all_block_definitions.items():
        # Skip System blocks
        insertion_status = record["block_insertion_status"]
        if insertion_status.startswith("System"):
            continue

        resolved_name = record["block_resolved_name"]
        parent_names_str = ", ".join(record["block_nested_parent_names"])

        # Calculate block insertion count
        block_insertion_count = block_counts.get(resolved_name, 0)

        # Calculate layer aggregation
        layers_for_block = {
            key.layer_name
            for key in block_layer_pairs
            if key.block_name == resolved_name
        }
        block_layer_count = len(layers_for_block)
        block_layer_names = ", ".join(sorted(layers_for_block))

        # Calculate rotation counts summed across all layers
        rot_0 = sum(
            count
            for key, count in block_rotation_counts.items()
            if key.block_name == resolved_name and key.rotation_category == "0"
        )
        rot_90 = sum(
            count
            for key, count in block_rotation_counts.items()
            if key.block_name == resolved_name and key.rotation_category == "90"
        )
        rot_180 = sum(
            count
            for key, count in block_rotation_counts.items()
            if key.block_name == resolved_name and key.rotation_category == "180"
        )
        rot_270 = sum(
            count
            for key, count in block_rotation_counts.items()
            if key.block_name == resolved_name and key.rotation_category == "270"
        )
        rot_other = sum(
            count
            for key, count in block_rotation_counts.items()
            if key.block_name == resolved_name and key.rotation_category == "other"
        )

        # Extract scale data
        scale_set = block_scale_data.get(resolved_name, {(1.0, 1.0)})
        x_variance = _has_x_scale_variance(scale_set)
        y_variance = _has_y_scale_variance(scale_set)

        if x_variance:
            if _has_negative_scale_in_set(scale_set, "x"):
                x_scale: str | float = "VARIES (-)"
            else:
                x_scale = "VARIES"
        else:
            x_scale = _get_single_scale_value(scale_set, "x")

        if y_variance:
            if _has_negative_scale_in_set(scale_set, "y"):
                y_scale: str | float = "VARIES (-)"
            else:
                y_scale = "VARIES"
        else:
            y_scale = _get_single_scale_value(scale_set, "y")

        # Extract geometry data
        geometry_data = block_trimming_data.get(resolved_name)
        if geometry_data:
            native_width: float | str = geometry_data["native_width"]
            native_height: float | str = geometry_data["native_height"]
            vertical_segments = geometry_data["vertical_segments"]
            horizontal_segments = geometry_data["horizontal_segments"]

            # Convert segment lists to comma-separated strings
            def format_number(n: float) -> str:
                """Format number without decimals if it's a whole number."""
                return str(int(n)) if n == int(n) else str(n)

            vertical_segments_str = (
                ", ".join(map(format_number, vertical_segments))
                if vertical_segments
                else ""
            )
            vertical_segments_str = _truncate_segment_string(vertical_segments_str)

            horizontal_segments_str = (
                ", ".join(map(format_number, horizontal_segments))
                if horizontal_segments
                else ""
            )
            horizontal_segments_str = _truncate_segment_string(horizontal_segments_str)
        else:
            native_width = ""
            native_height = ""
            vertical_segments_str = ""
            horizontal_segments_str = ""

        # Extract content zone data
        content_zone = block_content_zone_data.get(resolved_name)
        if content_zone and content_zone["content_zone_detected"]:
            trim_left: float | str = content_zone["suggested_trim_left"] or ""
            trim_right: float | str = content_zone["suggested_trim_right"] or ""
            trim_top: float | str = content_zone["suggested_trim_top"] or ""
            trim_bottom: float | str = content_zone["suggested_trim_bottom"] or ""
            detected = "TRUE"
            cz_width: float | str = content_zone["content_zone_width"] or ""
            cz_height: float | str = content_zone["content_zone_height"] or ""
            poly_count: int | str = content_zone["polygon_count"]
            filtered_poly_count: int | str = content_zone["filtered_polygon_count"]
        else:
            trim_left = ""
            trim_right = ""
            trim_top = ""
            trim_bottom = ""
            detected = "FALSE" if content_zone else ""
            cz_width = ""
            cz_height = ""
            poly_count = content_zone["polygon_count"] if content_zone else ""
            filtered_poly_count = (
                content_zone["filtered_polygon_count"] if content_zone else ""
            )

        rows.append(
            {
                EXCEL_COLUMN_BLOCK_RAW_NAME: record["block_raw_name"],
                EXCEL_COLUMN_BLOCK_RESOLVED_NAME: resolved_name,
                EXCEL_COLUMN_BLOCK_SUGGESTED_TRIM_LEFT: trim_left,
                EXCEL_COLUMN_BLOCK_SUGGESTED_TRIM_RIGHT: trim_right,
                EXCEL_COLUMN_BLOCK_SUGGESTED_TRIM_TOP: trim_top,
                EXCEL_COLUMN_BLOCK_SUGGESTED_TRIM_BOTTOM: trim_bottom,
                EXCEL_COLUMN_BLOCK_VERTICAL_SEGMENTS: vertical_segments_str,
                EXCEL_COLUMN_BLOCK_HORIZONTAL_SEGMENTS: horizontal_segments_str,
                EXCEL_COLUMN_BLOCK_NATIVE_WIDTH: native_width,
                EXCEL_COLUMN_BLOCK_NATIVE_HEIGHT: native_height,
                EXCEL_COLUMN_BLOCK_CONTENT_ZONE_DETECTED: detected,
                EXCEL_COLUMN_BLOCK_CONTENT_ZONE_WIDTH: cz_width,
                EXCEL_COLUMN_BLOCK_CONTENT_ZONE_HEIGHT: cz_height,
                EXCEL_COLUMN_BLOCK_POLYGON_COUNT: poly_count,
                EXCEL_COLUMN_BLOCK_FILTERED_POLYGON_COUNT: filtered_poly_count,
                EXCEL_COLUMN_BLOCK_INSERTION_STATUS: insertion_status,
                EXCEL_COLUMN_BLOCK_IS_NESTED: record["block_is_nested"],
                EXCEL_COLUMN_BLOCK_NESTED_PARENT_NAMES: parent_names_str,
                EXCEL_COLUMN_BLOCK_ENTITY_COUNT: record["block_entity_count"],
                EXCEL_COLUMN_BLOCK_INSERTION_COUNT: block_insertion_count,
                EXCEL_COLUMN_BLOCK_LAYER_COUNT: block_layer_count,
                EXCEL_COLUMN_BLOCK_LAYER_NAMES: block_layer_names,
                EXCEL_COLUMN_BLOCK_ROTATION_0: rot_0,
                EXCEL_COLUMN_BLOCK_ROTATION_90: rot_90,
                EXCEL_COLUMN_BLOCK_ROTATION_180: rot_180,
                EXCEL_COLUMN_BLOCK_ROTATION_270: rot_270,
                EXCEL_COLUMN_BLOCK_ROTATION_OTHER: rot_other,
                EXCEL_COLUMN_BLOCK_SCALE_X: x_scale,
                EXCEL_COLUMN_BLOCK_SCALE_Y: y_scale,
            }
        )

    # Handle case where all blocks were system blocks (rows is empty)
    if not rows:
        logger.info("All blocks are system blocks, creating empty All Blocks sheet")
        df = pd.DataFrame(
            columns=[
                EXCEL_COLUMN_BLOCK_RAW_NAME,
                EXCEL_COLUMN_BLOCK_RESOLVED_NAME,
                EXCEL_COLUMN_BLOCK_SUGGESTED_TRIM_LEFT,
                EXCEL_COLUMN_BLOCK_SUGGESTED_TRIM_RIGHT,
                EXCEL_COLUMN_BLOCK_SUGGESTED_TRIM_TOP,
                EXCEL_COLUMN_BLOCK_SUGGESTED_TRIM_BOTTOM,
                EXCEL_COLUMN_BLOCK_VERTICAL_SEGMENTS,
                EXCEL_COLUMN_BLOCK_HORIZONTAL_SEGMENTS,
                EXCEL_COLUMN_BLOCK_NATIVE_WIDTH,
                EXCEL_COLUMN_BLOCK_NATIVE_HEIGHT,
                EXCEL_COLUMN_BLOCK_CONTENT_ZONE_DETECTED,
                EXCEL_COLUMN_BLOCK_CONTENT_ZONE_WIDTH,
                EXCEL_COLUMN_BLOCK_CONTENT_ZONE_HEIGHT,
                EXCEL_COLUMN_BLOCK_POLYGON_COUNT,
                EXCEL_COLUMN_BLOCK_FILTERED_POLYGON_COUNT,
                EXCEL_COLUMN_BLOCK_INSERTION_STATUS,
                EXCEL_COLUMN_BLOCK_IS_NESTED,
                EXCEL_COLUMN_BLOCK_NESTED_PARENT_NAMES,
                EXCEL_COLUMN_BLOCK_ENTITY_COUNT,
                EXCEL_COLUMN_BLOCK_INSERTION_COUNT,
                EXCEL_COLUMN_BLOCK_LAYER_COUNT,
                EXCEL_COLUMN_BLOCK_LAYER_NAMES,
                EXCEL_COLUMN_BLOCK_ROTATION_0,
                EXCEL_COLUMN_BLOCK_ROTATION_90,
                EXCEL_COLUMN_BLOCK_ROTATION_180,
                EXCEL_COLUMN_BLOCK_ROTATION_270,
                EXCEL_COLUMN_BLOCK_ROTATION_OTHER,
                EXCEL_COLUMN_BLOCK_SCALE_X,
                EXCEL_COLUMN_BLOCK_SCALE_Y,
            ]
        )
        df.columns = [format_header(col) for col in df.columns]
        df.to_excel(writer, sheet_name=EXCEL_SHEET_ALL_BLOCKS, index=False)
        return

    # Sort by insertion status (Inserted first), then by resolved name
    status_order = {
        "Inserted": 0,
        "Nested Only": 1,
        "Unused": 2,
        "Unresolved (*U)": 3,
        "Unresolved (A$C)": 4,
    }
    rows.sort(
        key=lambda r: (
            status_order.get(str(r[EXCEL_COLUMN_BLOCK_INSERTION_STATUS]), 99),
            str(r[EXCEL_COLUMN_BLOCK_RESOLVED_NAME]).lower(),
        )
    )

    df = pd.DataFrame(rows)

    # Format column headers for Excel display
    df.columns = [format_header(col) for col in df.columns]

    df.to_excel(writer, sheet_name=EXCEL_SHEET_ALL_BLOCKS, index=False)
    logger.info(f"All Blocks sheet created with {len(df)} rows")
