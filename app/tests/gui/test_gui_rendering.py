"""
GUI rendering tests that require display server (Xvfb).

These tests verify widgets are properly rendered, visible, and added to the
widget tree. They require a display server and are slower than introspection tests.

Usage:
    xvfb-run uv run pytest -m gui
"""

from typing import Generator

import pytest
from customtkinter import CTk, CTkButton
from main import DWGExtractorApp


@pytest.fixture
def gui_app() -> Generator[DWGExtractorApp, None, None]:
    """
    Create and render DWGExtractorApp instance for testing.

    Yields:
        DWGExtractorApp instance with rendered widgets
    """
    app = DWGExtractorApp()
    app.update_idletasks()  # Force rendering of widgets
    yield app
    app.destroy()


@pytest.mark.gui
class TestGUIRendering:
    """Test widget visibility and rendering in the widget tree."""

    def test_file_entry_is_visible_in_widget_tree(
        self, gui_app: DWGExtractorApp
    ) -> None:
        """Verify file_entry widget is visible in the rendered widget tree."""
        assert gui_app.file_entry.winfo_ismapped(), (
            "file_entry should be visible in widget tree. "
            "Widget was created but not added to layout (missing .pack() or .grid())"
        )

    def test_browse_button_is_visible_in_widget_tree(
        self, gui_app: DWGExtractorApp
    ) -> None:
        """Verify browse_button widget is visible in the rendered widget tree."""
        assert gui_app.browse_button.winfo_ismapped(), (
            "browse_button should be visible in widget tree. "
            "Widget was created but not added to layout (missing .pack() or .grid())"
        )

    def test_extract_button_is_visible_in_widget_tree(
        self, gui_app: DWGExtractorApp
    ) -> None:
        """Verify extract_button widget is visible in the rendered widget tree."""
        assert gui_app.extract_button.winfo_ismapped(), (
            "extract_button should be visible in widget tree. "
            "Widget was created but not added to layout (missing .pack() or .grid())"
        )

    def test_progress_bar_is_visible_in_widget_tree(
        self, gui_app: DWGExtractorApp
    ) -> None:
        """Verify progress_bar widget is visible in the rendered widget tree."""
        assert gui_app.progress_bar.winfo_ismapped(), (
            "progress_bar should be visible in widget tree. "
            "Widget was created but not added to layout (missing .pack() or .grid())"
        )

    def test_status_label_is_visible_in_widget_tree(
        self, gui_app: DWGExtractorApp
    ) -> None:
        """Verify status_label widget is visible in the rendered widget tree."""
        assert gui_app.status_label.winfo_ismapped(), (
            "status_label should be visible in widget tree. "
            "Widget was created but not added to layout (missing .pack() or .grid())"
        )

    def test_widgets_fail_if_not_packed_or_gridded(self) -> None:
        """
        Validate test methodology by verifying unpacked widgets fail visibility test.

        This test ensures our visibility tests catch layout bugs where widgets
        are created but not added to the layout manager.
        """
        # Create a minimal test app
        app = CTk()
        app.update_idletasks()

        # Create a widget but don't pack or grid it
        unpacked_button = CTkButton(app, text="Test")

        # Force render attempt
        app.update_idletasks()

        # Verify widget is NOT visible (validates test methodology)
        assert not unpacked_button.winfo_ismapped(), (
            "Unpacked widget should NOT be visible in widget tree. "
            "This validates that our tests will catch layout bugs."
        )

        app.destroy()

    def test_all_widgets_have_proper_geometry(self, gui_app: DWGExtractorApp) -> None:
        """Verify all widgets have non-zero dimensions after rendering."""
        # file_entry should have width
        assert (
            gui_app.file_entry.winfo_width() > 0
        ), "file_entry should have non-zero width after rendering"
        assert (
            gui_app.file_entry.winfo_height() > 0
        ), "file_entry should have non-zero height after rendering"

        # browse_button should have dimensions
        assert (
            gui_app.browse_button.winfo_width() > 0
        ), "browse_button should have non-zero width after rendering"
        assert (
            gui_app.browse_button.winfo_height() > 0
        ), "browse_button should have non-zero height after rendering"

        # extract_button should have dimensions
        assert (
            gui_app.extract_button.winfo_width() > 0
        ), "extract_button should have non-zero width after rendering"
        assert (
            gui_app.extract_button.winfo_height() > 0
        ), "extract_button should have non-zero height after rendering"

        # progress_bar should have dimensions
        assert (
            gui_app.progress_bar.winfo_width() > 0
        ), "progress_bar should have non-zero width after rendering"
        assert (
            gui_app.progress_bar.winfo_height() > 0
        ), "progress_bar should have non-zero height after rendering"

        # status_label should have dimensions
        assert (
            gui_app.status_label.winfo_width() > 0
        ), "status_label should have non-zero width after rendering"
        assert (
            gui_app.status_label.winfo_height() > 0
        ), "status_label should have non-zero height after rendering"
