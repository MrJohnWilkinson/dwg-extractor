"""
DXF extraction logic for the DXF Block Extractor.

This module provides functionality to parse DXF files using the ezdxf library,
extract comprehensive CAD analysis including block counts, layer metrics, and entity types.

Usage:
    from core.extractor import extract_blocks

    result = extract_blocks('/path/to/drawing.dxf')
    # Returns: ExtractionResult with block_counts, block_entities, layer_insertions, etc.
"""

import re
import threading
import time
from pathlib import Path
from typing import Any, TypedDict

import ezdxf
from ezdxf import DXFError
from ezdxf import colors as ezdxf_colors
from ezdxf.document import Drawing

from .constants import (
    DEFAULT_GAP_CLOSURE_TOLERANCE,
    DEFAULT_MIN_AREA_FILTER,
    DEFAULT_MIN_SIDE_FILTER,
    DXF_INSUNITS_MAP,
    ENTITY_COUNT_THRESHOLD,
    LINE_SEGMENT_THRESHOLD,
    POLYGON_COUNT_THRESHOLD,
    SUPPORTED_EXTENSIONS,
)
from .geometry import (
    _calculate_segments,
    _categorize_rotation,
    _detect_content_zone,
    _get_block_bounding_box,
    _get_intersection_points,
)
from .logger import setup_logger
from .types import (
    AnnotationKey,
    BlockDefinitionRecord,
    BlockLayerKey,
    BlockRotationKey,
    BlockTrimmingData,
    ColorAnalysisRecord,
    ColorEntityKey,
    ContentZoneData,
    ExtractionIssue,
)


logger = setup_logger(__name__)

# Threshold for logging slow block processing (seconds)
SLOW_BLOCK_THRESHOLD_SECONDS = 3.0


class ExtractionAbortedError(Exception):
    """Raised when extraction is aborted by user."""

    pass


def _check_abort(abort_event: threading.Event | None, context: str) -> None:
    """
    Check if abort requested and raise if so.

    Args:
        abort_event: Optional threading.Event to check for abort signal
        context: Description of current operation for logging

    Raises:
        ExtractionAbortedError: If abort_event is set
    """
    if abort_event and abort_event.is_set():
        logger.info(f"Extraction aborted during {context}")
        raise ExtractionAbortedError(f"Aborted during {context}")


def _get_drawing_units(doc: Drawing) -> int:
    """
    Read the $INSUNITS header variable from a DXF document.

    The $INSUNITS header specifies the drawing units used for insertion,
    which typically reflects the units the drawing was created in.

    Args:
        doc: The ezdxf Drawing document to read units from

    Returns:
        The $INSUNITS value as an integer. Returns 0 (Unitless) if the
        header variable is missing or cannot be read.

    Examples:
        >>> doc = ezdxf.readfile('metric_drawing.dxf')
        >>> _get_drawing_units(doc)
        4  # Millimeters

        >>> doc = ezdxf.readfile('imperial_drawing.dxf')
        >>> _get_drawing_units(doc)
        1  # Inches

        >>> doc = ezdxf.readfile('old_drawing.dxf')  # No $INSUNITS header
        >>> _get_drawing_units(doc)
        0  # Unitless (fallback)
    """
    try:
        units_value = doc.header.get("$INSUNITS", 0)
        units: int = int(units_value) if units_value is not None else 0
        unit_name = DXF_INSUNITS_MAP.get(units, f"Unknown ({units})")
        logger.debug(f"Detected drawing units: {unit_name} (code={units})")
        return units
    except (AttributeError, KeyError) as e:
        logger.debug(
            f"Could not read $INSUNITS header: {e}, defaulting to 0 (Unitless)"
        )
        return 0


def get_snap_tolerances(
    detected_units: int,
    override_units: int | None,
    gap_bridge_enabled: bool,
    gap_bridge_amount: float | None,
    precision_fix_enabled: bool = True,
    precision_fix_amount: float | None = None,
) -> tuple[float, float]:
    """
    Calculate appropriate snap tolerances based on units and user settings.

    This function computes two tolerance values:
    1. Precision tolerance (Stage 1): Fixes floating-point artifacts at line endpoints
    2. Gap bridge tolerance (Stage 2): Bridges intentional small gaps in the drawing

    Args:
        detected_units: The unit code detected from the DXF file's $INSUNITS header
        override_units: User-selected unit override. If None or -1, use detected_units
        gap_bridge_enabled: Whether gap bridging is enabled by the user
        gap_bridge_amount: Custom gap bridge amount. If None or <= 0, use default for unit
        precision_fix_enabled: Whether precision fix (Stage 1) snapping is enabled.
                               When False, precision_tolerance is set to 0.0.
                               Defaults to True for backward compatibility.
        precision_fix_amount: Custom precision fix amount. If provided and > 0, this value
                              is used directly as the precision tolerance. If None, 0, or
                              negative, the default from DEFAULT_GAP_CLOSURE_TOLERANCE is
                              used instead of the old PRECISION_SNAP_TOLERANCE values.
                              Defaults to None.

    Returns:
        Tuple of (precision_tolerance, gap_bridge_tolerance):
        - precision_tolerance: Returns user-specified amount if provided and > 0,
                               otherwise returns default from DEFAULT_GAP_CLOSURE_TOLERANCE
                               for the effective unit when enabled, or 0.0 when disabled
        - gap_bridge_tolerance: Returns 0.0 if disabled, otherwise returns user amount or default

    Examples:
        >>> # Auto-detect units (mm), gap bridging disabled, default precision tolerance
        >>> get_snap_tolerances(4, None, False, None)
        (3.0, 0.0)  # Uses DEFAULT_GAP_CLOSURE_TOLERANCE[4]

        >>> # Override to inches, gap bridging enabled with default
        >>> get_snap_tolerances(4, 1, True, None)
        (0.125, 0.125)  # Uses inch default from DEFAULT_GAP_CLOSURE_TOLERANCE

        >>> # Custom precision fix amount
        >>> get_snap_tolerances(4, None, False, None, precision_fix_amount=0.05)
        (0.05, 0.0)  # Uses custom precision amount

        >>> # Precision fix disabled (ignores precision_fix_amount)
        >>> get_snap_tolerances(4, None, False, None, precision_fix_enabled=False, precision_fix_amount=0.05)
        (0.0, 0.0)  # Precision tolerance is 0.0 when disabled

        >>> # precision_fix_amount=0 uses default
        >>> get_snap_tolerances(4, None, False, None, precision_fix_amount=0.0)
        (3.0, 0.0)  # Uses DEFAULT_GAP_CLOSURE_TOLERANCE[4] when amount is 0
    """
    # Determine effective units: use override if provided and not -1
    if override_units is not None and override_units != -1:
        effective_units = override_units
        logger.debug(
            f"Using override units: {DXF_INSUNITS_MAP.get(effective_units, f'Unknown ({effective_units})')}"
        )
    else:
        effective_units = detected_units
        logger.debug(
            f"Using detected units: {DXF_INSUNITS_MAP.get(effective_units, f'Unknown ({effective_units})')}"
        )

    # Calculate precision tolerance
    # When precision_fix_enabled=False, set to 0.0 to disable Stage 1 snapping
    if precision_fix_enabled:
        if precision_fix_amount is not None and precision_fix_amount > 0:
            # Use user-specified custom amount
            precision_tolerance = precision_fix_amount
            logger.debug(f"Using custom precision fix amount: {precision_tolerance}")
        else:
            # Use DEFAULT_GAP_CLOSURE_TOLERANCE dict with fallback
            precision_tolerance = DEFAULT_GAP_CLOSURE_TOLERANCE.get(
                effective_units,
                DEFAULT_GAP_CLOSURE_TOLERANCE.get(0, 3.0),  # Fallback to unitless
            )
            logger.debug(
                f"Using default precision fix tolerance: {precision_tolerance}"
            )
    else:
        precision_tolerance = 0.0

    # Calculate gap bridge tolerance
    if not gap_bridge_enabled:
        gap_bridge_tolerance = 0.0
    elif gap_bridge_amount is not None and gap_bridge_amount > 0:
        # Use user-specified amount
        gap_bridge_tolerance = gap_bridge_amount
    else:
        # Use default for the effective unit
        gap_bridge_tolerance = DEFAULT_GAP_CLOSURE_TOLERANCE.get(
            effective_units,
            DEFAULT_GAP_CLOSURE_TOLERANCE.get(0, 3.0),  # Fallback to unitless default
        )

    logger.debug(
        f"Calculated tolerances: precision={precision_tolerance}, gap_bridge={gap_bridge_tolerance}"
    )

    return (precision_tolerance, gap_bridge_tolerance)


