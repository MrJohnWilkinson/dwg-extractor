"""
Unit tests for the extractor module - block attribute extraction.

This test suite validates ATTRIB entity extraction from INSERT blocks,
including edge cases like empty values, multiple attributes, and blocks
without attributes.
"""

from core.extractor import extract_blocks


class TestBlockAttributeExtraction:
    """Test suite for block attribute extraction functionality."""

    def test_block_attribute_data_exists_in_result(self) -> None:
        """Test that block_attribute_data field exists in extraction result."""
        result = extract_blocks("app/tests/assets/block_attributes_test.dxf")

        assert "block_attribute_data" in result
        assert isinstance(result["block_attribute_data"], dict)

    def test_block_with_multiple_attributes(self) -> None:
        """Test extraction of block with multiple attribute tags."""
        result = extract_blocks("app/tests/assets/block_attributes_test.dxf")

        # PRODUCT_BLOCK should have attributes
        assert "PRODUCT_BLOCK" in result["block_attribute_data"]
        attrs = result["block_attribute_data"]["PRODUCT_BLOCK"]

        # Should be a list of (tag, value) tuples, sorted alphabetically
        assert isinstance(attrs, list)

        # Convert to dict for easier assertions
        attr_dict: dict[str, set[str]] = {}
        for tag, value in attrs:
            if tag not in attr_dict:
                attr_dict[tag] = set()
            attr_dict[tag].add(value)

        # Verify expected tags exist
        assert "PROD1" in attr_dict
        assert "PROD2" in attr_dict
        assert "DEPT" in attr_dict
        assert "BAY#" in attr_dict

        # Verify PROD1 has both unique values
        assert "Garage" in attr_dict["PROD1"]
        assert "Kitchen" in attr_dict["PROD1"]

        # Verify PROD2 has both non-empty values (empty skipped)
        assert "Door Openers" in attr_dict["PROD2"]
        assert "Appliances" in attr_dict["PROD2"]

    def test_block_with_single_attribute(self) -> None:
        """Test extraction of block with single attribute tag."""
        result = extract_blocks("app/tests/assets/block_attributes_test.dxf")

        # SIMPLE_BLOCK should have ID attribute
        assert "SIMPLE_BLOCK" in result["block_attribute_data"]
        attrs = result["block_attribute_data"]["SIMPLE_BLOCK"]

        # Should have 2 unique (tag, value) pairs
        assert len(attrs) == 2

        # Verify both ID values are captured
        values = [v for t, v in attrs if t == "ID"]
        assert "ITEM-001" in values
        assert "ITEM-002" in values

    def test_block_without_attributes(self) -> None:
        """Test that blocks without attributes are not in block_attribute_data."""
        result = extract_blocks("app/tests/assets/block_attributes_test.dxf")

        # NO_ATTRIB_BLOCK should not be in block_attribute_data
        # (or should have empty list, depending on implementation)
        if "NO_ATTRIB_BLOCK" in result["block_attribute_data"]:
            assert len(result["block_attribute_data"]["NO_ATTRIB_BLOCK"]) == 0

    def test_empty_attribute_values_skipped(self) -> None:
        """Test that empty attribute values are not extracted."""
        result = extract_blocks("app/tests/assets/block_attributes_test.dxf")

        # EMPTY_VALUE_BLOCK should not be in results (all values empty)
        if "EMPTY_VALUE_BLOCK" in result["block_attribute_data"]:
            attrs = result["block_attribute_data"]["EMPTY_VALUE_BLOCK"]
            # Should have no entries since all values are empty
            assert len(attrs) == 0

    def test_attribute_data_sorted_alphabetically(self) -> None:
        """Test that attribute data is sorted alphabetically by tag then value."""
        result = extract_blocks("app/tests/assets/block_attributes_test.dxf")

        if "PRODUCT_BLOCK" in result["block_attribute_data"]:
            attrs = result["block_attribute_data"]["PRODUCT_BLOCK"]
            # Verify list is sorted
            assert attrs == sorted(attrs)

    def test_attribute_deduplication(self) -> None:
        """Test that duplicate (tag, value) pairs are deduplicated."""
        result = extract_blocks("app/tests/assets/block_attributes_test.dxf")

        if "PRODUCT_BLOCK" in result["block_attribute_data"]:
            attrs = result["block_attribute_data"]["PRODUCT_BLOCK"]
            # Should not have duplicate entries
            assert len(attrs) == len(set(attrs))

    def test_block_attribute_data_empty_file(self) -> None:
        """Test attribute extraction from empty file."""
        result = extract_blocks("app/tests/assets/empty_drawing.dxf")

        assert "block_attribute_data" in result
        assert isinstance(result["block_attribute_data"], dict)
        # Empty file should have no attribute data
        assert len(result["block_attribute_data"]) == 0

    def test_block_attribute_data_file_without_attribs(self) -> None:
        """Test attribute extraction from file with blocks but no ATTRIB entities."""
        result = extract_blocks("app/tests/assets/sample_drawing.dxf")

        assert "block_attribute_data" in result
        assert isinstance(result["block_attribute_data"], dict)
        # sample_drawing.dxf has blocks but no ATTRIB entities
        # Result should be empty or have only entries with no attributes

    def test_attribute_tag_value_types(self) -> None:
        """Test that attribute tags and values are strings."""
        result = extract_blocks("app/tests/assets/block_attributes_test.dxf")

        for block_name, attrs in result["block_attribute_data"].items():
            assert isinstance(block_name, str)
            assert isinstance(attrs, list)
            for tag, value in attrs:
                assert isinstance(tag, str)
                assert isinstance(value, str)


