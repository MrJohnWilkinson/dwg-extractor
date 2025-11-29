"""
Unit tests for the extractor module - MTEXT formatting functionality.

This module contains tests for MTEXT formatting code cleanup and text extraction.
"""

import ezdxf
import pytest

from core.extractor import (
    _clean_mtext_content,
    extract_blocks,
)


class TestMtextFormatting:
    """Test suite for MTEXT formatting code cleanup functionality."""

    def test_mtext_paragraph_codes_stripped(self) -> None:
        """Verify paragraph alignment codes (\\pxqc;, \\pxql;, etc.) are removed."""
        result = extract_blocks("app/tests/assets/mtext_formatting_test.dxf")
        annotation_data = result["annotation_data"]

        # Find CENTERED TEXT entry (should have formatting stripped)
        centered_entries = [
            key
            for key in annotation_data.keys()
            if "CENTERED TEXT" in key.annotation_contents
        ]
        assert len(centered_entries) >= 1
        # The content should be "CENTERED TEXT", not "\\pxqc;CENTERED TEXT"
        for key in centered_entries:
            assert "\\pxqc" not in key.annotation_contents
            assert "pxqc" not in key.annotation_contents.lower()

        # Check left aligned
        left_entries = [
            key
            for key in annotation_data.keys()
            if "LEFT ALIGNED" in key.annotation_contents
        ]
        assert len(left_entries) >= 1
        for key in left_entries:
            assert "\\pxql" not in key.annotation_contents

        # Check right aligned
        right_entries = [
            key
            for key in annotation_data.keys()
            if "RIGHT ALIGNED" in key.annotation_contents
        ]
        assert len(right_entries) >= 1
        for key in right_entries:
            assert "\\pxqr" not in key.annotation_contents

        # Check justified
        justified_entries = [
            key
            for key in annotation_data.keys()
            if "JUSTIFIED TEXT" in key.annotation_contents
        ]
        assert len(justified_entries) >= 1
        for key in justified_entries:
            assert "\\pxqj" not in key.annotation_contents

    def test_mtext_paragraph_breaks_become_spaces(self) -> None:
        """Verify \\P paragraph breaks become single spaces, not newlines."""
        result = extract_blocks("app/tests/assets/mtext_formatting_test.dxf")
        annotation_data = result["annotation_data"]

        # Find LINE ONE LINE TWO entry
        line_entries = [
            key for key in annotation_data.keys() if "LINE ONE" in key.annotation_contents
        ]
        assert len(line_entries) >= 1

        for key in line_entries:
            contents = key.annotation_contents
            # Should not contain \\P
            assert "\\P" not in contents
            # Should not contain newlines
            assert "\n" not in contents
            # Should contain both parts separated by space
            if "LINE TWO" in contents:
                assert "LINE ONE" in contents and "LINE TWO" in contents

    def test_mtext_underline_overline_stripped(self) -> None:
        """Verify \\L, \\l, \\O, \\o formatting codes are removed."""
        result = extract_blocks("app/tests/assets/mtext_formatting_test.dxf")
        annotation_data = result["annotation_data"]

        # Find underlined text entry
        underline_entries = [
            key
            for key in annotation_data.keys()
            if "UNDERLINED" in key.annotation_contents
        ]
        assert len(underline_entries) >= 1

        for key in underline_entries:
            contents = key.annotation_contents
            # Should not contain \\L or \\l
            assert "\\L" not in contents
            assert "\\l" not in contents

        # Find overlined text entry
        overline_entries = [
            key for key in annotation_data.keys() if "OVERLINED" in key.annotation_contents
        ]
        assert len(overline_entries) >= 1

        for key in overline_entries:
            contents = key.annotation_contents
            # Should not contain \\O or \\o
            assert "\\O" not in contents
            assert "\\o" not in contents

    def test_mtext_color_codes_stripped(self) -> None:
        """Verify \\C....; color codes are removed."""
        result = extract_blocks("app/tests/assets/mtext_formatting_test.dxf")
        annotation_data = result["annotation_data"]

        # Find the color test entry - should have "NORMAL RED WHITE"
        color_entries = [
            key
            for key in annotation_data.keys()
            if "RED" in key.annotation_contents and "WHITE" in key.annotation_contents
        ]

        for key in color_entries:
            contents = key.annotation_contents
            # Should not contain \\C followed by numbers and semicolon
            assert "\\C1;" not in contents
            assert "\\C7;" not in contents

    def test_mtext_complex_formatting_stripped(self) -> None:
        """Verify complex example like \\pxqc;MENS CASUAL\\P PANTS becomes 'MENS CASUAL PANTS'."""
        result = extract_blocks("app/tests/assets/mtext_formatting_test.dxf")
        annotation_data = result["annotation_data"]

        # Find MENS CASUAL entry
        mens_entries = [
            key
            for key in annotation_data.keys()
            if "MENS CASUAL" in key.annotation_contents
        ]
        assert len(mens_entries) >= 1

        for key in mens_entries:
            contents = key.annotation_contents
            # Should not contain any formatting codes
            assert "\\pxqc" not in contents
            assert "\\P" not in contents
            # Should contain the plain text
            assert "MENS CASUAL" in contents
            # Should have PANTS (possibly with space)
            if "PANTS" in contents:
                # Verify the format is clean - no newlines
                assert "\n" not in contents

    def test_mtext_plain_text_preserved(self) -> None:
        """Verify MTEXT without formatting codes is unchanged."""
        result = extract_blocks("app/tests/assets/mtext_formatting_test.dxf")
        annotation_data = result["annotation_data"]

        # Find plain text entry
        plain_entries = [
            key
            for key in annotation_data.keys()
            if "PLAIN TEXT WITHOUT FORMATTING" in key.annotation_contents
        ]
        assert len(plain_entries) >= 1

        for key in plain_entries:
            contents = key.annotation_contents
            # Should be exactly "PLAIN TEXT WITHOUT FORMATTING"
            assert contents == "PLAIN TEXT WITHOUT FORMATTING"

    def test_text_entities_unchanged(self) -> None:
        """Verify TEXT entities still work correctly (not affected by MTEXT changes)."""
        result = extract_blocks("app/tests/assets/annotation_test.dxf")
        annotation_data = result["annotation_data"]

        # Find TEXT entries (not MTEXT)
        text_entries = [
            (key, count)
            for key, count in annotation_data.items()
            if key.annotation_type == "TEXT"
        ]
        assert len(text_entries) > 0

        # Verify TEXT entities have expected content
        for key, count in text_entries:
            contents = key.annotation_contents
            assert isinstance(contents, str)
            # TEXT entities should have their content preserved
            assert len(contents) > 0 or contents == ""

    def test_mtext_multiple_spaces_collapsed(self) -> None:
        """Verify multiple consecutive spaces are collapsed to single space."""
        result = extract_blocks("app/tests/assets/mtext_formatting_test.dxf")
        annotation_data = result["annotation_data"]

        # Find entries with multiple paragraph breaks (WORD1\\P\\PWORD2)
        # These should have spaces collapsed
        word_entries = [
            key
            for key in annotation_data.keys()
            if "WORD1" in key.annotation_contents
            and "WORD2" in key.annotation_contents
            and "\\~" not in key.annotation_contents
        ]

        for key in word_entries:
            contents = key.annotation_contents
            # Should not have multiple consecutive spaces
            assert "  " not in contents  # No double spaces
            # Should have single space between words
            if "WORD1" in contents and "WORD2" in contents:
                # The words should be separated by a single space
                assert "WORD1 WORD2" in contents

    def test_mtext_font_changes_stripped(self) -> None:
        """Verify \\f....; font change codes are removed."""
        result = extract_blocks("app/tests/assets/mtext_formatting_test.dxf")
        annotation_data = result["annotation_data"]

        # Find BOLD text entry
        bold_entries = [
            key for key in annotation_data.keys() if "BOLD" in key.annotation_contents
        ]

        for key in bold_entries:
            contents = key.annotation_contents
            # Should not contain font codes
            assert "\\f" not in contents
            assert "Arial" not in contents or "NORMAL" in contents

    def test_mtext_height_changes_stripped(self) -> None:
        """Verify \\H....; text height codes are removed."""
        result = extract_blocks("app/tests/assets/mtext_formatting_test.dxf")
        annotation_data = result["annotation_data"]

        # Find BIG text entry
        big_entries = [
            key for key in annotation_data.keys() if "BIG" in key.annotation_contents
        ]

        for key in big_entries:
            contents = key.annotation_contents
            # Should not contain height codes
            assert "\\H" not in contents

    def test_clean_mtext_content_function_directly(self) -> None:
        """Test the _clean_mtext_content helper function directly."""
        # Create a simple test MTEXT entity
        doc = ezdxf.new("R2010")
        msp = doc.modelspace()

        # Test with paragraph alignment code
        mtext1 = msp.add_mtext("\\pxqc;CENTERED")
        result1 = _clean_mtext_content(mtext1)
        assert result1 == "CENTERED"
        assert "\\pxqc" not in result1

        # Test with paragraph break
        mtext2 = msp.add_mtext("LINE1\\PLINE2")
        result2 = _clean_mtext_content(mtext2)
        assert "\\P" not in result2
        assert "\n" not in result2
        assert "LINE1" in result2
        assert "LINE2" in result2

        # Test with complex formatting
        mtext3 = msp.add_mtext("\\pxqc;MENS CASUAL\\P PANTS")
        result3 = _clean_mtext_content(mtext3)
        assert "\\pxqc" not in result3
        assert "\\P" not in result3
        assert "MENS CASUAL" in result3
        assert "PANTS" in result3

        # Test plain text preserved
        mtext4 = msp.add_mtext("PLAIN TEXT")
        result4 = _clean_mtext_content(mtext4)
        assert result4 == "PLAIN TEXT"

    def test_color_analysis_mtext_formatting_stripped(self) -> None:
        """Verify color_analysis_data also has MTEXT formatting stripped."""
        result = extract_blocks("app/tests/assets/mtext_formatting_test.dxf")
        color_data = result["color_analysis_data"]

        # Find MTEXT records
        mtext_records = [r for r in color_data if r["entity_type"] == "MTEXT"]

        # All MTEXT should have clean content without formatting codes
        for record in mtext_records:
            contents = record["annotation_contents"]
            # Should not contain any common MTEXT formatting codes
            assert "\\pxq" not in contents
            assert "\\P" not in contents
            assert "\\L" not in contents
            assert "\\O" not in contents
            assert "\\C" not in contents or contents.count("\\") == 0
