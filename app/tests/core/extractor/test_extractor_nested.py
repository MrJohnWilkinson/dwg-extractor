"""
Unit tests for nested block detection functionality in the extractor module.

Tests the following ExtractionResult fields:
- all_block_definitions: Complete BlockDefinitionRecord entries for every block
- nested_block_parents: Parent-child relationships between blocks

Uses the nested_block_test.dxf fixture which contains:
- OUTER_BLOCK: Contains INSERT refs to INNER_BLOCK and MULTI_PARENT_BLOCK (Inserted)
- INNER_BLOCK: Nested only in OUTER_BLOCK (Nested Only)
- STANDALONE_BLOCK: Inserted in modelspace, not nested (Inserted)
- UNUSED_BLOCK: Defined but never inserted anywhere (Unused)
- MULTI_PARENT_BLOCK: Nested in OUTER_BLOCK and SECOND_OUTER, also in modelspace (Inserted)
- SECOND_OUTER: Contains INSERT of MULTI_PARENT_BLOCK (Inserted)
"""

from typing import Generator

import pytest

from core.extractor import ExtractionResult, extract_blocks


class TestNestedBlockDetection:
    """Test suite for nested block detection functionality."""

    @pytest.fixture
    def nested_result(self) -> Generator[ExtractionResult, None, None]:
        """Extract blocks from nested_block_test.dxf fixture."""
        yield extract_blocks("app/tests/assets/nested_block_test.dxf")

    @pytest.fixture
    def empty_result(self) -> Generator[ExtractionResult, None, None]:
        """Extract blocks from empty_drawing.dxf fixture."""
        yield extract_blocks("app/tests/assets/empty_drawing.dxf")

    def test_extract_all_block_definitions_exists(
        self, nested_result: ExtractionResult
    ) -> None:
        """Test that all_block_definitions field exists in result."""
        assert "all_block_definitions" in nested_result
        assert isinstance(nested_result["all_block_definitions"], dict)

    def test_extract_nested_block_parents_exists(
        self, nested_result: ExtractionResult
    ) -> None:
        """Test that nested_block_parents field exists in result."""
        assert "nested_block_parents" in nested_result
        assert isinstance(nested_result["nested_block_parents"], dict)

    def test_all_block_definitions_contains_user_blocks(
        self, nested_result: ExtractionResult
    ) -> None:
        """Test that all user-defined blocks are tracked in all_block_definitions."""
        block_defs = nested_result["all_block_definitions"]

        # All 6 user-defined blocks should be present (by raw name)
        expected_blocks = {
            "OUTER_BLOCK",
            "INNER_BLOCK",
            "STANDALONE_BLOCK",
            "UNUSED_BLOCK",
            "MULTI_PARENT_BLOCK",
            "SECOND_OUTER",
        }

        for block_name in expected_blocks:
            assert block_name in block_defs, (
                f"Block {block_name} not found in all_block_definitions"
            )

    def test_all_block_definitions_contains_system_blocks(
        self, nested_result: ExtractionResult
    ) -> None:
        """Test that system blocks are also tracked in all_block_definitions."""
        block_defs = nested_result["all_block_definitions"]

        # System blocks should be present
        assert "*Model_Space" in block_defs
        assert "*Paper_Space" in block_defs

    def test_block_definition_record_structure(
        self, nested_result: ExtractionResult
    ) -> None:
        """Test that each BlockDefinitionRecord has the correct structure."""
        block_defs = nested_result["all_block_definitions"]

        for raw_name, record in block_defs.items():
            # Verify all required fields are present
            assert "block_raw_name" in record
            assert "block_resolved_name" in record
            assert "block_insertion_status" in record
            assert "block_is_nested" in record
            assert "block_nested_parent_names" in record
            assert "block_entity_count" in record

            # Verify types
            assert isinstance(record["block_raw_name"], str)
            assert isinstance(record["block_resolved_name"], str)
            assert isinstance(record["block_insertion_status"], str)
            assert isinstance(record["block_is_nested"], bool)
            assert isinstance(record["block_nested_parent_names"], list)
            assert isinstance(record["block_entity_count"], int)

            # raw_name in record should match the key
            assert record["block_raw_name"] == raw_name

    def test_nested_block_insertion_status_inserted(
        self, nested_result: ExtractionResult
    ) -> None:
        """Test insertion status for blocks with modelspace insertions."""
        block_defs = nested_result["all_block_definitions"]

        # These blocks are inserted in modelspace
        assert block_defs["OUTER_BLOCK"]["block_insertion_status"] == "Inserted"
        assert block_defs["STANDALONE_BLOCK"]["block_insertion_status"] == "Inserted"
        assert block_defs["SECOND_OUTER"]["block_insertion_status"] == "Inserted"
        assert block_defs["MULTI_PARENT_BLOCK"]["block_insertion_status"] == "Inserted"

    def test_nested_block_insertion_status_nested_only(
        self, nested_result: ExtractionResult
    ) -> None:
        """Test insertion status for blocks only nested in other blocks."""
        block_defs = nested_result["all_block_definitions"]

        # INNER_BLOCK is only nested in OUTER_BLOCK, not in modelspace
        assert block_defs["INNER_BLOCK"]["block_insertion_status"] == "Nested Only"

    def test_nested_block_insertion_status_unused(
        self, nested_result: ExtractionResult
    ) -> None:
        """Test insertion status for blocks never inserted anywhere."""
        block_defs = nested_result["all_block_definitions"]

        # UNUSED_BLOCK is defined but never inserted
        assert block_defs["UNUSED_BLOCK"]["block_insertion_status"] == "Unused"

    def test_nested_block_insertion_status_system(
        self, nested_result: ExtractionResult
    ) -> None:
        """Test insertion status for system blocks."""
        block_defs = nested_result["all_block_definitions"]

        # System blocks should be classified as "System"
        assert block_defs["*Model_Space"]["block_insertion_status"] == "System"
        assert block_defs["*Paper_Space"]["block_insertion_status"] == "System"

    def test_nested_block_is_nested_flag(
        self, nested_result: ExtractionResult
    ) -> None:
        """Test block_is_nested flag accuracy."""
        block_defs = nested_result["all_block_definitions"]

        # Blocks that are nested in other blocks
        assert block_defs["INNER_BLOCK"]["block_is_nested"] is True
        assert block_defs["MULTI_PARENT_BLOCK"]["block_is_nested"] is True

        # Blocks that are NOT nested in other blocks
        assert block_defs["OUTER_BLOCK"]["block_is_nested"] is False
        assert block_defs["STANDALONE_BLOCK"]["block_is_nested"] is False
        assert block_defs["UNUSED_BLOCK"]["block_is_nested"] is False
        assert block_defs["SECOND_OUTER"]["block_is_nested"] is False

    def test_nested_block_parent_names(
        self, nested_result: ExtractionResult
    ) -> None:
        """Test block_nested_parent_names lists."""
        block_defs = nested_result["all_block_definitions"]

        # INNER_BLOCK is nested only in OUTER_BLOCK
        assert block_defs["INNER_BLOCK"]["block_nested_parent_names"] == ["OUTER_BLOCK"]

        # Blocks not nested anywhere should have empty list
        assert block_defs["OUTER_BLOCK"]["block_nested_parent_names"] == []
        assert block_defs["STANDALONE_BLOCK"]["block_nested_parent_names"] == []
        assert block_defs["UNUSED_BLOCK"]["block_nested_parent_names"] == []
        assert block_defs["SECOND_OUTER"]["block_nested_parent_names"] == []

    def test_nested_block_multi_parent(
        self, nested_result: ExtractionResult
    ) -> None:
        """Test blocks nested in multiple parents."""
        block_defs = nested_result["all_block_definitions"]

        # MULTI_PARENT_BLOCK is nested in both OUTER_BLOCK and SECOND_OUTER
        parent_names = block_defs["MULTI_PARENT_BLOCK"]["block_nested_parent_names"]
        assert len(parent_names) == 2
        assert "OUTER_BLOCK" in parent_names
        assert "SECOND_OUTER" in parent_names
        # Should be sorted alphabetically
        assert parent_names == sorted(parent_names)

    def test_nested_block_entity_counts(
        self, nested_result: ExtractionResult
    ) -> None:
        """Test entity count accuracy in block definitions."""
        block_defs = nested_result["all_block_definitions"]

        # From create_nested_block_test.py:
        # OUTER_BLOCK: 4 entities (1 polyline + 3 block refs)
        # INNER_BLOCK: 2 entities (1 polyline + 1 circle)
        # STANDALONE_BLOCK: 3 entities (1 polyline + 2 lines)
        # UNUSED_BLOCK: 2 entities (1 circle + 1 text)
        # MULTI_PARENT_BLOCK: 2 entities (1 polyline + 1 line)
        # SECOND_OUTER: 2 entities (1 polyline + 1 block ref)

        assert block_defs["OUTER_BLOCK"]["block_entity_count"] == 4
        assert block_defs["INNER_BLOCK"]["block_entity_count"] == 2
        assert block_defs["STANDALONE_BLOCK"]["block_entity_count"] == 3
        assert block_defs["UNUSED_BLOCK"]["block_entity_count"] == 2
        assert block_defs["MULTI_PARENT_BLOCK"]["block_entity_count"] == 2
        assert block_defs["SECOND_OUTER"]["block_entity_count"] == 2

    def test_nested_block_parents_dict_structure(
        self, nested_result: ExtractionResult
    ) -> None:
        """Test nested_block_parents dictionary structure."""
        nested_parents = nested_result["nested_block_parents"]

        # Should be a dict with string keys and list values
        for child_name, parent_list in nested_parents.items():
            assert isinstance(child_name, str)
            assert isinstance(parent_list, list)
            for parent in parent_list:
                assert isinstance(parent, str)

    def test_nested_block_parents_content(
        self, nested_result: ExtractionResult
    ) -> None:
        """Test nested_block_parents contains correct relationships."""
        nested_parents = nested_result["nested_block_parents"]

        # INNER_BLOCK should have OUTER_BLOCK as parent
        assert "INNER_BLOCK" in nested_parents
        assert nested_parents["INNER_BLOCK"] == ["OUTER_BLOCK"]

        # MULTI_PARENT_BLOCK should have both parents
        assert "MULTI_PARENT_BLOCK" in nested_parents
        assert sorted(nested_parents["MULTI_PARENT_BLOCK"]) == [
            "OUTER_BLOCK",
            "SECOND_OUTER",
        ]

        # Blocks not nested should not be in nested_parents
        assert "OUTER_BLOCK" not in nested_parents
        assert "STANDALONE_BLOCK" not in nested_parents
        assert "UNUSED_BLOCK" not in nested_parents
        assert "SECOND_OUTER" not in nested_parents

    def test_nested_block_empty_file(self, empty_result: ExtractionResult) -> None:
        """Test nested block fields for empty file."""
        # all_block_definitions should exist but only have system blocks
        assert "all_block_definitions" in empty_result
        assert isinstance(empty_result["all_block_definitions"], dict)

        # Should have at least Model_Space and Paper_Space
        block_defs = empty_result["all_block_definitions"]
        assert "*Model_Space" in block_defs
        assert "*Paper_Space" in block_defs

        # nested_block_parents should be empty (no nested blocks)
        assert "nested_block_parents" in empty_result
        assert isinstance(empty_result["nested_block_parents"], dict)
        # Empty file has no user blocks, so no nesting relationships
        assert len(empty_result["nested_block_parents"]) == 0

    def test_nested_block_resolved_names(
        self, nested_result: ExtractionResult
    ) -> None:
        """Test that resolved names match raw names for non-anonymous blocks."""
        block_defs = nested_result["all_block_definitions"]

        # For regular (non-anonymous) blocks, raw name should equal resolved name
        regular_blocks = [
            "OUTER_BLOCK",
            "INNER_BLOCK",
            "STANDALONE_BLOCK",
            "UNUSED_BLOCK",
            "MULTI_PARENT_BLOCK",
            "SECOND_OUTER",
        ]

        for block_name in regular_blocks:
            record = block_defs[block_name]
            assert record["block_raw_name"] == record["block_resolved_name"]

    def test_insertion_status_values_are_valid(
        self, nested_result: ExtractionResult
    ) -> None:
        """Test that all insertion status values are from the expected set."""
        block_defs = nested_result["all_block_definitions"]

        valid_statuses = {
            "Inserted",
            "Nested Only",
            "Unused",
            "System",
            "System (Dimension)",
            "System (Hatch)",
            "Unresolved (*U)",
            "Unresolved (A$C)",
        }

        for raw_name, record in block_defs.items():
            status = record["block_insertion_status"]
            assert status in valid_statuses, (
                f"Block {raw_name} has invalid status: {status}"
            )


class TestNestedBlockWithSampleFile:
    """Additional tests using sample_drawing.dxf for broader coverage."""

    @pytest.fixture
    def sample_result(self) -> Generator[ExtractionResult, None, None]:
        """Extract blocks from sample_drawing.dxf fixture."""
        yield extract_blocks("app/tests/assets/sample_drawing.dxf")

    def test_sample_file_has_all_block_definitions(
        self, sample_result: ExtractionResult
    ) -> None:
        """Test that sample file extraction includes all_block_definitions."""
        assert "all_block_definitions" in sample_result
        assert isinstance(sample_result["all_block_definitions"], dict)
        # Sample file has blocks, so should have more than just system blocks
        assert len(sample_result["all_block_definitions"]) >= 3  # System + user blocks

    def test_sample_file_has_nested_block_parents(
        self, sample_result: ExtractionResult
    ) -> None:
        """Test that sample file extraction includes nested_block_parents."""
        assert "nested_block_parents" in sample_result
        assert isinstance(sample_result["nested_block_parents"], dict)