def get_filter_values(
    detected_units: int,
    override_units: int | None,
    min_area_enabled: bool,
    min_area_amount: float | None,
    min_side_enabled: bool,
    min_side_amount: float | None,
) -> tuple[float, float]:
    """
    Calculate min area and min side filter values based on settings.

    This function computes filter values for polygon filtering in content zone detection:
    - When a filter is disabled, returns 0.0 (no filtering)
    - When enabled with a positive amount, uses that amount
    - When enabled without an amount (None, 0, or negative), uses unit-specific default

    Args:
        detected_units: The unit code detected from the DXF file's $INSUNITS header
        override_units: User-selected unit override. If None or -1, use detected_units
        min_area_enabled: Whether minimum area filtering is enabled
        min_area_amount: Custom min area amount. If None or <= 0, use default for unit
        min_side_enabled: Whether minimum side filtering is enabled
        min_side_amount: Custom min side amount. If None or <= 0, use default for unit

    Returns:
        Tuple of (min_area, min_side):
        - min_area: Returns 0.0 if disabled, user amount if provided and > 0,
                    otherwise default from DEFAULT_MIN_AREA_FILTER for the effective unit
        - min_side: Returns 0.0 if disabled, user amount if provided and > 0,
                    otherwise default from DEFAULT_MIN_SIDE_FILTER for the effective unit

    Examples:
        >>> # Both filters disabled
        >>> get_filter_values(4, None, False, None, False, None)
        (0.0, 0.0)

        >>> # Area filter enabled with default, side filter disabled
        >>> get_filter_values(4, None, True, None, False, None)
        (100000.0, 0.0)  # Uses DEFAULT_MIN_AREA_FILTER[4]

        >>> # Both enabled with custom amounts
        >>> get_filter_values(4, None, True, 50.0, True, 5.0)
        (50.0, 5.0)

        >>> # Unit override affects default values
        >>> get_filter_values(4, 1, True, None, True, None)
        (155.0, 0.394)  # Uses inch defaults from constants
    """
    # Determine effective units: use override if provided and not -1
    if override_units is not None and override_units != -1:
        effective_units = override_units
        logger.debug(
            f"Using override units for filters: {DXF_INSUNITS_MAP.get(effective_units, f'Unknown ({effective_units})')}"
        )
    else:
        effective_units = detected_units
        logger.debug(
            f"Using detected units for filters: {DXF_INSUNITS_MAP.get(effective_units, f'Unknown ({effective_units})')}"
        )

    # Calculate min area filter value
    if not min_area_enabled:
        min_area = 0.0
    elif min_area_amount is not None and min_area_amount > 0:
        min_area = min_area_amount
        logger.debug(f"Using custom min area filter amount: {min_area}")
    else:
        min_area = DEFAULT_MIN_AREA_FILTER.get(effective_units, 100.0)
        logger.debug(f"Using default min area filter: {min_area}")

    # Calculate min side filter value
    if not min_side_enabled:
        min_side = 0.0
    elif min_side_amount is not None and min_side_amount > 0:
        min_side = min_side_amount
        logger.debug(f"Using custom min side filter amount: {min_side}")
    else:
        min_side = DEFAULT_MIN_SIDE_FILTER.get(effective_units, 10.0)
        logger.debug(f"Using default min side filter: {min_side}")

    logger.debug(f"Calculated filter values: min_area={min_area}, min_side={min_side}")

    return (min_area, min_side)


def _clean_mtext_content(entity: Any) -> str:
    """
    Clean MTEXT content by stripping formatting codes and normalizing whitespace.

    Uses ezdxf's built-in plain_text() method to remove formatting codes, then
    converts newlines to spaces and collapses multiple spaces.

    Args:
        entity: The MTEXT entity to extract clean text from

    Returns:
        Cleaned plain text string with formatting codes removed and whitespace normalized.

    Examples:
        >>> # MTEXT with paragraph alignment code
        >>> _clean_mtext_content(mtext_with_pxqc)  # raw: "\\pxqc;CENTERED"
        "CENTERED"

        >>> # MTEXT with paragraph breaks
        >>> _clean_mtext_content(mtext_with_breaks)  # raw: "LINE1\\PLINE2"
        "LINE1 LINE2"

        >>> # Complex formatting
        >>> _clean_mtext_content(mtext_complex)  # raw: "\\pxqc;MENS CASUAL\\P PANTS"
        "MENS CASUAL PANTS"
    """
    try:
        # Use ezdxf's plain_text() to strip formatting codes
        # split=False returns a single string (cast needed for type checker)
        plain_result = entity.plain_text(split=False)
        plain: str = (
            plain_result if isinstance(plain_result, str) else "\n".join(plain_result)
        )

        # Replace newlines with spaces (plain_text converts \P to newline)
        text = plain.replace("\n", " ")

        # Collapse multiple consecutive spaces into single space
        text = re.sub(r" +", " ", text)

        # Strip leading/trailing whitespace
        return text.strip()
    except (AttributeError, TypeError):
        # Fallback to raw text if plain_text() fails
        return str(entity.text) if hasattr(entity, "text") else ""


def _resolve_entity_color_with_aci(
    entity: Any, doc: Drawing
) -> tuple[tuple[int, int, int], int | None] | None:
    """
    Resolve an entity's color to RGB values and ACI (AutoCAD Color Index).

    Handles multiple color specifications including direct RGB (True Color),
    ByLayer, ByBlock, and ACI color indices.

    Args:
        entity: The ezdxf entity to resolve color for
        doc: The DXF document containing the entity

    Returns:
        Tuple of ((r, g, b), aci_value) where:
        - (r, g, b) are RGB values (0-255 range)
        - aci_value is the ACI index (0-256) or None for True Color
        Returns None if color cannot be resolved.

    Examples:
        >>> entity_true_color = ...  # Entity with True Color (24-bit RGB)
        >>> _resolve_entity_color_with_aci(entity_true_color, doc)
        ((255, 128, 0), None)  # Orange True Color, no ACI

        >>> entity_bylayer = ...  # Entity using ByLayer color
        >>> _resolve_entity_color_with_aci(entity_bylayer, doc)
        ((0, 255, 0), 256)  # Resolved RGB from layer, ACI 256 (ByLayer)

        >>> entity_aci = ...  # Entity with ACI color index 1 (red)
        >>> _resolve_entity_color_with_aci(entity_aci, doc)
        ((255, 0, 0), 1)  # Red, ACI 1

        >>> entity_byblock = ...  # Entity with ByBlock color
        >>> _resolve_entity_color_with_aci(entity_byblock, doc)
        ((255, 255, 255), 0)  # White fallback, ACI 0 (ByBlock)
    """
    try:
        # Try direct RGB color first (True Color - no ACI index)
        if hasattr(entity, "rgb") and entity.rgb is not None:
            rgb = entity.rgb
            if isinstance(rgb, tuple) and len(rgb) == 3:
                return ((int(rgb[0]), int(rgb[1]), int(rgb[2])), None)
            return None

        # Check for True Color (group code 420 - packed 24-bit RGB)
        try:
            true_color = entity.dxf.get("true_color", None)
            if true_color is not None:
                # Unpack 24-bit integer to RGB
                r = (true_color >> 16) & 0xFF
                g = (true_color >> 8) & 0xFF
                b = true_color & 0xFF
                logger.debug(f"Resolved True Color: RGB=({r}, {g}, {b})")
                return ((r, g, b), None)  # True Color has no ACI
        except (AttributeError, TypeError):
            pass

        # Get the color attribute
        if not hasattr(entity.dxf, "color"):
            return None

        color_value = entity.dxf.color

        # ByLayer color (256)
        if color_value == 256:
            try:
                layer_name = entity.dxf.layer
                layer = doc.layers.get(layer_name)
                if layer and hasattr(layer.dxf, "color"):
                    layer_color = layer.dxf.color
                    # Convert ACI to RGB
                    if 0 <= layer_color <= 255:
                        rgb = ezdxf_colors.aci2rgb(layer_color)
                        return (rgb, 256)  # Return ACI 256 (ByLayer)
            except (AttributeError, KeyError):
                pass
            return None

        # ByBlock color (0) - default to white as safe fallback
        if color_value == 0:
            return ((255, 255, 255), 0)  # Return ACI 0 (ByBlock)

        # ACI color index (1-255)
        if 1 <= color_value <= 255:
            rgb = ezdxf_colors.aci2rgb(color_value)
            return (rgb, color_value)

        # Invalid or unsupported color
        return None

    except (AttributeError, TypeError, ValueError):
        return None


