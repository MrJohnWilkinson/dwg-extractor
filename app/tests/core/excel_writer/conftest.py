"""Shared fixtures for excel_writer tests."""

import tempfile
from typing import Iterator

import pytest

from core.extractor import ExtractionResult
from core.types import AnnotationKey, BlockLayerKey, BlockRotationKey


@pytest.fixture
def temp_dir() -> Iterator[str]:
    """Create a temporary directory for test outputs."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def sample_extraction_data() -> ExtractionResult:
    """Provide sample extraction data for testing."""
    return {
        "block_counts": {"VALVE": 10, "PIPE": 5, "TAG": 3},
        "block_entities": {"VALVE": 8, "PIPE": 12, "TAG": 4},
        "block_layer_pairs": {
            BlockLayerKey(block_name="VALVE", layer_name="Layer1"): 7,
            BlockLayerKey(block_name="VALVE", layer_name="Layer2"): 3,
            BlockLayerKey(block_name="PIPE", layer_name="Layer1"): 5,
            BlockLayerKey(block_name="TAG", layer_name="Layer1"): 3,
        },
        "block_rotation_counts": {
            BlockRotationKey(
                block_name="VALVE", layer_name="Layer1", rotation_category="0"
            ): 5,
            BlockRotationKey(
                block_name="VALVE", layer_name="Layer1", rotation_category="90"
            ): 2,
            BlockRotationKey(
                block_name="VALVE", layer_name="Layer2", rotation_category="0"
            ): 3,
            BlockRotationKey(
                block_name="PIPE", layer_name="Layer1", rotation_category="0"
            ): 3,
            BlockRotationKey(
                block_name="PIPE", layer_name="Layer1", rotation_category="180"
            ): 2,
            BlockRotationKey(
                block_name="TAG", layer_name="Layer1", rotation_category="other"
            ): 3,
        },
        "block_scale_data": {
            "VALVE": {(1.0, 1.0), (-1.0, 1.0)},
            "PIPE": {(1.0, -1.0)},
            "TAG": {(-1.0, -1.0)},
        },
        "block_xdata_apps": {},
        "layer_block_insertion_counts": {"Layer1": 15, "Layer2": 3},
        "layer_entity_counts": {"Layer1": 25, "Layer2": 10},
        "layer_unique_color_counts": {"Layer1": 3, "Layer2": 1},
        "layer_annotation_counts": {"Layer1": 5, "Layer2": 2},
        "annotation_data": {},
        "entity_type_counts": {"INSERT": 18, "LINE": 15, "CIRCLE": 8},
        "color_analysis_data": [],
        "extraction_issues": [],
        "block_trimming_data": {
            "VALVE": {
                "native_width": 100.0,
                "native_height": 50.0,
                "vertical_segments": [10.0, 80.0, 10.0],
                "horizontal_segments": [5.0, 40.0, 5.0],
            },
            "PIPE": {
                "native_width": 200.0,
                "native_height": 100.0,
                "vertical_segments": [20.0, 160.0, 20.0],
                "horizontal_segments": [10.0, 80.0, 10.0],
            },
            "TAG": {
                "native_width": 50.0,
                "native_height": 25.0,
                "vertical_segments": [50.0],
                "horizontal_segments": [25.0],
            },
        },
        "block_content_zone_data": {
            "VALVE": {
                "suggested_trim_left": 10.0,
                "suggested_trim_right": 10.0,
                "suggested_trim_top": 5.0,
                "suggested_trim_bottom": 5.0,
                "content_zone_detected": True,
                "content_zone_width": 80.0,
                "content_zone_height": 40.0,
                "polygon_count": 2,
                "filtered_polygon_count": 2,
            },
            "PIPE": {
                "suggested_trim_left": 20.0,
                "suggested_trim_right": 20.0,
                "suggested_trim_top": 10.0,
                "suggested_trim_bottom": 10.0,
                "content_zone_detected": True,
                "content_zone_width": 160.0,
                "content_zone_height": 80.0,
                "polygon_count": 2,
                "filtered_polygon_count": 2,
            },
            "TAG": {
                "suggested_trim_left": None,
                "suggested_trim_right": None,
                "suggested_trim_top": None,
                "suggested_trim_bottom": None,
                "content_zone_detected": False,
                "content_zone_width": None,
                "content_zone_height": None,
                "polygon_count": 0,
                "filtered_polygon_count": 0,
            },
        },
        "all_block_definitions": {
            "VALVE": {
                "block_raw_name": "VALVE",
                "block_resolved_name": "VALVE",
                "block_insertion_status": "Inserted",
                "block_is_nested": False,
                "block_nested_parent_names": [],
                "block_entity_count": 8,
            },
            "PIPE": {
                "block_raw_name": "PIPE",
                "block_resolved_name": "PIPE",
                "block_insertion_status": "Inserted",
                "block_is_nested": True,
                "block_nested_parent_names": ["VALVE"],
                "block_entity_count": 12,
            },
            "TAG": {
                "block_raw_name": "TAG",
                "block_resolved_name": "TAG",
                "block_insertion_status": "Nested Only",
                "block_is_nested": True,
                "block_nested_parent_names": ["VALVE", "PIPE"],
                "block_entity_count": 4,
            },
            "*Model_Space": {
                "block_raw_name": "*Model_Space",
                "block_resolved_name": "*Model_Space",
                "block_insertion_status": "System",
                "block_is_nested": False,
                "block_nested_parent_names": [],
                "block_entity_count": 50,
            },
        },
        "nested_block_parents": {
            "PIPE": ["VALVE"],
            "TAG": ["PIPE", "VALVE"],
        },
        "block_attribute_data": {},
    }


@pytest.fixture
def annotation_extraction_data() -> ExtractionResult:
    """Provide sample extraction data with annotations."""
    return {
        "block_counts": {"VALVE": 5},
        "block_entities": {"VALVE": 8},
        "block_layer_pairs": {
            BlockLayerKey(block_name="VALVE", layer_name="Layer1"): 5
        },
        "block_rotation_counts": {
            BlockRotationKey(
                block_name="VALVE", layer_name="Layer1", rotation_category="0"
            ): 5
        },
        "block_scale_data": {"VALVE": {(1.0, 1.0)}},
        "block_xdata_apps": {},
        "layer_block_insertion_counts": {"Layer1": 5},
        "layer_entity_counts": {"Layer1": 25},
        "layer_unique_color_counts": {"Layer1": 2},
        "layer_annotation_counts": {"Layer1": 10},
        "annotation_data": {
            AnnotationKey(
                annotation_contents="Sample Text",
                annotation_type="TEXT",
                layer_name="Layer1",
                color_r=255,
                color_g=0,
                color_b=0,
            ): 3,
            AnnotationKey(
                annotation_contents="Another Text",
                annotation_type="MTEXT",
                layer_name="Layer2",
                color_r=0,
                color_g=255,
                color_b=0,
            ): 2,
            AnnotationKey(
                annotation_contents="Third Text",
                annotation_type="TEXT",
                layer_name="Layer1",
                color_r=0,
                color_g=0,
                color_b=255,
            ): 1,
        },
        "entity_type_counts": {"INSERT": 5, "LINE": 20},
        "color_analysis_data": [],
        "extraction_issues": [],
        "block_trimming_data": {
            "VALVE": {
                "native_width": 10.0,
                "native_height": 5.0,
                "vertical_segments": [10.0],
                "horizontal_segments": [5.0],
            }
        },
        "block_content_zone_data": {
            "VALVE": {
                "suggested_trim_left": 1.0,
                "suggested_trim_right": 1.0,
                "suggested_trim_top": 0.5,
                "suggested_trim_bottom": 0.5,
                "content_zone_detected": True,
                "content_zone_width": 8.0,
                "content_zone_height": 4.0,
                "polygon_count": 1,
                "filtered_polygon_count": 1,
            }
        },
        "all_block_definitions": {
            "VALVE": {
                "block_raw_name": "VALVE",
                "block_resolved_name": "VALVE",
                "block_insertion_status": "Inserted",
                "block_is_nested": False,
                "block_nested_parent_names": [],
                "block_entity_count": 8,
            },
        },
        "nested_block_parents": {},
        "block_attribute_data": {},
    }


@pytest.fixture
def color_analysis_data() -> ExtractionResult:
    """Provide sample extraction data with color analysis records."""
    return {
        "block_counts": {},
        "block_entities": {},
        "block_layer_pairs": {},
        "block_rotation_counts": {},
        "block_scale_data": {},
        "block_xdata_apps": {},
        "layer_block_insertion_counts": {"Layer1": 0},
        "layer_entity_counts": {"Layer1": 10},
        "layer_unique_color_counts": {"Layer1": 3},
        "layer_annotation_counts": {"Layer1": 2},
        "annotation_data": {},
        "entity_type_counts": {"LINE": 5, "TEXT": 2},
        "color_analysis_data": [
            {
                "annotation_contents": "",
                "layer_name": "Layer1",
                "color_r": 255,
                "color_g": 0,
                "color_b": 0,
                "color_aci": 1,
                "entity_type": "Lines",
                "entity_count": 3,
            },
            {
                "annotation_contents": "",
                "layer_name": "Layer1",
                "color_r": 255,
                "color_g": 255,
                "color_b": 0,
                "color_aci": 2,
                "entity_type": "Lines",
                "entity_count": 2,
            },
            {
                "annotation_contents": "Sample Text",
                "layer_name": "Layer1",
                "color_r": 124,
                "color_g": 82,
                "color_b": 165,
                "color_aci": None,  # True Color
                "entity_type": "TEXT",
                "entity_count": 1,
            },
            {
                "annotation_contents": "",
                "layer_name": "Layer1",
                "color_r": 255,
                "color_g": 255,
                "color_b": 255,
                "color_aci": 256,  # ByLayer
                "entity_type": "Lines",
                "entity_count": 1,
            },
        ],
        "extraction_issues": [],
        "block_trimming_data": {},
        "block_content_zone_data": {},
        "all_block_definitions": {
            "LINE_BLOCK": {
                "block_raw_name": "LINE_BLOCK",
                "block_resolved_name": "LINE_BLOCK",
                "block_insertion_status": "Unused",
                "block_is_nested": False,
                "block_nested_parent_names": [],
                "block_entity_count": 5,
            },
        },
        "nested_block_parents": {},
        "block_attribute_data": {},
    }


@pytest.fixture
def extraction_issues_data() -> ExtractionResult:
    """Provide sample extraction data with extraction issues."""
    return {
        "block_counts": {"VALVE": 10},
        "block_entities": {"VALVE": 8},
        "block_layer_pairs": {
            BlockLayerKey(block_name="VALVE", layer_name="Layer1"): 10,
        },
        "block_rotation_counts": {
            BlockRotationKey(
                block_name="VALVE", layer_name="Layer1", rotation_category="0"
            ): 10,
        },
        "block_scale_data": {"VALVE": {(1.0, 1.0)}},
        "block_xdata_apps": {},
        "layer_block_insertion_counts": {"Layer1": 10},
        "layer_entity_counts": {"Layer1": 15},
        "layer_unique_color_counts": {"Layer1": 1},
        "layer_annotation_counts": {"Layer1": 0},
        "annotation_data": {},
        "entity_type_counts": {"INSERT": 10},
        "color_analysis_data": [],
        "extraction_issues": [
            {
                "issue_type": "Unresolved Anonymous Block",
                "block_name": "*U1",
                "layer_name": "Layer1",
                "insertion_count": 5,
                "details": "No AcDbBlockRepBTag XDATA found",
            },
            {
                "issue_type": "Unresolved Anonymous Block",
                "block_name": "*U2",
                "layer_name": "Layer2",
                "insertion_count": 3,
                "details": "No AcDbBlockRepBTag XDATA found",
            },
        ],
        "block_trimming_data": {
            "VALVE": {
                "native_width": 100.0,
                "native_height": 50.0,
                "vertical_segments": [10.0, 80.0, 10.0],
                "horizontal_segments": [5.0, 40.0, 5.0],
            },
        },
        "block_content_zone_data": {
            "VALVE": {
                "suggested_trim_left": 10.0,
                "suggested_trim_right": 10.0,
                "suggested_trim_top": 5.0,
                "suggested_trim_bottom": 5.0,
                "content_zone_detected": True,
                "content_zone_width": 80.0,
                "content_zone_height": 40.0,
                "polygon_count": 2,
                "filtered_polygon_count": 2,
            },
        },
        "all_block_definitions": {
            "VALVE": {
                "block_raw_name": "VALVE",
                "block_resolved_name": "VALVE",
                "block_insertion_status": "Inserted",
                "block_is_nested": False,
                "block_nested_parent_names": [],
                "block_entity_count": 8,
            },
            "*U1": {
                "block_raw_name": "*U1",
                "block_resolved_name": "*U1",
                "block_insertion_status": "Unresolved (*U)",
                "block_is_nested": False,
                "block_nested_parent_names": [],
                "block_entity_count": 3,
            },
        },
        "nested_block_parents": {},
        "block_attribute_data": {},
    }


@pytest.fixture
def no_issues_data() -> ExtractionResult:
    """Provide sample extraction data with no extraction issues."""
    return {
        "block_counts": {"VALVE": 10},
        "block_entities": {"VALVE": 8},
        "block_layer_pairs": {
            BlockLayerKey(block_name="VALVE", layer_name="Layer1"): 10,
        },
        "block_rotation_counts": {
            BlockRotationKey(
                block_name="VALVE", layer_name="Layer1", rotation_category="0"
            ): 10,
        },
        "block_scale_data": {"VALVE": {(1.0, 1.0)}},
        "block_xdata_apps": {},
        "layer_block_insertion_counts": {"Layer1": 10},
        "layer_entity_counts": {"Layer1": 15},
        "layer_unique_color_counts": {"Layer1": 1},
        "layer_annotation_counts": {"Layer1": 0},
        "annotation_data": {},
        "entity_type_counts": {"INSERT": 10},
        "color_analysis_data": [],
        "extraction_issues": [],
        "block_trimming_data": {
            "VALVE": {
                "native_width": 100.0,
                "native_height": 50.0,
                "vertical_segments": [10.0, 80.0, 10.0],
                "horizontal_segments": [5.0, 40.0, 5.0],
            },
        },
        "block_content_zone_data": {
            "VALVE": {
                "suggested_trim_left": 10.0,
                "suggested_trim_right": 10.0,
                "suggested_trim_top": 5.0,
                "suggested_trim_bottom": 5.0,
                "content_zone_detected": True,
                "content_zone_width": 80.0,
                "content_zone_height": 40.0,
                "polygon_count": 2,
                "filtered_polygon_count": 2,
            },
        },
        "all_block_definitions": {
            "VALVE": {
                "block_raw_name": "VALVE",
                "block_resolved_name": "VALVE",
                "block_insertion_status": "Inserted",
                "block_is_nested": False,
                "block_nested_parent_names": [],
                "block_entity_count": 8,
            },
        },
        "nested_block_parents": {},
        "block_attribute_data": {},
    }
