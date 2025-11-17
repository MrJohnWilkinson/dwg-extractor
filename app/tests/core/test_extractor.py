"""
Unit tests for the extractor module.

This test suite validates the DWG/DXF extraction functionality including:
- Valid file processing with known block counts
- Empty file handling (no blocks)
- Invalid/corrupted file error handling
- Missing file error handling
- Count accuracy verification
- Return type validation
"""

import pytest
from pathlib import Path
from core.extractor import extract_blocks, ExtractionResult, _categorize_rotation
import ezdxf


class TestExtractor:
    """Test suite for the extract_blocks function."""

    def test_extract_valid_file(self) -> None:
        """Test extraction from valid DXF file with known block counts."""
        result = extract_blocks('app/tests/assets/sample_drawing.dxf')

        # Verify result is an ExtractionResult dict
        assert isinstance(result, dict)
        assert 'block_counts' in result
        assert 'block_entities' in result
        assert 'block_layer_pairs' in result
        assert 'layer_insertion_counts' in result
        assert 'layer_entity_counts' in result
        assert 'entity_type_counts' in result

        # Verify we have exactly 3 block types
        assert len(result['block_counts']) == 3

        # Verify correct counts for each block type
        assert result['block_counts']['VALVE_GATE'] == 10
        assert result['block_counts']['PIPE_SUPPORT'] == 5
        assert result['block_counts']['EQUIPMENT_TAG'] == 3

    def test_extract_empty_file(self) -> None:
        """Test extraction from valid DXF file with no blocks."""
        result = extract_blocks('app/tests/assets/empty_drawing.dxf')

        # Verify result has all required keys with empty dicts
        assert isinstance(result, dict)
        assert result['block_counts'] == {}
        assert isinstance(result['block_entities'], dict)
        assert result['block_layer_pairs'] == {}
        assert isinstance(result['layer_insertion_counts'], dict)
        assert isinstance(result['layer_entity_counts'], dict)
        assert isinstance(result['entity_type_counts'], dict)

    def test_extract_invalid_file(self) -> None:
        """Test that invalid/corrupted files raise ValueError."""
        with pytest.raises(ValueError, match="Invalid or corrupted"):
            extract_blocks('app/tests/assets/invalid.dxf')

    def test_extract_missing_file(self) -> None:
        """Test that missing files raise FileNotFoundError."""
        with pytest.raises(FileNotFoundError, match="File not found"):
            extract_blocks('app/tests/assets/nonexistent.dxf')

    def test_extract_counts_accuracy(self) -> None:
        """Test that total count is accurate."""
        result = extract_blocks('app/tests/assets/sample_drawing.dxf')

        # Total count should be 10 + 5 + 3 = 18
        total_count = sum(result['block_counts'].values())
        assert total_count == 18

        # All counts should be positive integers
        for count in result['block_counts'].values():
            assert isinstance(count, int)
            assert count > 0

    def test_extract_returns_dict(self) -> None:
        """Test that return value has correct types."""
        result = extract_blocks('app/tests/assets/sample_drawing.dxf')

        # Verify return type is dict with correct keys
        assert isinstance(result, dict)
        assert 'block_counts' in result
        assert 'block_entities' in result
        assert 'block_layer_pairs' in result
        assert 'layer_insertion_counts' in result
        assert 'layer_entity_counts' in result
        assert 'entity_type_counts' in result

        # Verify all block count keys are strings and values are integers
        for key, value in result['block_counts'].items():
            assert isinstance(key, str)
            assert isinstance(value, int)

    def test_extract_unsupported_extension(self) -> None:
        """Test that unsupported file extensions raise ValueError."""
        # Create a temporary file with wrong extension
        temp_file = Path('app/tests/assets/test.txt')
        temp_file.write_text('test')

        try:
            with pytest.raises(ValueError, match="Unsupported file extension"):
                extract_blocks(str(temp_file))
        finally:
            # Clean up
            if temp_file.exists():
                temp_file.unlink()

    def test_extract_block_entities(self) -> None:
        """Test that block definition entity counts are extracted."""
        result = extract_blocks('app/tests/assets/sample_drawing.dxf')

        # Verify block_entities contains data for each block type
        assert len(result['block_entities']) >= len(result['block_counts'])

        # All values should be non-negative integers
        for entity_count in result['block_entities'].values():
            assert isinstance(entity_count, int)
            assert entity_count >= 0

    def test_extract_layer_metrics(self) -> None:
        """Test that layer-based metrics are extracted."""
        result = extract_blocks('app/tests/assets/sample_drawing.dxf')

        # Verify layer data is present
        assert isinstance(result['layer_insertion_counts'], dict)
        assert isinstance(result['layer_entity_counts'], dict)

        # Should have at least one layer (layer "0" is default)
        assert len(result['layer_entity_counts']) > 0

        # All layer entity counts should be positive
        for count in result['layer_entity_counts'].values():
            assert isinstance(count, int)
            assert count > 0

    def test_extract_entity_types(self) -> None:
        """Test that global entity type counts are extracted."""
        result = extract_blocks('app/tests/assets/sample_drawing.dxf')

        # Verify entity_type_counts contains data
        assert len(result['entity_type_counts']) > 0

        # Should at least have INSERT entities (since we have blocks)
        assert 'INSERT' in result['entity_type_counts']
        assert result['entity_type_counts']['INSERT'] == 18  # 10 + 5 + 3

        # All values should be positive integers
        for count in result['entity_type_counts'].values():
            assert isinstance(count, int)
            assert count > 0

    @pytest.mark.skip(reason="ezdxf.readfile() does not support DWG files directly - requires ODA File Converter or ezdxf.recover")
    def test_extract_real_dwg_file(self) -> None:
        """Test extraction from a real DWG file."""
        # Note: ezdxf.readfile() cannot read DWG files directly
        # DWG support requires ODA File Converter or ezdxf.recover module
        # This test is skipped as it's beyond the scope of Phase 2
        result = extract_blocks('app/tests/assets/Supermarket-2020.dwg')

        # Verify we get an ExtractionResult
        assert isinstance(result, dict)
        assert 'block_counts' in result

        # Verify all block names are strings and counts are positive integers
        for block_name, count in result['block_counts'].items():
            assert isinstance(block_name, str)
            assert isinstance(count, int)
            assert count > 0

    def test_extract_block_layer_pairs(self) -> None:
        """Test that block-layer pairs are extracted correctly."""
        result = extract_blocks('app/tests/assets/sample_drawing.dxf')

        # Verify block_layer_pairs is present in result
        assert 'block_layer_pairs' in result
        assert isinstance(result['block_layer_pairs'], dict)

        # Verify block_layer_pairs has at least one entry
        assert len(result['block_layer_pairs']) > 0

        # Verify all keys are tuples of (str, str) and values are positive integers
        for pair_key, count in result['block_layer_pairs'].items():
            assert isinstance(pair_key, tuple)
            assert len(pair_key) == 2
            assert isinstance(pair_key[0], str)  # block_name
            assert isinstance(pair_key[1], str)  # layer_name
            assert isinstance(count, int)
            assert count > 0

    def test_block_layer_pairs_conservation(self) -> None:
        """Test that sum of block_layer_pairs equals sum of block_counts."""
        result = extract_blocks('app/tests/assets/sample_drawing.dxf')

        # Sum of all block_layer_pairs should equal sum of all block_counts
        total_pair_count = sum(result['block_layer_pairs'].values())
        total_block_count = sum(result['block_counts'].values())

        assert total_pair_count == total_block_count
        assert total_pair_count == 18  # Known count from sample_drawing.dxf

    def test_block_layer_pairs_tuple_keys(self) -> None:
        """Test that all block_layer_pairs keys are (str, str) tuples."""
        result = extract_blocks('app/tests/assets/sample_drawing.dxf')

        for pair_key in result['block_layer_pairs'].keys():
            # Verify key is a tuple
            assert isinstance(pair_key, tuple)
            # Verify tuple has exactly 2 elements
            assert len(pair_key) == 2
            # Verify both elements are strings
            block_name, layer_name = pair_key
            assert isinstance(block_name, str)
            assert isinstance(layer_name, str)
            # Verify neither is empty
            assert len(block_name) > 0
            assert len(layer_name) > 0

    def test_block_layer_pairs_empty_file(self) -> None:
        """Test that empty file returns empty block_layer_pairs dict."""
        result = extract_blocks('app/tests/assets/empty_drawing.dxf')

        # Verify block_layer_pairs is an empty dict
        assert isinstance(result['block_layer_pairs'], dict)
        assert len(result['block_layer_pairs']) == 0
        assert result['block_layer_pairs'] == {}

    def test_categorize_rotation_standard_angles(self) -> None:
        """Test rotation categorization for exact standard angles."""
        assert _categorize_rotation(0.0) == '0'
        assert _categorize_rotation(90.0) == '90'
        assert _categorize_rotation(180.0) == '180'
        assert _categorize_rotation(270.0) == '270'

    def test_categorize_rotation_tolerance(self) -> None:
        """Test rotation categorization with ±1° tolerance."""
        # Test angles within ±1° of standard angles
        assert _categorize_rotation(0.5) == '0'
        assert _categorize_rotation(89.5) == '90'
        assert _categorize_rotation(90.5) == '90'
        assert _categorize_rotation(179.5) == '180'
        assert _categorize_rotation(180.5) == '180'
        assert _categorize_rotation(269.5) == '270'
        assert _categorize_rotation(270.5) == '270'
        assert _categorize_rotation(359.5) == '0'

    def test_categorize_rotation_non_standard(self) -> None:
        """Test rotation categorization for non-standard angles."""
        assert _categorize_rotation(45.0) == 'other'
        assert _categorize_rotation(135.0) == 'other'
        assert _categorize_rotation(225.0) == 'other'
        assert _categorize_rotation(315.0) == 'other'
        assert _categorize_rotation(30.0) == 'other'
        assert _categorize_rotation(60.0) == 'other'

    def test_categorize_rotation_normalization(self) -> None:
        """Test rotation normalization for negative and >360° angles."""
        # Negative angles should normalize correctly
        assert _categorize_rotation(-90.0) == '270'
        assert _categorize_rotation(-180.0) == '180'
        assert _categorize_rotation(-270.0) == '90'

        # Angles > 360 should normalize correctly
        assert _categorize_rotation(450.0) == '90'
        assert _categorize_rotation(540.0) == '180'
        assert _categorize_rotation(630.0) == '270'

    def test_categorize_rotation_boundary_cases(self) -> None:
        """Test rotation categorization for boundary edge cases."""
        # Angles just outside tolerance should be 'other'
        assert _categorize_rotation(1.5) == 'other'
        assert _categorize_rotation(88.0) == 'other'
        assert _categorize_rotation(92.0) == 'other'
        assert _categorize_rotation(178.0) == 'other'
        assert _categorize_rotation(182.0) == 'other'

    def test_extract_block_rotation_counts(self) -> None:
        """Test that block_rotation_counts field exists and contains correct structure."""
        result = extract_blocks('app/tests/assets/sample_drawing.dxf')

        # Verify block_rotation_counts is present
        assert 'block_rotation_counts' in result
        assert isinstance(result['block_rotation_counts'], dict)

        # Should have at least one entry for files with blocks
        assert len(result['block_rotation_counts']) > 0

    def test_block_rotation_counts_tuple_keys(self) -> None:
        """Test that all block_rotation_counts keys are (str, str, str) tuples."""
        result = extract_blocks('app/tests/assets/test_rotations.dxf')

        # Verify all keys are 3-element tuples
        for rotation_key in result['block_rotation_counts'].keys():
            assert isinstance(rotation_key, tuple)
            assert len(rotation_key) == 3
            block_name, layer_name, rotation_category = rotation_key
            assert isinstance(block_name, str)
            assert isinstance(layer_name, str)
            assert isinstance(rotation_category, str)
            assert len(block_name) > 0
            assert len(layer_name) > 0

    def test_block_rotation_counts_valid_categories(self) -> None:
        """Test that rotation categories are only valid values."""
        result = extract_blocks('app/tests/assets/test_rotations.dxf')

        valid_categories = {'0', '90', '180', '270', 'other'}

        for rotation_key in result['block_rotation_counts'].keys():
            _, _, rotation_category = rotation_key
            assert rotation_category in valid_categories

    def test_block_rotation_counts_conservation(self) -> None:
        """Test that sum of rotation counts equals sum of block_layer_pairs."""
        result = extract_blocks('app/tests/assets/test_rotations.dxf')

        # Sum of all rotation counts should equal sum of block_layer_pairs
        total_rotation_count = sum(result['block_rotation_counts'].values())
        total_pair_count = sum(result['block_layer_pairs'].values())

        assert total_rotation_count == total_pair_count

    def test_block_rotation_counts_with_fixture(self) -> None:
        """Test rotation extraction with test_rotations.dxf fixture with known counts."""
        result = extract_blocks('app/tests/assets/test_rotations.dxf')

        # Expected counts from the fixture:
        # 5 blocks at 0° on LAYER_A
        # 3 blocks at 90° on LAYER_A
        # 2 blocks at 180° on LAYER_B
        # 1 block at 270° on LAYER_B
        # 2 blocks at non-standard angles (45°, 135°) on LAYER_C

        # Verify specific rotation counts
        assert result['block_rotation_counts'][('TEST_BLOCK', 'LAYER_A', '0')] == 5
        assert result['block_rotation_counts'][('TEST_BLOCK', 'LAYER_A', '90')] == 3
        assert result['block_rotation_counts'][('TEST_BLOCK', 'LAYER_B', '180')] == 2
        assert result['block_rotation_counts'][('TEST_BLOCK', 'LAYER_B', '270')] == 1
        assert result['block_rotation_counts'][('TEST_BLOCK', 'LAYER_C', 'other')] == 2

        # Verify total count
        total = sum(result['block_rotation_counts'].values())
        assert total == 13  # 5 + 3 + 2 + 1 + 2