def _resolve_entity_color_to_rgb(
    entity: Any, doc: Drawing
) -> tuple[int, int, int] | None:
    """
    Resolve an entity's color to RGB values.

    Handles multiple color specifications including direct RGB, ByLayer, ByBlock, and ACI color indices.
    This is a convenience wrapper around _resolve_entity_color_with_aci() for backwards compatibility.

    Args:
        entity: The ezdxf entity to resolve color for
        doc: The DXF document containing the entity

    Returns:
        Tuple of (r, g, b) values (0-255 range) or None if color cannot be resolved

    Examples:
        >>> entity_with_rgb = ...  # Entity with direct RGB color
        >>> _resolve_entity_color_to_rgb(entity_with_rgb, doc)
        (255, 0, 0)  # Red

        >>> entity_bylayer = ...  # Entity using ByLayer color
        >>> _resolve_entity_color_to_rgb(entity_bylayer, doc)
        (0, 255, 0)  # Resolved from layer color

        >>> entity_aci = ...  # Entity with ACI color index
        >>> _resolve_entity_color_to_rgb(entity_aci, doc)
        (255, 255, 0)  # Yellow

        >>> entity_invalid = ...  # Entity with invalid/missing color
        >>> _resolve_entity_color_to_rgb(entity_invalid, doc)
        None
    """
    result = _resolve_entity_color_with_aci(entity, doc)
    if result is None:
        return None
    return result[0]


def extract_color_analysis(doc: Drawing) -> list[ColorAnalysisRecord]:
    """
    Extract color analysis data from all Line, Polyline, HATCH, TEXT, and MTEXT entities.

    This function analyzes drawing entities grouped by their RGB color, layer name, and entity type.
    Geometric entities (Lines/Polylines/Hatches) are aggregated by unique combinations with counts.
    Text entities (TEXT/MTEXT) are extracted individually with full content.

    Args:
        doc: The ezdxf Drawing object to extract color analysis from

    Returns:
        List of color analysis records sorted by (color_r, color_g, color_b, layer_name, entity_type).
        Each record contains:
            - annotation_contents (str): Text content for TEXT/MTEXT, empty string for geometric entities
            - layer_name (str): Layer name of the entity
            - color_r (int): Red component 0-255
            - color_g (int): Green component 0-255
            - color_b (int): Blue component 0-255
            - color_aci (int | None): AutoCAD Color Index (0-256) or None for True Color
            - entity_type (str): 'Lines', 'Polylines', 'Hatches', 'TEXT', or 'MTEXT'
            - entity_count (int): Count of entities (1 for text, aggregate for geometric)

    Examples:
        >>> doc = ezdxf.readfile('drawing.dxf')
        >>> results = extract_color_analysis(doc)
        >>> results[0]
        {'annotation_contents': '', 'layer_name': 'WALLS', 'color_r': 255, 'color_g': 0, 'color_b': 0,
         'color_aci': 1, 'entity_type': 'Lines', 'entity_count': 45}
        >>> results[5]
        {'annotation_contents': 'DOOR', 'layer_name': 'NOTES', 'color_r': 0, 'color_g': 255, 'color_b': 0,
         'color_aci': 3, 'entity_type': 'TEXT', 'entity_count': 1}
    """
    try:
        logger.info("Starting color analysis extraction...")

        # Dictionary for grouping geometric entities using ColorEntityKey
        geometric_entities: dict[ColorEntityKey, int] = {}

        # List for text annotations (each is individual)
        text_annotations: list[ColorAnalysisRecord] = []

        msp = doc.modelspace()
        entity_count = 0
        total_entities = sum(1 for _ in msp)
        logger.debug(
            f"Color analysis starting with {total_entities} total modelspace entities"
        )

        # Re-iterate since we consumed the iterator
        msp = doc.modelspace()
        for entity in msp:
            entity_type = entity.dxftype()

            # Filter for relevant entity types
            if entity_type not in (
                "LINE",
                "LWPOLYLINE",
                "POLYLINE",
                "HATCH",
                "TEXT",
                "MTEXT",
            ):
                continue

            # Resolve entity color to RGB and ACI
            color_result = _resolve_entity_color_with_aci(entity, doc)
            if color_result is None:
                continue

            rgb, color_aci = color_result

            # Get layer name
            layer_name = entity.dxf.layer if hasattr(entity.dxf, "layer") else "0"

            color_r, color_g, color_b = rgb
            entity_count += 1

            # Handle geometric entities (Lines and Polylines)
            if entity_type == "LINE":
                key = ColorEntityKey(
                    color_r=color_r,
                    color_g=color_g,
                    color_b=color_b,
                    color_aci=color_aci,
                    layer_name=layer_name,
                    entity_type="Lines",
                )
                geometric_entities[key] = geometric_entities.get(key, 0) + 1

            elif entity_type in ("LWPOLYLINE", "POLYLINE"):
                key = ColorEntityKey(
                    color_r=color_r,
                    color_g=color_g,
                    color_b=color_b,
                    color_aci=color_aci,
                    layer_name=layer_name,
                    entity_type="Polylines",
                )
                geometric_entities[key] = geometric_entities.get(key, 0) + 1

            elif entity_type == "HATCH":
                key = ColorEntityKey(
                    color_r=color_r,
                    color_g=color_g,
                    color_b=color_b,
                    color_aci=color_aci,
                    layer_name=layer_name,
                    entity_type="Hatches",
                )
                geometric_entities[key] = geometric_entities.get(key, 0) + 1

            # Handle text entities (TEXT and MTEXT)
            elif entity_type == "TEXT":
                text_content = entity.dxf.text if hasattr(entity.dxf, "text") else ""
                text_annotations.append(
                    {
                        "annotation_contents": text_content,
                        "layer_name": layer_name,
                        "color_r": color_r,
                        "color_g": color_g,
                        "color_b": color_b,
                        "color_aci": color_aci,
                        "entity_type": "TEXT",
                        "entity_count": 1,
                    }
                )

            elif entity_type == "MTEXT":
                text_content = _clean_mtext_content(entity)
                text_annotations.append(
                    {
                        "annotation_contents": text_content,
                        "layer_name": layer_name,
                        "color_r": color_r,
                        "color_g": color_g,
                        "color_b": color_b,
                        "color_aci": color_aci,
                        "entity_type": "MTEXT",
                        "entity_count": 1,
                    }
                )

        logger.info(f"Processed {entity_count} entities for color analysis")
        logger.debug(
            f"Color analysis complete: {len(geometric_entities)} geometric groups, {len(text_annotations)} text entities"
        )

        # Convert geometric entities dict to list of records
        geometric_records: list[ColorAnalysisRecord] = [
            ColorAnalysisRecord(
                annotation_contents="",
                layer_name=key.layer_name,
                color_r=key.color_r,
                color_g=key.color_g,
                color_b=key.color_b,
                color_aci=key.color_aci,
                entity_type=key.entity_type,
                entity_count=count,
            )
            for key, count in geometric_entities.items()
        ]

        # Combine geometric and text records
        all_records = geometric_records + text_annotations

        # Sort by (color_r, color_g, color_b, layer_name, entity_type) - all ascending
        sorted_records = sorted(
            all_records,
            key=lambda x: (
                x["color_r"],
                x["color_g"],
                x["color_b"],
                x["layer_name"],
                x["entity_type"],
            ),
        )

        logger.info(
            f"Color analysis extraction complete: {len(sorted_records)} total records"
        )
        return sorted_records

    except Exception as e:
        logger.error(f"Error during color analysis extraction: {e}")
        return []


def _is_anonymous_block(block_name: str) -> bool:
    """
    Check if a block name represents an anonymous (dynamic) block instance.

    AutoCAD creates anonymous blocks for dynamic block instances using two
    naming conventions:
    - *U* pattern (e.g., *U1, *U25) - standard dynamic block instances
    - A$C* pattern (e.g., A$C7F63364D, A$C25B30886) - alternate naming with hex suffix

    Args:
        block_name: The block name to check

    Returns:
        True if the block is an anonymous dynamic block instance, False otherwise

    Examples:
        >>> _is_anonymous_block('*U1')
        True
        >>> _is_anonymous_block('A$C7F63364D')
        True
        >>> _is_anonymous_block('DOOR')
        False
        >>> _is_anonymous_block('*Model_Space')
        False  # System block, not dynamic block
    """
    return block_name.startswith("*U") or block_name.startswith("A$C")