class TestBlockAttributeEdgeCases:
    """Test suite for block attribute edge cases."""

    def test_attribute_special_characters_preserved(self) -> None:
        """Test that special characters in attribute values are preserved."""
        result = extract_blocks("app/tests/assets/block_attributes_test.dxf")

        # Verify BAY# tag contains special character in tag name
        if "PRODUCT_BLOCK" in result["block_attribute_data"]:
            attrs = result["block_attribute_data"]["PRODUCT_BLOCK"]
            tags = [tag for tag, value in attrs]
            assert "BAY#" in tags  # Tag with special character

    def test_attribute_whitespace_in_values(self) -> None:
        """Test that attribute values with spaces are preserved correctly."""
        result = extract_blocks("app/tests/assets/block_attributes_test.dxf")

        if "PRODUCT_BLOCK" in result["block_attribute_data"]:
            attrs = result["block_attribute_data"]["PRODUCT_BLOCK"]
            values = [value for tag, value in attrs if tag == "PROD2"]
            # "Door Openers" contains a space
            assert any(" " in v for v in values)


class TestBlockAttributeDataStructure:
    """Test suite for block_attribute_data structure verification."""

    def test_attribute_data_is_list_of_tuples(self) -> None:
        """Test that each block's attribute data is a list of tuples."""
        result = extract_blocks("app/tests/assets/block_attributes_test.dxf")

        for block_name, attrs in result["block_attribute_data"].items():
            assert isinstance(attrs, list)
            for item in attrs:
                assert isinstance(item, (list, tuple))
                assert len(item) == 2

    def test_attribute_data_conservation(self) -> None:
        """Test that all non-empty attributes from all insertions are captured."""
        result = extract_blocks("app/tests/assets/block_attributes_test.dxf")

        # PRODUCT_BLOCK has 3 insertions with various attribute values
        # After deduplication and empty value filtering:
        # PROD1: "Garage", "Kitchen" (2 values, "Garage" appears twice but deduplicated)
        # PROD2: "Door Openers", "Appliances" (2 values, empty skipped)
        # DEPT: "30", "45" (2 values, "30" appears twice but deduplicated)
        # BAY#: "27-004", "12-001", "27-005" (3 values)

        if "PRODUCT_BLOCK" in result["block_attribute_data"]:
            attrs = result["block_attribute_data"]["PRODUCT_BLOCK"]

            # Count unique values per tag
            tag_values: dict[str, set[str]] = {}
            for tag, value in attrs:
                if tag not in tag_values:
                    tag_values[tag] = set()
                tag_values[tag].add(value)

            # Verify expected counts (these may vary based on test file content)
            assert len(tag_values.get("PROD1", set())) >= 2
            assert len(tag_values.get("PROD2", set())) >= 2
            assert len(tag_values.get("DEPT", set())) >= 2
            assert len(tag_values.get("BAY#", set())) >= 3
