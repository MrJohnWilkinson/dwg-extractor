"""
Unit tests for the excel_formatting module - header formatting.
"""

from core.excel_formatting import format_header


class TestFormatHeader:
    """Test suite for format_header function."""

    def test_format_header_basic(self) -> None:
        """Test simple snake_case conversion."""
        assert format_header("block_name") == "Block Name"

    def test_format_header_multiple_words(self) -> None:
        """Test longer field names."""
        assert (
            format_header("layer_block_insertion_count")
            == "Layer Block Insertion Count"
        )

    def test_format_header_single_word(self) -> None:
        """Test single word."""
        assert format_header("count") == "Count"

    def test_format_header_with_numbers(self) -> None:
        """Test with numbers."""
        assert format_header("rotation_0") == "Rotation 0"
        assert format_header("block_rotation_90") == "Block Rotation 90"
        assert format_header("block_rotation_180") == "Block Rotation 180"

    def test_format_header_empty_string(self) -> None:
        """Test empty string."""
        assert format_header("") == ""

    def test_format_header_no_underscores(self) -> None:
        """Test string without underscores."""
        assert format_header("name") == "Name"

    def test_format_header_acronym_dwg(self) -> None:
        """Test DWG acronym override."""
        assert format_header("dwg_file_name") == "DWG File Name"

    def test_format_header_acronym_dxf(self) -> None:
        """Test DXF acronym override."""
        assert format_header("dxf_version") == "DXF Version"

    def test_format_header_acronym_cad(self) -> None:
        """Test CAD acronym override."""
        assert format_header("cad_entity_type") == "CAD Entity Type"

    def test_format_header_acronym_id(self) -> None:
        """Test ID acronym override."""
        assert format_header("block_id") == "Block ID"

    def test_format_header_entity_type_count(self) -> None:
        """Test entity_type_count conversion."""
        assert format_header("entity_type_count") == "Entity Type Count"

    def test_format_header_block_insertion_count(self) -> None:
        """Test block_insertion_count conversion."""
        assert format_header("block_insertion_count") == "Block Insertion Count"