def _resolve_dynamic_block_name(
    block_record: Any, doc: Drawing, block_name: str | None = None
) -> tuple[str | None, str]:
    """
    Resolve the original name for a dynamic block from XDATA.

    AutoCAD stores the original block name in XDATA under:
    - 'AcDbBlockRepBTag' - primary application ID for both *U and A$C blocks
    - 'AcDbDynamicBlockTrueName' - fallback for A$C blocks (but may self-reference)

    The original block name can be stored in XDATA as either:
    - Tag code 1000: ASCII string containing the block name directly
    - Tag code 1005: Database handle (hex string) pointing to the original block record

    Args:
        block_record: The ezdxf block table record to check for XDATA
        doc: The ezdxf Drawing document for resolving handle references
        block_name: Optional original block name (used to detect self-referencing XDATA)

    Returns:
        A tuple of (resolved_name, resolution_details):
        - resolved_name: The resolved block name if found, None if unresolved
        - resolution_details: String describing what was found/attempted:
            - "No XDATA found" - block_record has no xdata
            - "Resolved from AcDbBlockRepBTag tag 1000" - direct name resolution
            - "Resolved from AcDbBlockRepBTag handle {handle}" - handle resolution success
            - "Handle {handle} not found in document (orphaned dynamic block)" - handle missing
            - "Resolved from AcDbDynamicBlockTrueName" - fallback resolution
            - "Self-referencing XDATA" - when resolved name equals block_name
            - "AcDbBlockRepBTag XDATA present but no resolvable data" - XDATA exists but no 1000/1005

    Examples:
        >>> block_record = doc.blocks.get('*U1').block_record
        >>> _resolve_dynamic_block_name(block_record, doc)
        ('DOOR_DYNAMIC', 'Resolved from AcDbBlockRepBTag tag 1000')

        >>> block_record_no_xdata = doc.blocks.get('*U5').block_record
        >>> _resolve_dynamic_block_name(block_record_no_xdata, doc)
        (None, 'No XDATA found')

        >>> block_record_orphan = doc.blocks.get('*U999').block_record
        >>> _resolve_dynamic_block_name(block_record_orphan, doc)
        (None, 'Handle B0DE5 not found in document (orphaned dynamic block)')

        >>> block_record_self_ref = doc.blocks.get('A$C25B30886').block_record
        >>> _resolve_dynamic_block_name(block_record_self_ref, doc, 'A$C25B30886')
        (None, 'Self-referencing XDATA')
    """
    try:
        # Access the block record's XDATA
        # The block_record.xdata is a dictionary-like object mapping appids to tag data
        if not hasattr(block_record, "xdata") or block_record.xdata is None:
            return (None, "No XDATA found")

        # Check for AcDbBlockRepBTag application ID
        xdata = block_record.xdata
        if not hasattr(xdata, "get"):
            return (None, "No XDATA found")

        # Track if we found AcDbBlockRepBTag but couldn't resolve
        found_rep_btag = False
        orphaned_handle: str | None = None

        # Try AcDbBlockRepBTag first (primary resolution method)
        # Note: ezdxf's XData.get() raises DXFValueError if appid not found
        try:
            rep_btag_data = xdata.get("AcDbBlockRepBTag")
            if rep_btag_data is not None:
                found_rep_btag = True
                for tag in rep_btag_data:
                    # Group code 1000 contains string data (the original block name)
                    if hasattr(tag, "code") and tag.code == 1000:
                        original_name = tag.value
                        if isinstance(original_name, str) and original_name:
                            # Check for self-reference (e.g., A$C25B30886 -> A$C25B30886)
                            if block_name and original_name == block_name:
                                logger.debug(
                                    f"Self-referencing AcDbBlockRepBTag for {block_name}, treating as unresolved"
                                )
                                return (None, "Self-referencing XDATA")
                            logger.debug(
                                f"Resolved dynamic block name from AcDbBlockRepBTag: {original_name}"
                            )
                            return (
                                original_name,
                                "Resolved from AcDbBlockRepBTag tag 1000",
                            )
                    # Group code 1005 contains database handle pointing to original block
                    elif hasattr(tag, "code") and tag.code == 1005:
                        handle = tag.value
                        try:
                            # Resolve handle through document's entity database
                            original_block_record = doc.entitydb.get(handle)
                            if original_block_record is not None:
                                # Get the name from the resolved block record
                                if hasattr(original_block_record, "dxf") and hasattr(
                                    original_block_record.dxf, "name"
                                ):
                                    original_name = original_block_record.dxf.name
                                    if isinstance(original_name, str) and original_name:
                                        # Check for self-reference
                                        if block_name and original_name == block_name:
                                            logger.debug(
                                                f"Self-referencing handle in AcDbBlockRepBTag for {block_name}, treating as unresolved"
                                            )
                                            return (None, "Self-referencing XDATA")
                                        logger.debug(
                                            f"Resolved dynamic block name from AcDbBlockRepBTag handle {handle}: {original_name}"
                                        )
                                        return (
                                            original_name,
                                            f"Resolved from AcDbBlockRepBTag handle {handle}",
                                        )
                            else:
                                # Handle not found in document - this is an orphaned dynamic block
                                logger.debug(
                                    f"Handle {handle} not found in document entitydb (orphaned dynamic block)"
                                )
                                orphaned_handle = handle
                        except (KeyError, TypeError, AttributeError) as e:
                            logger.debug(
                                f"Failed to resolve handle {handle} in AcDbBlockRepBTag: {e}"
                            )
                            orphaned_handle = handle
        except (DXFError, KeyError):
            # AcDbBlockRepBTag not found in XDATA
            pass

        # If we found an orphaned handle, report it specifically
        if orphaned_handle is not None:
            return (
                None,
                f"Handle {orphaned_handle} not found in document (orphaned dynamic block)",
            )

        # Fallback: Try AcDbDynamicBlockTrueName (used by some A$C blocks)
        try:
            true_name_data = xdata.get("AcDbDynamicBlockTrueName")
            if true_name_data is not None:
                for tag in true_name_data:
                    if hasattr(tag, "code") and tag.code == 1000:
                        original_name = tag.value
                        if isinstance(original_name, str) and original_name:
                            # Check for self-reference
                            if block_name and original_name == block_name:
                                logger.debug(
                                    f"Self-referencing AcDbDynamicBlockTrueName for {block_name}, treating as unresolved"
                                )
                                return (None, "Self-referencing XDATA")
                            logger.debug(
                                f"Resolved dynamic block name from AcDbDynamicBlockTrueName: {original_name}"
                            )
                            return (
                                original_name,
                                "Resolved from AcDbDynamicBlockTrueName",
                            )
        except (DXFError, KeyError):
            # AcDbDynamicBlockTrueName not found in XDATA
            pass

        # If we found AcDbBlockRepBTag but couldn't extract a name, report that
        if found_rep_btag:
            return (None, "AcDbBlockRepBTag XDATA present but no resolvable data")

        return (None, "No AcDbBlockRepBTag XDATA found")

    except (AttributeError, TypeError, KeyError) as e:
        logger.debug(f"Error resolving dynamic block name: {e}")
        return (None, f"Error resolving XDATA: {e}")


