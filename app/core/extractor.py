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
from .types import BlockTrimmingData, ColorAnalysisRecord


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
        plain: str = plain_result if isinstance(plain_result, str) else "\n".join(plain_result)

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

        # Dictionary for grouping geometric entities: (R, G, B, ACI, layer_name, entity_type) -> count
        geometric_entities: dict[tuple[int, int, int, int | None, str, str], int] = {}

        # List for text annotations (each is individual)
        text_annotations: list[ColorAnalysisRecord] = []

        msp = doc.modelspace()
        entity_count = 0

        for entity in msp:
            entity_type = entity.dxftype()

            # Filter for relevant entity types
            if entity_type not in ("LINE", "LWPOLYLINE", "POLYLINE", "HATCH", "TEXT", "MTEXT"):
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
                key = (color_r, color_g, color_b, color_aci, layer_name, "Lines")
                geometric_entities[key] = geometric_entities.get(key, 0) + 1

            elif entity_type in ("LWPOLYLINE", "POLYLINE"):
                key = (color_r, color_g, color_b, color_aci, layer_name, "Polylines")
                geometric_entities[key] = geometric_entities.get(key, 0) + 1

            elif entity_type == "HATCH":
                key = (color_r, color_g, color_b, color_aci, layer_name, "Hatches")
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

        # Convert geometric entities dict to list of records
        geometric_records: list[ColorAnalysisRecord] = [
            ColorAnalysisRecord(
                annotation_contents="",
                layer_name=layer_name,
                color_r=color_r,
                color_g=color_g,
                color_b=color_b,
                color_aci=color_aci,
                entity_type=entity_type,
                entity_count=count,
            )
            for (
                color_r,
                color_g,
                color_b,
                color_aci,
                layer_name,
                entity_type,
            ), count in geometric_entities.items()
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


class ExtractionResult(TypedDict):
    """
    Comprehensive extraction result containing all CAD analysis data.

    Attributes:
        block_counts: Dictionary mapping block names to insertion counts
        block_entities: Dictionary mapping block names to entity count within their definition
        block_layer_pairs: Dictionary mapping (block_name, layer_name) tuples to insertion counts
        block_rotation_counts: Dictionary mapping (block_name, layer_name, rotation_category) tuples to insertion counts
                               Rotation categories are strings: '0', '90', '180', '270', 'other'
        block_scale_data: Dictionary mapping block names to sets of unique (x_scale, y_scale) tuples
                          Tracks ALL unique scale combinations across all insertions and layers per block
                          Scale values indicate transformation factors (1.0 = normal, -1.0 = mirrored, 2.0 = 200%)
        block_xdata_apps: Dictionary mapping (block_name, layer_name) tuples to sets of XDATA application IDs
                          Collects unique application IDs from XDATA attached to block INSERT entities
        layer_block_insertion_counts: Dictionary mapping layer names to block insertion counts on that layer
        layer_entity_counts: Dictionary mapping layer names to total entity counts on that layer
        layer_unique_color_counts: Dictionary mapping layer names to count of unique RGB color values on that layer
                                   Tracks distinct colors across all entities on each layer
        layer_annotation_counts: Dictionary mapping layer names to combined TEXT and MTEXT entity counts
                                Counts both TEXT (single-line) and MTEXT (multi-line) entities on each layer
                                Example: {'NOTES': 25, 'TITLE_BLOCK': 8, 'DIMENSIONS': 0}
        annotation_data: Dictionary mapping annotation tuples to occurrence counts
                        Key: (contents, type, layer_name, color_r, color_g, color_b)
                        Value: count of annotations with that unique combination
                        Example: {('DOOR', 'TEXT', 'NOTES', 255, 0, 0): 5, ('WINDOW', 'MTEXT', 'NOTES', 0, 255, 0): 3}
        entity_type_counts: Dictionary mapping entity type names to their total count in the drawing
        block_trimming_data: Dictionary mapping block names to their geometry analysis data.
                             Each block entry contains: native_width (float), native_height (float),
                             vertical_segments (list[float] - left-to-right), horizontal_segments (list[float] - bottom-to-top)
        color_analysis_data: List of color analysis records. Each record contains: annotation_contents (str, blank for Lines/Polylines/Hatches),
                            layer_name (str), color_r (int 0-255), color_g (int 0-255), color_b (int 0-255),
                            entity_type (str: 'Lines', 'Polylines', 'Hatches', 'TEXT', 'MTEXT'), entity_count (int)
                            Example: [{'annotation_contents': '', 'layer_name': 'WALLS', 'color_r': 255, 'color_g': 0, 'color_b': 0,
                                      'entity_type': 'Lines', 'entity_count': 45}, ...]

    Examples:
        block_layer_pairs: {('DOOR', 'WALLS'): 5, ('DOOR', 'OPENINGS'): 3, ('WINDOW', 'WALLS'): 8}
        block_rotation_counts: {('DOOR', 'WALLS', '0'): 12, ('DOOR', 'WALLS', '90'): 18, ('DOOR', 'WALLS', '180'): 10}
        block_scale_data: {'DOOR': {(1.0, 1.0), (2.0, 1.0)}, 'WINDOW': {(-1.0, 1.0)}}
        block_xdata_apps: {('DOOR', 'WALLS'): {'ACAD', 'CUSTOM_APP'}, ('WINDOW', 'WALLS'): {'BIM_TOOL'}}
        layer_unique_color_counts: {'WALLS': 3, 'DOORS': 1, 'WINDOWS': 2}
        block_trimming_data: {'SHELF_4FT': {'native_width': 1200.0, 'native_height': 600.0,
                                             'vertical_segments': [50.0, 1100.0, 50.0],
                                             'horizontal_segments': [25.0, 550.0, 25.0]}}
    """

    block_counts: dict[str, int]
    block_entities: dict[str, int]
    block_layer_pairs: dict[tuple[str, str], int]
    block_rotation_counts: dict[tuple[str, str, str], int]
    block_scale_data: dict[str, set[tuple[float, float]]]
    block_xdata_apps: dict[tuple[str, str], set[str]]
    layer_block_insertion_counts: dict[str, int]
    layer_entity_counts: dict[str, int]
    layer_unique_color_counts: dict[str, int]
    layer_annotation_counts: dict[str, int]
    annotation_data: dict[tuple[str, str, str, int, int, int], int]
    entity_type_counts: dict[str, int]
    block_trimming_data: dict[str, BlockTrimmingData]
    color_analysis_data: list[ColorAnalysisRecord]


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
        raise ValueError(
            f"Unsupported file extension: {path.suffix}. Must be .dxf"
        )

    try:
        # Load DXF file
        doc = ezdxf.readfile(file_path)
        msp = doc.modelspace()

        # Initialize result dictionaries
        block_counts: dict[str, int] = {}
        block_entities: dict[str, int] = {}
        block_layer_pairs: dict[tuple[str, str], int] = {}
        block_rotation_counts: dict[tuple[str, str, str], int] = {}
        block_scale_data: dict[str, set[tuple[float, float]]] = {}
        block_xdata_apps: dict[tuple[str, str], set[str]] = {}
        layer_block_insertion_counts: dict[str, int] = {}
        layer_entity_counts: dict[str, int] = {}
        layer_unique_colors: dict[str, set[tuple[int, int, int]]] = {}
        layer_annotation_counts: dict[str, int] = {}
        annotation_data: dict[tuple[str, str, str, int, int, int], int] = {}
        entity_type_counts: dict[str, int] = {}
        block_trimming_data: dict[str, BlockTrimmingData] = {}

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
            # Skip anonymous blocks and modelspace/paperspace
            if block_name.startswith("*"):
                continue

            entity_count = sum(1 for _ in block_def)
            block_entities[block_name] = entity_count

            # Analyze block geometry for trimming assistance
            bbox = _get_block_bounding_box(block_def)
            native_width = round(bbox[2] - bbox[0], 2)
            native_height = round(bbox[3] - bbox[1], 2)

            vertical_points, horizontal_points = _get_intersection_points(block_def)
            vertical_segments = _calculate_segments(vertical_points)
            horizontal_segments = _calculate_segments(horizontal_points)

            block_trimming_data[block_name] = {
                "native_width": native_width,
                "native_height": native_height,
                "vertical_segments": vertical_segments,
                "horizontal_segments": horizontal_segments,
            }

        logger.info(f"Analyzed {len(block_entities)} block definitions")
        logger.info(
            f"Analyzed geometry for {len(block_trimming_data)} block definitions"
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

                    # Resolve color to RGB
                    rgb_color = _resolve_entity_color_to_rgb(entity, doc)

                    # Only track if we have content and could resolve color
                    if contents and rgb_color is not None:
                        annotation_key = (
                            contents,
                            entity_type,
                            layer_name,
                            rgb_color[0],
                            rgb_color[1],
                            rgb_color[2],
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
                block_name = entity.dxf.name
                block_counts[block_name] = block_counts.get(block_name, 0) + 1
                layer_block_insertion_counts[layer_name] = (
                    layer_block_insertion_counts.get(layer_name, 0) + 1
                )

                # Track block-layer pairs
                pair_key = (block_name, layer_name)
                block_layer_pairs[pair_key] = block_layer_pairs.get(pair_key, 0) + 1

                # Track block rotation counts
                rotation = entity.dxf.rotation
                rotation_category = _categorize_rotation(rotation)
                rotation_key = (block_name, layer_name, rotation_category)
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
        }

        return result

    except (DXFError, IOError, OSError) as e:
        logger.error(f"Invalid or corrupted DXF file: {file_path} - {str(e)}")
        raise ValueError(f"Invalid or corrupted file: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error during extraction: {str(e)}", exc_info=True)
        raise
