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
    EXCEL_COLUMN_BLOCK_ENTITY_COUNT,
    EXCEL_COLUMN_BLOCK_HORIZONTAL_SEGMENTS,
    EXCEL_COLUMN_BLOCK_INSERTION_COUNT,
    EXCEL_COLUMN_BLOCK_LAYER_NAME,
    EXCEL_COLUMN_BLOCK_NAME,
    EXCEL_COLUMN_BLOCK_NATIVE_HEIGHT,
    EXCEL_COLUMN_BLOCK_NATIVE_WIDTH,
    EXCEL_COLUMN_BLOCK_ROTATION_0,
    EXCEL_COLUMN_BLOCK_ROTATION_90,
    EXCEL_COLUMN_BLOCK_ROTATION_180,
    EXCEL_COLUMN_BLOCK_ROTATION_270,
    EXCEL_COLUMN_BLOCK_ROTATION_OTHER,
    EXCEL_COLUMN_BLOCK_SCALE_X,
    EXCEL_COLUMN_BLOCK_SCALE_Y,
    EXCEL_COLUMN_BLOCK_VERTICAL_SEGMENTS,
    EXCEL_COLUMN_BLOCK_XDATA_APPS,
    EXCEL_COLUMN_COLOR_ANNOTATION_CONTENTS,
    EXCEL_COLUMN_COLOR_BLUE,
    EXCEL_COLUMN_COLOR_ENTITY_COUNT,
    EXCEL_COLUMN_COLOR_ENTITY_TYPE,
    EXCEL_COLUMN_COLOR_GREEN,
    EXCEL_COLUMN_COLOR_LAYER_NAME,
    EXCEL_COLUMN_COLOR_RED,
    EXCEL_COLUMN_COLOR_SAMPLE,
    EXCEL_COLUMN_ENTITY_TYPE_COUNT,
    EXCEL_COLUMN_ENTITY_TYPE_NAME,
    EXCEL_COLUMN_LAYER_ANNOTATION_COUNT,
    EXCEL_COLUMN_LAYER_BLOCK_INSERTION_COUNT,
    EXCEL_COLUMN_LAYER_ENTITY_COUNT,
    EXCEL_COLUMN_LAYER_NAME,
    EXCEL_COLUMN_LAYER_UNIQUE_COLOR_COUNT,
    EXCEL_SHEET_ANNOTATIONS_ANALYSIS,
    EXCEL_SHEET_BLOCK_ANALYSIS,
    EXCEL_SHEET_BLOCK_GEOMETRY_ANALYSIS,
    EXCEL_SHEET_COLOR_ANALYSIS,
    EXCEL_SHEET_ENTITY_SUMMARY,
    EXCEL_SHEET_LAYER_ANALYSIS,
)
from .excel_formatting import (
    _format_annotations_analysis_sheet,
    _format_block_analysis_sheet,
    _format_block_geometry_analysis_sheet,
    _format_color_analysis_sheet,
    _format_entity_summary_sheet,
    _format_layer_analysis_sheet,
    format_header,
)
from .extractor import ExtractionResult
from .logger import setup_logger


logger = setup_logger(__name__)


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