class ExtractionResult(TypedDict):
    """
    Comprehensive extraction result containing all CAD analysis data.

    Attributes:
        block_counts: Dictionary mapping block names to insertion counts
        block_entities: Dictionary mapping block names to entity count within their definition
        block_layer_pairs: Dictionary mapping BlockLayerKey to insertion counts
        block_rotation_counts: Dictionary mapping BlockRotationKey to insertion counts
                               Rotation categories are strings: '0', '90', '180', '270', 'other'
        block_scale_data: Dictionary mapping block names to sets of unique (x_scale, y_scale) tuples
                          Tracks ALL unique scale combinations across all insertions and layers per block
                          Scale values indicate transformation factors (1.0 = normal, -1.0 = mirrored, 2.0 = 200%)
        block_xdata_apps: Dictionary mapping BlockLayerKey to sets of XDATA application IDs
                          Collects unique application IDs from XDATA attached to block INSERT entities
        layer_block_insertion_counts: Dictionary mapping layer names to block insertion counts on that layer
        layer_entity_counts: Dictionary mapping layer names to total entity counts on that layer
        layer_unique_color_counts: Dictionary mapping layer names to count of unique RGB color values on that layer
                                   Tracks distinct colors across all entities on each layer
        layer_annotation_counts: Dictionary mapping layer names to combined TEXT and MTEXT entity counts
                                Counts both TEXT (single-line) and MTEXT (multi-line) entities on each layer
                                Example: {'NOTES': 25, 'TITLE_BLOCK': 8, 'DIMENSIONS': 0}
        annotation_data: Dictionary mapping AnnotationKey to occurrence counts
                        Example: {AnnotationKey('DOOR', 'TEXT', 'NOTES', 255, 0, 0): 5}
        entity_type_counts: Dictionary mapping entity type names to their total count in the drawing
        block_trimming_data: Dictionary mapping block names to their geometry analysis data.
                             Each block entry contains: native_width (float), native_height (float),
                             vertical_segments (list[float] - left-to-right), horizontal_segments (list[float] - bottom-to-top)
        color_analysis_data: List of color analysis records. Each record contains: annotation_contents (str, blank for Lines/Polylines/Hatches),
                            layer_name (str), color_r (int 0-255), color_g (int 0-255), color_b (int 0-255),
                            entity_type (str: 'Lines', 'Polylines', 'Hatches', 'TEXT', 'MTEXT'), entity_count (int)
                            Example: [{'annotation_contents': '', 'layer_name': 'WALLS', 'color_r': 255, 'color_g': 0, 'color_b': 0,
                                      'entity_type': 'Lines', 'entity_count': 45}, ...]
        extraction_issues: List of extraction issue records for unresolved anonymous blocks and other issues.
                          Each record contains issue_type, block_name, layer_name, insertion_count, details.
                          Example: [{'issue_type': 'Unresolved Anonymous Block', 'block_name': '*U3',
                                    'layer_name': 'FIXTURES', 'insertion_count': 5,
                                    'details': 'No AcDbBlockRepBTag XDATA found'}]
        block_content_zone_data: Dictionary mapping block names to their content zone detection results.
                                Each block entry contains ContentZoneData with suggested_trim_left, suggested_trim_right,
                                suggested_trim_top, suggested_trim_bottom (all float | None), and content_zone_detected (bool).
                                Example: {'SHELF_4FT': {'suggested_trim_left': 10.0, 'suggested_trim_right': 10.0,
                                          'suggested_trim_top': 5.0, 'suggested_trim_bottom': 5.0, 'content_zone_detected': True}}
        all_block_definitions: Dictionary mapping raw block names to complete BlockDefinitionRecord entries.
                              Tracks every block definition in the DXF file with metadata including:
                              - block_raw_name: Original block name (e.g., '*U1', 'A$C7F63364D', 'DOOR')
                              - block_resolved_name: Resolved name for anonymous blocks, or same as raw_name
                              - block_insertion_status: One of 'Inserted', 'Nested Only', 'Unused', 'System',
                                'System (Dimension)', 'System (Hatch)', 'Unresolved (*U)', 'Unresolved (A$C)'
                              - block_is_nested: True if this block appears inside another block's definition
                              - block_nested_parent_names: Sorted list of parent block names that contain this block
                              - block_entity_count: Number of entities in the block definition
                              Example: {'DOOR': {'block_raw_name': 'DOOR', 'block_resolved_name': 'DOOR',
                                        'block_insertion_status': 'Inserted', 'block_is_nested': False,
                                        'block_nested_parent_names': [], 'block_entity_count': 12}}
        nested_block_parents: Dictionary mapping child block names to lists of parent block names.
                             Only includes blocks that are nested inside other blocks (via INSERT entities).
                             Parent names are sorted alphabetically for consistent output.
                             Example: {'HANDLE': ['DOOR', 'WINDOW'], 'HINGE': ['DOOR']}

    Examples:
        block_layer_pairs: {BlockLayerKey('DOOR', 'WALLS'): 5, BlockLayerKey('WINDOW', 'WALLS'): 8}
        block_rotation_counts: {BlockRotationKey('DOOR', 'WALLS', '0'): 12, BlockRotationKey('DOOR', 'WALLS', '90'): 18}
        block_scale_data: {'DOOR': {(1.0, 1.0), (2.0, 1.0)}, 'WINDOW': {(-1.0, 1.0)}}
        block_xdata_apps: {BlockLayerKey('DOOR', 'WALLS'): {'ACAD', 'CUSTOM_APP'}}
        layer_unique_color_counts: {'WALLS': 3, 'DOORS': 1, 'WINDOWS': 2}
        block_trimming_data: {'SHELF_4FT': {'native_width': 1200.0, 'native_height': 600.0,
                                             'vertical_segments': [50.0, 1100.0, 50.0],
                                             'horizontal_segments': [25.0, 550.0, 25.0]}}
    """

    block_counts: dict[str, int]
    block_entities: dict[str, int]
    block_layer_pairs: dict[BlockLayerKey, int]
    block_rotation_counts: dict[BlockRotationKey, int]
    block_scale_data: dict[str, set[tuple[float, float]]]
    block_xdata_apps: dict[BlockLayerKey, set[str]]
    layer_block_insertion_counts: dict[str, int]
    layer_entity_counts: dict[str, int]
    layer_unique_color_counts: dict[str, int]
    layer_annotation_counts: dict[str, int]
    annotation_data: dict[AnnotationKey, int]
    entity_type_counts: dict[str, int]
    block_trimming_data: dict[str, BlockTrimmingData]
    color_analysis_data: list[ColorAnalysisRecord]
    extraction_issues: list[ExtractionIssue]
    block_content_zone_data: dict[str, ContentZoneData]
    all_block_definitions: dict[str, BlockDefinitionRecord]
    nested_block_parents: dict[str, list[str]]


