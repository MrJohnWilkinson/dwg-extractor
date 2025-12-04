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
from pathlib import Path
from typing import Any, TypedDict

import ezdxf
from ezdxf import DXFError
from ezdxf import colors as ezdxf_colors
from ezdxf.document import Drawing

from .constants import SUPPORTED_EXTENSIONS
from .geometry import (
    _calculate_segments,
    _categorize_rotation,
    _get_block_bounding_box,
    _get_intersection_points,
)
from .logger import setup_logger
from .types import (
    AnnotationKey,
    BlockLayerKey,
    BlockRotationKey,
    BlockTrimmingData,
    ColorAnalysisRecord,
    ColorEntityKey,
    ExtractionIssue,
)


logger = setup_logger(__name__)


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
        logger.debug(f"Color analysis starting with {total_entities} total modelspace entities")

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
                            return (original_name, "Resolved from AcDbBlockRepBTag tag 1000")
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
                                        return (original_name, f"Resolved from AcDbBlockRepBTag handle {handle}")
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
            return (None, f"Handle {orphaned_handle} not found in document (orphaned dynamic block)")

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
                            return (original_name, "Resolved from AcDbDynamicBlockTrueName")
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


def extract_blocks(file_path: str) -> ExtractionResult:
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

    Returns:
        ExtractionResult TypedDict containing all analysis data.
        All dictionaries will be empty if the file contains no relevant data.

    Raises:
        FileNotFoundError: If the specified file does not exist
        ValueError: If the file extension is not supported or file is corrupted

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
        # Load DXF file
        logger.debug(f"Loading DXF file: {file_path}")
        doc = ezdxf.readfile(file_path)
        logger.debug(f"DXF file loaded successfully: {file_path}")
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
        extraction_issues: list[ExtractionIssue] = []

        # Mapping from anonymous block names (*U1, *U2, etc.) to resolved original names
        anonymous_to_resolved: dict[str, str] = {}
        # Track unresolved anonymous blocks: {(anon_name, layer_name): count}
        unresolved_anonymous_blocks: dict[tuple[str, str], int] = {}
        # Store resolution details for each anonymous block (for accurate error messages)
        anonymous_resolution_details: dict[str, str] = {}

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
        for block_def in doc.blocks:
            block_name = block_def.name

            # Skip modelspace/paperspace blocks
            if block_name in ("*Model_Space", "*Paper_Space") or block_name.startswith(
                "*Paper_Space"
            ):
                continue

            # Handle anonymous blocks starting with *U (dynamic block instances)
            if block_name.startswith("*U"):
                # Try to resolve original name from XDATA on block record
                try:
                    block_record = block_def.block_record
                    resolved_name, resolution_details = _resolve_dynamic_block_name(block_record, doc, block_name)
                    # Store resolution details for accurate error reporting later
                    anonymous_resolution_details[block_name] = resolution_details
                    if resolved_name:
                        # Store mapping for INSERT processing
                        anonymous_to_resolved[block_name] = resolved_name
                        logger.debug(
                            f"Resolved anonymous block {block_name} to {resolved_name}"
                        )
                        # Use the resolved name for all processing
                        effective_name = resolved_name
                    else:
                        # Track as unresolved - will be counted during INSERT processing
                        logger.debug(
                            f"Anonymous block {block_name} has no resolvable XDATA: {resolution_details}"
                        )
                        continue  # Skip geometry analysis for unresolved *U blocks
                except (AttributeError, TypeError) as e:
                    logger.debug(f"Error accessing block record for {block_name}: {e}")
                    anonymous_resolution_details[block_name] = f"Error accessing block record: {e}"
                    continue
            # Handle A$C blocks (alternate anonymous block naming convention)
            elif block_name.startswith("A$C"):
                # Try to resolve original name from XDATA on block record
                try:
                    block_record = block_def.block_record
                    resolved_name, resolution_details = _resolve_dynamic_block_name(block_record, doc, block_name)
                    # Store resolution details for accurate error reporting later
                    anonymous_resolution_details[block_name] = resolution_details
                    if resolved_name:
                        # Store mapping for INSERT processing
                        anonymous_to_resolved[block_name] = resolved_name
                        logger.debug(
                            f"Resolved A$C block {block_name} to {resolved_name}"
                        )
                        # Use the resolved name for all processing
                        effective_name = resolved_name
                    else:
                        # Unlike *U, unresolved A$C blocks ARE processed with raw name
                        # Store identity mapping for INSERT processing (to track in issues)
                        anonymous_to_resolved[block_name] = block_name
                        logger.debug(
                            f"A$C block {block_name} has no resolvable XDATA, using raw name: {resolution_details}"
                        )
                        effective_name = block_name
                except (AttributeError, TypeError) as e:
                    logger.debug(f"Error accessing block record for {block_name}: {e}")
                    # Still process with raw name
                    anonymous_to_resolved[block_name] = block_name
                    anonymous_resolution_details[block_name] = f"Error accessing block record: {e}"
                    effective_name = block_name
            # Skip other anonymous blocks (dimension blocks, hatch patterns, etc.)
            elif block_name.startswith("*"):
                continue
            else:
                effective_name = block_name

            logger.debug(f"Analyzing block definition: {effective_name}")
            entity_count = sum(1 for _ in block_def)
            block_entities[effective_name] = entity_count

            # Analyze block geometry for trimming assistance
            bbox = _get_block_bounding_box(block_def)
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

        logger.info(f"Analyzed {len(block_entities)} block definitions")
        logger.info(
            f"Analyzed geometry for {len(block_trimming_data)} block definitions"
        )
        logger.info(
            f"Resolved {len(anonymous_to_resolved)} anonymous blocks to original names"
        )

        # Iterate through modelspace entities
        logger.info("Analyzing modelspace entities...")
        for entity in msp:
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

                logger.debug(f"Processing INSERT: block={block_name}, layer={layer_name}")
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
        }

        return result

    except (DXFError, IOError, OSError) as e:
        logger.error(f"Invalid or corrupted DXF file: {file_path} - {str(e)}")
        raise ValueError(f"Invalid or corrupted file: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error during extraction: {str(e)}", exc_info=True)
        raise