def write_excel(extraction_data: ExtractionResult, output_path: str) -> str:
    """
    Generate a multi-sheet Excel file from comprehensive CAD extraction data.

    This function creates an Excel workbook with five sheets:
    - Block Analysis: Simplified inventory with block-layer pairs and insertion counts
    - Layer Analysis: Layers with insertion counts and entity counts
    - Entity Summary: Entity types with total counts
    - Block Geometry Analysis: Consolidated transformations and geometry (rotations, scales, dimensions, segments)
    - Annotations Analysis: Text annotations (TEXT/MTEXT) with contents, type, layer, color, and counts

    All sheets include headers, appropriate sorting, auto-filters, and proper column widths.
    The Block Geometry Analysis sheet includes red highlighting for mirrored blocks (negative scales).
    The output filename is timestamped to prevent overwrites.

    Args:
        extraction_data: ExtractionResult TypedDict containing all CAD analysis data
        output_path: Path to the original DXF file (used for output filename)

    Returns:
        Full path to the created Excel file as a string

    Raises:
        ValueError: If extraction_data is None or invalid

    Examples:
        >>> result = extract_blocks('drawing.dxf')
        >>> excel_file = write_excel(result, 'drawing.dxf')
        >>> print(excel_file)
        '/path/to/drawing_blocks_20250117_143022.xlsx'
    """
    logger.info("Starting multi-sheet Excel file generation")

    # Validate input
    if extraction_data is None:
        logger.error("extraction_data cannot be None")
        raise ValueError("extraction_data cannot be None")

    try:
        # Generate timestamped filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        input_path = Path(output_path)
        filename = f"{input_path.stem}_blocks_{timestamp}.xlsx"
        full_path = input_path.parent / filename

        # Create Excel writer
        with pd.ExcelWriter(full_path, engine="openpyxl") as writer:
            # Sheet 1: Block Analysis
            _create_block_analysis_sheet(extraction_data, writer)

            # Sheet 2: Layer Analysis
            _create_layer_analysis_sheet(extraction_data, writer)

            # Sheet 3: Entity Summary
            _create_entity_summary_sheet(extraction_data, writer)

            # Sheet 4: Block Geometry Analysis
            _create_block_geometry_analysis_sheet(extraction_data, writer)

            # Sheet 5: Annotations Analysis
            _create_annotations_analysis_sheet(extraction_data, writer)

            # Sheet 6: Color Analysis
            _create_color_analysis_sheet(extraction_data, writer)

        # Load workbook for post-processing (formatting)
        wb = load_workbook(full_path)

        # Apply formatting to all sheets
        _format_block_analysis_sheet(wb)
        _format_layer_analysis_sheet(wb)
        _format_entity_summary_sheet(wb)
        _format_block_geometry_analysis_sheet(wb)
        _format_annotations_analysis_sheet(wb)
        _format_color_analysis_sheet(wb)

        # Save workbook with formatting
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

    if block_layer_pairs:
        # Unpack block-layer pairs into DataFrame rows (simplified - no rotations)
        rows = []
        for (block_name, layer_name), insertion_count in block_layer_pairs.items():
            entity_count = block_entities.get(block_name, 0)

            # Get XDATA apps for this block-layer pair
            xdata_apps = block_xdata_apps.get((block_name, layer_name), set())
            xdata_apps_str = ", ".join(sorted(xdata_apps)) if xdata_apps else "-"

            rows.append(
                {
                    EXCEL_COLUMN_BLOCK_NAME: block_name,
                    EXCEL_COLUMN_BLOCK_INSERTION_COUNT: insertion_count,
                    EXCEL_COLUMN_BLOCK_ENTITY_COUNT: entity_count,
                    EXCEL_COLUMN_BLOCK_LAYER_NAME: layer_name,
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

    if block_layer_pairs:
        # Build DataFrame rows from block-layer pairs with all geometry data
        rows = []
        for (block_name, layer_name), _insertion_count in block_layer_pairs.items():
            # Look up geometry data for this block
            geometry_data = block_trimming_data.get(block_name)

            # Skip blocks without geometry data (anonymous blocks, etc.)
            if geometry_data is None:
                continue

            # Extract rotation counts for this block-layer pair
            rot_0 = block_rotation_counts.get((block_name, layer_name, "0"), 0)
            rot_90 = block_rotation_counts.get((block_name, layer_name, "90"), 0)
            rot_180 = block_rotation_counts.get((block_name, layer_name, "180"), 0)
            rot_270 = block_rotation_counts.get((block_name, layer_name, "270"), 0)
            rot_other = block_rotation_counts.get((block_name, layer_name, "other"), 0)

            # Extract scale data for this block (all insertions across all layers)
            # Determine if X or Y scales vary, display "VARIES" or "VARIES (-)" or numeric value
            scale_set = block_scale_data.get(block_name, {(1.0, 1.0)})

            if _has_x_scale_variance(scale_set):
                if _has_negative_scale_in_set(scale_set, "x"):
                    x_scale: str | float = "VARIES (-)"
                else:
                    x_scale = "VARIES"
            else:
                x_scale = _get_single_scale_value(scale_set, "x")

            if _has_y_scale_variance(scale_set):
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
            horizontal_segments_str = (
                ", ".join(map(format_number, horizontal_segments))
                if horizontal_segments
                else ""
            )

            rows.append(
                {
                    EXCEL_COLUMN_BLOCK_NAME: block_name,
                    EXCEL_COLUMN_BLOCK_LAYER_NAME: layer_name,
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
                }
            )

        df = pd.DataFrame(rows)
        # Sort by block_name alphabetically
        df.sort_values(by=EXCEL_COLUMN_BLOCK_NAME, ascending=True, inplace=True)
    else:
        # Create empty DataFrame with headers only (all 13 columns)
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

    if annotation_data:
        # Build DataFrame rows from annotation data
        rows = []
        for (
            contents,
            annotation_type,
            layer_name,
            color_r,
            color_g,
            color_b,
        ), count in annotation_data.items():
            rows.append(
                {
                    EXCEL_COLUMN_ANNOTATION_CONTENTS: contents,
                    EXCEL_COLUMN_ANNOTATION_TYPE: annotation_type,
                    EXCEL_COLUMN_ANNOTATION_LAYER_NAME: layer_name,
                    EXCEL_COLUMN_ANNOTATION_COLOR_R: color_r,
                    EXCEL_COLUMN_ANNOTATION_COLOR_G: color_g,
                    EXCEL_COLUMN_ANNOTATION_COLOR_B: color_b,
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

    if color_analysis_data:
        # Build DataFrame directly from color analysis data
        rows = []
        for record in color_analysis_data:
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
                    EXCEL_COLUMN_COLOR_ENTITY_TYPE: record["entity_type"],
                    EXCEL_COLUMN_COLOR_ENTITY_COUNT: record["entity_count"],
                }
            )

        df = pd.DataFrame(rows)
        # Data is already sorted from extract_color_analysis()
    else:
        # Create empty DataFrame with headers only
        df = pd.DataFrame(
            columns=[
                EXCEL_COLUMN_COLOR_ANNOTATION_CONTENTS,
                EXCEL_COLUMN_COLOR_LAYER_NAME,
                EXCEL_COLUMN_COLOR_RED,
                EXCEL_COLUMN_COLOR_GREEN,
                EXCEL_COLUMN_COLOR_BLUE,
                EXCEL_COLUMN_COLOR_SAMPLE,
                EXCEL_COLUMN_COLOR_ENTITY_TYPE,
                EXCEL_COLUMN_COLOR_ENTITY_COUNT,
            ]
        )

    # Format column headers for Excel display
    df.columns = [format_header(col) for col in df.columns]

    df.to_excel(writer, sheet_name=EXCEL_SHEET_COLOR_ANALYSIS, index=False)
    logger.info(f"Color Analysis sheet created with {len(df)} rows")
