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
from core.extractor import extract_blocks, ExtractionResult
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