def extract_blocks(
    file_path: str,
    abort_event: threading.Event | None = None,
    *,
    unit_override: int | None = None,
    gap_bridge_enabled: bool = False,
    gap_bridge_amount: float | None = None,
    precision_fix_enabled: bool = True,
    precision_fix_amount: float | None = None,
    min_area_filter_enabled: bool = False,
    min_area_filter_amount: float | None = None,
    min_side_filter_enabled: bool = False,
    min_side_filter_amount: float | None = None,
    # Pre-Filters
    skip_curved_entities: bool = False,
    min_line_length_filter_enabled: bool = False,
    min_line_length_filter_amount: float | None = None,
    # Post-Filters
    curved_filter_enabled: bool = False,
    # Early-exit threshold parameters
    polygon_count_threshold: int | None = None,
    line_segment_threshold: int | None = None,
    entity_count_threshold: int | None = None,
) -> ExtractionResult:
    """
    Extract comprehensive CAD analysis from a DXF file.

    This function loads a CAD file and extracts:
    - Block insertion counts
    - Entity counts within each block definition
    - Block-layer pairs (unique combinations of block name and layer)
    - Block rotation counts for each block-layer pair
    - Layer-based insertion counts
    - Layer-based total entity counts
    - Global entity type counts
    - Block trimming analysis (native dimensions and geometric segments)

    Args:
        file_path: Path to the DXF file to process
        abort_event: Optional threading.Event to signal abort request.
                     When set, extraction will stop at the next checkpoint
                     and raise ExtractionAbortedError.
        unit_override: User-selected unit override. -1 for auto-detect, or
                       $INSUNITS value (0=Unitless, 1=IN, 2=FT, 4=MM, 5=CM,
                       6=M). None = auto.
        gap_bridge_enabled: Enable Stage 2 gap bridging. When True, applies
                            gap bridge tolerance to bridge intentional gaps.
        gap_bridge_amount: Custom gap bridge tolerance. None = use default
                           for unit.
        precision_fix_enabled: Enable Stage 1 precision fix snapping. When True,
                               applies precision tolerance to fix floating-point
                               artifacts. When False, disables precision snapping.
                               Defaults to True for backward compatibility.
        precision_fix_amount: Custom precision fix amount. If provided and > 0,
                              this value is used instead of the default tolerance
                              for the unit. If None, 0, or negative, uses the
                              default from DEFAULT_GAP_CLOSURE_TOLERANCE.
                              Defaults to None.
        min_area_filter_enabled: Enable minimum area filtering for content zone detection.
                                 When True, polygons with area below threshold are filtered out.
                                 Defaults to False.
        min_area_filter_amount: Custom minimum area threshold. If provided and > 0, this value
                                is used. If None, 0, or negative, uses the default from
                                DEFAULT_MIN_AREA_FILTER for the effective unit.
                                Defaults to None.
        min_side_filter_enabled: Enable minimum side filtering for content zone detection.
                                 When True, polygons with shortest side below threshold are
                                 filtered out. Defaults to False.
        min_side_filter_amount: Custom minimum side threshold. If provided and > 0, this value
                                is used. If None, 0, or negative, uses the default from
                                DEFAULT_MIN_SIDE_FILTER for the effective unit.
                                Defaults to None.
        skip_curved_entities: If True, skip CIRCLE and ARC entities during edge
                              extraction for content zone detection. Default False.
        min_line_length_filter_enabled: Enable minimum line length filtering.
                                        When True, short LINE entities are filtered out.
                                        Default False.
        min_line_length_filter_amount: Minimum line length threshold. Lines shorter
                                       than this are excluded. If None or <= 0, filter is inactive.
        curved_filter_enabled: Enable curved polygon post-filtering.
                               When True, polygons containing curved edges are filtered out.
                               Default False.
        polygon_count_threshold: Maximum polygons for content zone calculation.
                                 None uses default (500). Blocks exceeding this skip content zone.
        line_segment_threshold: Maximum edges for region detection.
                                None uses default (5000). Blocks exceeding this skip region detection.
        entity_count_threshold: Maximum entities for content zone detection.
                                None uses default (1000). Blocks exceeding this skip content zone.

    Returns:
        ExtractionResult TypedDict containing all analysis data.
        All dictionaries will be empty if the file contains no relevant data.

    Raises:
        FileNotFoundError: If the specified file does not exist
        ValueError: If the file extension is not supported or file is corrupted
        ExtractionAbortedError: If abort_event is set during extraction

    Examples:
        >>> result = extract_blocks('drawing.dxf')
        >>> result['block_counts']
        {'VALVE_GATE': 142, 'PIPE_SUPPORT': 89}
        >>> result['block_entities']
        {'VALVE_GATE': 8, 'PIPE_SUPPORT': 12}
        >>> result['block_layer_pairs']
        {('VALVE_GATE', 'Piping'): 100, ('VALVE_GATE', 'Equipment'): 42, ('PIPE_SUPPORT', 'Piping'): 89}
        >>> result['layer_block_insertion_counts']
        {'Piping': 200, 'Equipment': 31}
        >>> result['block_trimming_data']
        {'SHELF_4FT': {'native_width': 1200.0, 'native_height': 600.0, 'vertical_segments': [50.0, 1100.0, 50.0], 'horizontal_segments': [25.0, 550.0, 25.0]}}

        >>> # With custom precision fix amount
        >>> result = extract_blocks('drawing.dxf', precision_fix_amount=0.05)

        >>> # With polygon filtering enabled
        >>> result = extract_blocks('drawing.dxf', min_area_filter_enabled=True)

        >>> # With custom filter amounts
        >>> result = extract_blocks('drawing.dxf',
        ...     min_area_filter_enabled=True,
        ...     min_area_filter_amount=50.0,
        ...     min_side_filter_enabled=True,
        ...     min_side_filter_amount=5.0)
    """
    logger.info(f"Starting block extraction from {file_path}")

    # Validate file exists
    path = Path(file_path)
    if not path.exists():
        logger.error(f"File not found: {file_path}")
        raise FileNotFoundError(f"File not found: {file_path}")

    # Validate file extension
    if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
        logger.error(
            f"Unsupported file extension: {path.suffix}. Supported: {SUPPORTED_EXTENSIONS}"
        )
        raise ValueError(f"Unsupported file extension: {path.suffix}. Must be .dxf")

    try:
        # Initial abort check before any processing
        _check_abort(abort_event, "extraction start")

        # Load DXF file
        logger.debug(f"Loading DXF file: {file_path}")
        doc = ezdxf.readfile(file_path)
        logger.debug(f"DXF file loaded successfully: {file_path}")

        # Detect drawing units and calculate tolerances
        detected_units = _get_drawing_units(doc)
        precision_tolerance, gap_bridge_tolerance = get_snap_tolerances(
            detected_units,
            unit_override,
            gap_bridge_enabled,
            gap_bridge_amount,
            precision_fix_enabled,
            precision_fix_amount,
        )
        logger.info(
            f"Using tolerances: precision={precision_tolerance}, "
            f"gap_bridge={gap_bridge_tolerance} "
            f"(units={'auto' if unit_override in (None, -1) else unit_override}, "
            f"precision_fix={'enabled' if precision_fix_enabled else 'disabled'}, "
            f"precision_fix_amount={precision_fix_amount})"
        )

        # Calculate polygon filter values
        min_area, min_side = get_filter_values(
            detected_units,
            unit_override,
            min_area_filter_enabled,
            min_area_filter_amount,
            min_side_filter_enabled,
            min_side_filter_amount,
        )
        logger.info(
            f"Using polygon filters: min_area={min_area}, min_side={min_side} "
            f"(area_filter={'enabled' if min_area_filter_enabled else 'disabled'}, "
            f"side_filter={'enabled' if min_side_filter_enabled else 'disabled'})"
        )

        # Calculate effective min line length
        min_line_length = 0.0
        if min_line_length_filter_enabled and min_line_length_filter_amount:
            min_line_length = min_line_length_filter_amount
        logger.info(
            f"Using pre-filters: skip_curved={skip_curved_entities}, "
            f"min_line_length={min_line_length} "
            f"(min_line_filter={'enabled' if min_line_length_filter_enabled else 'disabled'})"
        )
        logger.info(
            f"Using post-filters: curved_filter={'enabled' if curved_filter_enabled else 'disabled'}"
        )

        msp = doc.modelspace()

        # Initialize result dictionaries
        block_counts: dict[str, int] = {}
        block_entities: dict[str, int] = {}
        block_layer_pairs: dict[BlockLayerKey, int] = {}
        block_rotation_counts: dict[BlockRotationKey, int] = {}
        block_scale_data: dict[str, set[tuple[float, float]]] = {}
        block_xdata_apps: dict[BlockLayerKey, set[str]] = {}
        layer_block_insertion_counts: dict[str, int] = {}
        layer_entity_counts: dict[str, int] = {}
        layer_unique_colors: dict[str, set[tuple[int, int, int]]] = {}
        layer_annotation_counts: dict[str, int] = {}
        annotation_data: dict[AnnotationKey, int] = {}
        entity_type_counts: dict[str, int] = {}
        block_trimming_data: dict[str, BlockTrimmingData] = {}
        block_content_zone_data: dict[str, ContentZoneData] = {}
        extraction_issues: list[ExtractionIssue] = []

        # Mapping from anonymous block names (*U1, *U2, etc.) to resolved original names
        anonymous_to_resolved: dict[str, str] = {}
        # Track unresolved anonymous blocks: {(anon_name, layer_name): count}
        unresolved_anonymous_blocks: dict[tuple[str, str], int] = {}
        # Store resolution details for each anonymous block (for accurate error messages)
        anonymous_resolution_details: dict[str, str] = {}

        # Track all block definitions and nested relationships
        all_block_definitions: dict[str, BlockDefinitionRecord] = {}
        nested_block_parents: dict[str, set[str]] = {}  # child_name -> {parent_names}

        # Initialize all layers from layer table with 0 counts
        logger.info("Initializing layers from layer table...")
        for layer in doc.layers:
            layer_name = layer.dxf.name
            # Skip system layers (modelspace/paperspace internal layers)
            if layer_name.startswith("*"):
                continue
            layer_entity_counts[layer_name] = 0
            layer_block_insertion_counts[layer_name] = 0
            layer_annotation_counts[layer_name] = 0
        logger.info(f"Initialized {len(layer_entity_counts)} layers from layer table")

        # Extract block definition entity counts and geometry analysis
        logger.info("Analyzing block definitions...")

        # PHASE 1: Build anonymous block mappings (must be sequential - reads XDATA)
        for block_def in doc.blocks:
            block_name = block_def.name

            if block_name.startswith("*U") or block_name.startswith("A$C"):
                try:
                    block_record = block_def.block_record
                    resolved_name, resolution_details = _resolve_dynamic_block_name(
                        block_record, doc, block_name
                    )
                    anonymous_resolution_details[block_name] = resolution_details
                    if resolved_name:
                        anonymous_to_resolved[block_name] = resolved_name
                    elif block_name.startswith("A$C"):
                        anonymous_to_resolved[block_name] = block_name
                except (AttributeError, TypeError) as e:
                    anonymous_resolution_details[block_name] = f"Error: {e}"
                    if block_name.startswith("A$C"):
                        anonymous_to_resolved[block_name] = block_name

        logger.info(
            f"Resolved {len(anonymous_to_resolved)} anonymous blocks to original names"
        )

        # PHASE 2: Sequential block geometry analysis
        for block_def in doc.blocks:
            block_name = block_def.name

            # Skip modelspace/paperspace blocks
            if block_name in ("*Model_Space", "*Paper_Space") or block_name.startswith(
                "*Paper_Space"
            ):
                continue

            # Handle anonymous blocks starting with *U (dynamic block instances)
            if block_name.startswith("*U"):
                if block_name in anonymous_to_resolved:
                    effective_name = anonymous_to_resolved[block_name]
                else:
                    continue  # Skip unresolved *U blocks
            elif block_name.startswith("A$C"):
                if block_name in anonymous_to_resolved:
                    effective_name = anonymous_to_resolved[block_name]
                else:
                    effective_name = block_name
            elif block_name.startswith("*"):
                continue  # Skip other system blocks
            else:
                effective_name = block_name

            logger.info(f"[BLOCK START] '{effective_name}'")

            # Start timing for this block
            block_start = time.perf_counter()

            # Count entities
            entity_count = sum(1 for _ in block_def)
            block_entities[effective_name] = entity_count

            # Scan for nested INSERTs
            for entity in block_def:
                if entity.dxftype() == "INSERT":
                    nested_name = entity.dxf.name
                    if nested_name in anonymous_to_resolved:
                        nested_name = anonymous_to_resolved[nested_name]
                    if nested_name not in nested_block_parents:
                        nested_block_parents[nested_name] = set()
                    nested_block_parents[nested_name].add(effective_name)

            # Analyze block geometry (with nested INSERT expansion)
            bbox = _get_block_bounding_box(block_def, doc)
            native_width = round(bbox[2] - bbox[0], 2)
            native_height = round(bbox[3] - bbox[1], 2)

            vertical_points, horizontal_points = _get_intersection_points(block_def)
            vertical_segments = _calculate_segments(vertical_points)
            horizontal_segments = _calculate_segments(horizontal_points)

            block_trimming_data[effective_name] = {
                "native_width": native_width,
                "native_height": native_height,
                "vertical_segments": vertical_segments,
                "horizontal_segments": horizontal_segments,
            }

            # Detect content zone
            # Use passed thresholds or fall back to constants
            effective_polygon_threshold = (
                polygon_count_threshold
                if polygon_count_threshold is not None
                else POLYGON_COUNT_THRESHOLD
            )
            effective_line_threshold = (
                line_segment_threshold
                if line_segment_threshold is not None
                else LINE_SEGMENT_THRESHOLD
            )
            effective_entity_threshold = (
                entity_count_threshold
                if entity_count_threshold is not None
                else ENTITY_COUNT_THRESHOLD
            )

            content_zone = _detect_content_zone(
                block_def,
                bbox,
                abort_event,
                precision_tolerance,
                gap_bridge_tolerance,
                min_area,
                min_side,
                skip_curved_entities,
                min_line_length,
                curved_filter_enabled,
                polygon_count_threshold=effective_polygon_threshold,
                line_segment_threshold=effective_line_threshold,
                entity_count_threshold=effective_entity_threshold,
            )
            block_content_zone_data[effective_name] = content_zone

            # Log block processing end with timing
            block_duration = time.perf_counter() - block_start
            if block_duration > SLOW_BLOCK_THRESHOLD_SECONDS:
                logger.info(
                    f"[TIMING] Block '{effective_name}' took {block_duration:.3f}s (>3s threshold)"
                )
            logger.info(f"[BLOCK END] '{effective_name}' ({block_duration:.3f}s)")

        logger.info(f"Analyzed {len(block_entities)} block definitions")
        logger.info(
            f"Analyzed geometry for {len(block_trimming_data)} block definitions"
        )

        # Iterate through modelspace entities
        logger.info("Analyzing modelspace entities...")
        entity_idx = 0
        for entity in msp:
            entity_idx += 1
            # Abort checkpoint every 500 entities
            if entity_idx % 500 == 0:
                _check_abort(abort_event, "modelspace entity processing")

            entity_type = entity.dxftype()
            layer_name = entity.dxf.layer

            # Count entity types
            entity_type_counts[entity_type] = entity_type_counts.get(entity_type, 0) + 1

            # Count entities per layer
            layer_entity_counts[layer_name] = layer_entity_counts.get(layer_name, 0) + 1

            # Extract TEXT and MTEXT annotation data
            if entity_type in ("TEXT", "MTEXT"):
                # Count annotations per layer
                layer_annotation_counts[layer_name] = (
                    layer_annotation_counts.get(layer_name, 0) + 1
                )

                # Extract annotation details for Annotations Analysis sheet
                try:
                    # Get text contents
                    if entity_type == "TEXT":
                        contents = (
                            entity.dxf.text if hasattr(entity.dxf, "text") else ""
                        )
                    else:  # MTEXT
                        contents = _clean_mtext_content(entity)

                    # Log annotation content (truncated to 50 chars)
                    preview = contents[:50] + "..." if len(contents) > 50 else contents
                    logger.debug(
                        f"Processing {entity_type}: layer={layer_name}, content={preview!r}"
                    )

                    # Resolve color to RGB
                    rgb_color = _resolve_entity_color_to_rgb(entity, doc)

                    # Only track if we have content and could resolve color
                    if contents and rgb_color is not None:
                        annotation_key = AnnotationKey(
                            annotation_contents=contents,
                            annotation_type=entity_type,
                            layer_name=layer_name,
                            color_r=rgb_color[0],
                            color_g=rgb_color[1],
                            color_b=rgb_color[2],
                        )
                        annotation_data[annotation_key] = (
                            annotation_data.get(annotation_key, 0) + 1
                        )
                except (AttributeError, TypeError):
                    # Skip entities with missing or invalid annotation data
                    pass

            # Extract entity color for layer color analysis
            try:
                # Try to get RGB color directly
                rgb_color = entity.rgb
                if rgb_color is not None:
                    # Initialize set if needed
                    if layer_name not in layer_unique_colors:
                        layer_unique_colors[layer_name] = set()
                    # Add RGB tuple to the set (ensures uniqueness)
                    layer_unique_colors[layer_name].add(rgb_color)
            except (AttributeError, TypeError):
                # Entity doesn't have rgb property or it's not accessible
                pass

            # Count INSERT entities (block insertions)
            if entity_type == "INSERT":
                original_block_name = entity.dxf.name
                is_unresolved_a_dollar_c = False

                # Handle anonymous blocks (*U blocks - dynamic block instances)
                if original_block_name.startswith("*U"):
                    if original_block_name in anonymous_to_resolved:
                        # Use the resolved original name
                        block_name = anonymous_to_resolved[original_block_name]
                        logger.debug(
                            f"Processing INSERT: anonymous block {original_block_name} resolved to {block_name}, layer={layer_name}"
                        )
                    else:
                        # Track unresolved anonymous block for extraction issues
                        anon_key = (original_block_name, layer_name)
                        unresolved_anonymous_blocks[anon_key] = (
                            unresolved_anonymous_blocks.get(anon_key, 0) + 1
                        )
                        logger.debug(
                            f"Processing INSERT: unresolved anonymous block {original_block_name}, layer={layer_name}"
                        )
                        # Skip further processing for unresolved *U blocks
                        # Still count as INSERT entity type and layer count
                        layer_block_insertion_counts[layer_name] = (
                            layer_block_insertion_counts.get(layer_name, 0) + 1
                        )
                        continue
                # Handle A$C blocks (alternate anonymous block naming convention)
                elif original_block_name.startswith("A$C"):
                    if original_block_name in anonymous_to_resolved:
                        resolved = anonymous_to_resolved[original_block_name]
                        # Check if it's an identity mapping (unresolved A$C block)
                        if resolved == original_block_name:
                            # Unresolved A$C block - use raw name but track in issues
                            block_name = original_block_name
                            is_unresolved_a_dollar_c = True
                            logger.debug(
                                f"Processing INSERT: unresolved A$C block {original_block_name}, layer={layer_name}"
                            )
                        else:
                            # Resolved A$C block - use resolved name
                            block_name = resolved
                            logger.debug(
                                f"Processing INSERT: A$C block {original_block_name} resolved to {block_name}, layer={layer_name}"
                            )
                    else:
                        # Not in mapping (shouldn't happen if block def was processed)
                        # Treat as unresolved and use raw name
                        block_name = original_block_name
                        is_unresolved_a_dollar_c = True
                        logger.debug(
                            f"Processing INSERT: A$C block {original_block_name} not in mapping, using raw name"
                        )
                else:
                    block_name = original_block_name

                # Track unresolved A$C blocks in extraction issues
                # (but still continue with full processing unlike *U)
                if is_unresolved_a_dollar_c:
                    anon_key = (original_block_name, layer_name)
                    unresolved_anonymous_blocks[anon_key] = (
                        unresolved_anonymous_blocks.get(anon_key, 0) + 1
                    )

                logger.debug(
                    f"Processing INSERT: block={block_name}, layer={layer_name}"
                )
                block_counts[block_name] = block_counts.get(block_name, 0) + 1
                layer_block_insertion_counts[layer_name] = (
                    layer_block_insertion_counts.get(layer_name, 0) + 1
                )

                # Track block-layer pairs
                pair_key = BlockLayerKey(
                    block_name=block_name,
                    layer_name=layer_name,
                )
                block_layer_pairs[pair_key] = block_layer_pairs.get(pair_key, 0) + 1

                # Track block rotation counts
                rotation = entity.dxf.rotation
                rotation_category = _categorize_rotation(rotation)
                logger.debug(
                    f"Rotation data: block={block_name}, rotation={rotation:.2f}°, category={rotation_category}"
                )
                rotation_key = BlockRotationKey(
                    block_name=block_name,
                    layer_name=layer_name,
                    rotation_category=rotation_category,
                )
                block_rotation_counts[rotation_key] = (
                    block_rotation_counts.get(rotation_key, 0) + 1
                )

                # Extract scale data (X and Y scale factors)
                try:
                    x_scale = entity.dxf.xscale
                    y_scale = entity.dxf.yscale
                except AttributeError:
                    # Default to 1.0 if scale attributes are missing
                    x_scale = 1.0
                    y_scale = 1.0

                logger.debug(
                    f"Scale data: block={block_name}, x_scale={x_scale}, y_scale={y_scale}"
                )

                # Store all unique scale combinations per block (across all layers)
                if block_name not in block_scale_data:
                    block_scale_data[block_name] = set()
                block_scale_data[block_name].add((x_scale, y_scale))

                # Extract XDATA application IDs
                # Access the xdata property which is a dictionary-like object
                try:
                    # The xdata attribute contains a dictionary mapping appids to tag data
                    if (
                        hasattr(entity, "xdata")
                        and entity.xdata is not None
                        and len(entity.xdata) > 0
                    ):
                        # Get all application IDs from the xdata dictionary
                        app_ids = (
                            list(entity.xdata.data.keys())
                            if hasattr(entity.xdata, "data")
                            else []
                        )
                        if app_ids:
                            # Initialize set if needed
                            if pair_key not in block_xdata_apps:
                                block_xdata_apps[pair_key] = set()
                            # Add all application IDs to the set
                            block_xdata_apps[pair_key].update(app_ids)
                except (AttributeError, TypeError):
                    # Entity doesn't support XDATA
                    pass

        # Convert color sets to counts
        layer_unique_color_counts: dict[str, int] = {
            layer: len(colors) for layer, colors in layer_unique_colors.items()
        }
        # Ensure all layers have a color count (0 for layers with no entities)
        for layer_name in layer_entity_counts.keys():
            if layer_name not in layer_unique_color_counts:
                layer_unique_color_counts[layer_name] = 0

        # Build complete block definition records after modelspace scan
        # This must happen AFTER block_counts is populated
        logger.info("Building complete block definition records...")

        def _classify_block_insertion_status(
            block_name: str,
            raw_name: str,
            block_counts: dict[str, int],
            nested_parents: dict[str, set[str]],
        ) -> str:
            """Determine insertion status for a block."""
            # System blocks
            if raw_name in ("*Model_Space", "*Paper_Space") or raw_name.startswith(
                "*Paper_Space"
            ):
                return "System"
            if (
                raw_name.startswith("*D")
                and len(raw_name) > 2
                and raw_name[2:].isdigit()
            ):
                return "System (Dimension)"
            if (
                raw_name.startswith("*X")
                and len(raw_name) > 2
                and raw_name[2:].isdigit()
            ):
                return "System (Hatch)"

            # Unresolved anonymous blocks
            if raw_name.startswith("*U") and raw_name not in anonymous_to_resolved:
                return "Unresolved (*U)"
            if raw_name.startswith("A$C"):
                resolved = anonymous_to_resolved.get(raw_name)
                if resolved is None or resolved == raw_name:
                    return "Unresolved (A$C)"

            # Regular/resolved blocks - check insertion status
            if block_name in block_counts:
                return "Inserted"
            if block_name in nested_parents:
                return "Nested Only"
            return "Unused"

        for block_def in doc.blocks:
            raw_name = block_def.name

            # Determine effective (resolved) name
            if raw_name in anonymous_to_resolved:
                effective_name = anonymous_to_resolved[raw_name]
            else:
                effective_name = raw_name

            # Count entities
            entity_count = sum(1 for _ in block_def)

            # Get parent names (sorted for consistency)
            parent_names = sorted(list(nested_block_parents.get(effective_name, set())))

            # Determine insertion status
            insertion_status = _classify_block_insertion_status(
                effective_name,
                raw_name,
                block_counts,
                nested_block_parents,
            )

            # Build record
            all_block_definitions[raw_name] = BlockDefinitionRecord(
                block_raw_name=raw_name,
                block_resolved_name=effective_name,
                block_insertion_status=insertion_status,
                block_is_nested=effective_name in nested_block_parents,
                block_nested_parent_names=parent_names,
                block_entity_count=entity_count,
            )

        logger.info(f"Tracked {len(all_block_definitions)} total block definitions")

        # Log summary
        total_insertions = sum(block_counts.values())
        unique_blocks = len(block_counts)
        total_entities = sum(entity_type_counts.values())
        unique_entity_types = len(entity_type_counts)
        total_layers = len(layer_entity_counts)

        logger.info(
            f"Found {total_insertions} block insertions across {unique_blocks} unique blocks"
        )
        logger.info(f"Found {len(block_layer_pairs)} unique block-layer pairs")
        logger.info(
            f"Tracked rotations for {len(block_rotation_counts)} block-layer-rotation combinations"
        )
        logger.info(f"Extracted scale data for {len(block_scale_data)} unique blocks")
        logger.info(f"Found XDATA on {len(block_xdata_apps)} block-layer pairs")
        logger.info(
            f"Found {total_entities} total entities across {unique_entity_types} entity types"
        )
        logger.info(f"Found {total_layers} layers in drawing")
        logger.info(f"Extracted color data for {len(layer_unique_color_counts)} layers")
        total_annotation_entities = sum(layer_annotation_counts.values())
        unique_annotation_groups = len(annotation_data)
        logger.info(
            f"Found {total_annotation_entities} annotation entities across {len(layer_annotation_counts)} layers"
        )
        logger.info(f"Extracted {unique_annotation_groups} unique annotation groups")

        # Extract color analysis data
        color_analysis_data = extract_color_analysis(doc)
        logger.info(f"Extracted {len(color_analysis_data)} color analysis records")

        # Convert unresolved anonymous blocks to extraction issues
        for (anon_name, issue_layer_name), count in unresolved_anonymous_blocks.items():
            # Use stored resolution details for accurate error messages
            if anon_name in anonymous_resolution_details:
                details = anonymous_resolution_details[anon_name]
            elif anon_name.startswith("A$C"):
                details = "No AcDbBlockRepBTag or AcDbDynamicBlockTrueName XDATA found (using raw A$C name)"
            else:
                details = "No AcDbBlockRepBTag XDATA found"
            extraction_issues.append(
                ExtractionIssue(
                    issue_type="Unresolved Anonymous Block",
                    block_name=anon_name,
                    layer_name=issue_layer_name,
                    insertion_count=count,
                    details=details,
                )
            )

        # Sort extraction issues by insertion count descending
        extraction_issues.sort(key=lambda x: x["insertion_count"], reverse=True)

        if extraction_issues:
            logger.info(
                f"Found {len(extraction_issues)} extraction issues ({sum(i['insertion_count'] for i in extraction_issues)} total insertions)"
            )

        # Return comprehensive result
        logger.debug("DIAG: Building result dictionary...")
        result: ExtractionResult = {
            "block_counts": block_counts,
            "block_entities": block_entities,
            "block_layer_pairs": block_layer_pairs,
            "block_rotation_counts": block_rotation_counts,
            "block_scale_data": block_scale_data,
            "block_xdata_apps": block_xdata_apps,
            "layer_block_insertion_counts": layer_block_insertion_counts,
            "layer_entity_counts": layer_entity_counts,
            "layer_unique_color_counts": layer_unique_color_counts,
            "layer_annotation_counts": layer_annotation_counts,
            "annotation_data": annotation_data,
            "entity_type_counts": entity_type_counts,
            "block_trimming_data": block_trimming_data,
            "color_analysis_data": color_analysis_data,
            "extraction_issues": extraction_issues,
            "block_content_zone_data": block_content_zone_data,
            "all_block_definitions": all_block_definitions,
            "nested_block_parents": {
                k: sorted(list(v)) for k, v in nested_block_parents.items()
            },
        }
        logger.debug("DIAG: Result dictionary built successfully")
        logger.debug(
            f"DIAG: nested_block_parents has {len(result['nested_block_parents'])} entries"
        )
        logger.debug("DIAG: About to return from extract_blocks")
        return result

    except (DXFError, IOError, OSError) as e:
        logger.error(f"Invalid or corrupted DXF file: {file_path} - {str(e)}")
        raise ValueError(f"Invalid or corrupted file: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error during extraction: {str(e)}", exc_info=True)
        raise
