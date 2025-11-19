"""
Fast introspection tests for GUI widget structure.

These tests verify widget existence, attributes, and relationships without
requiring GUI rendering. They are fast and suitable for CI/CD environments
without X server or display capabilities.

Usage:
    uv run pytest -m fast
"""

import pytest
from main import DWGExtractorApp
from pytest_mock import MockerFixture

from core.constants import MSG_SELECT_FILE


@pytest.mark.fast
class TestWidgetStructure:
    """Test widget creation and configuration without rendering."""

    def test_app_initializes_successfully(self) -> None:
        """Verify DWGExtractorApp creates instance without errors."""
        app = DWGExtractorApp()
        assert app is not None
        assert isinstance(app, DWGExtractorApp)
        app.destroy()

    def test_window_has_correct_configuration(self) -> None:
        """Verify window title, geometry, and resizable settings."""
        app = DWGExtractorApp()

        assert app.title() == "DWG Block Extractor"
        assert app.geometry() == "500x300"
        assert app.resizable() == (False, False), "Window should not be resizable"

        app.destroy()

    def test_file_entry_widget_exists_with_correct_attributes(self) -> None:
        """Verify file_entry widget exists with correct configuration."""
        app = DWGExtractorApp()

        assert hasattr(app, "file_entry"), "App should have file_entry attribute"
        assert app.file_entry is not None

        # Check width
        assert (
            app.file_entry.cget("width") == 360
        ), "file_entry should have width of 360"

        # Check placeholder text
        assert (
            app.file_entry.cget("placeholder_text") == MSG_SELECT_FILE
        ), f"file_entry placeholder should be '{MSG_SELECT_FILE}'"

        # Check state
        assert (
            app.file_entry.cget("state") == "readonly"
        ), "file_entry should be readonly"

        app.destroy()

    def test_browse_button_exists_with_correct_attributes(self) -> None:
        """Verify browse_button widget exists with correct configuration."""
        app = DWGExtractorApp()

        assert hasattr(app, "browse_button"), "App should have browse_button attribute"
        assert app.browse_button is not None

        # Check text
        assert (
            app.browse_button.cget("text") == "Browse"
        ), "browse_button text should be 'Browse'"

        # Check width
        assert (
            app.browse_button.cget("width") == 120
        ), "browse_button should have width of 120"

        # Check command is bound to _browse_file method
        command = app.browse_button.cget("command")
        assert command is not None, "browse_button should have a command"
        assert callable(command), "browse_button command should be callable"

        app.destroy()

    def test_extract_button_exists_with_correct_attributes(self) -> None:
        """Verify extract_button widget exists with correct configuration."""
        app = DWGExtractorApp()

        assert hasattr(app, "extract_button"), "App should have extract_button attribute"
        assert app.extract_button is not None

        # Check text
        assert (
            app.extract_button.cget("text") == "Extract"
        ), "extract_button text should be 'Extract'"

        # Check width
        assert (
            app.extract_button.cget("width") == 120
        ), "extract_button should have width of 120"

        # Check command is bound to _extract_blocks method
        command = app.extract_button.cget("command")
        assert command is not None, "extract_button should have a command"
        assert callable(command), "extract_button command should be callable"

        # Check initial state is disabled
        assert (
            app.extract_button.cget("state") == "disabled"
        ), "extract_button should be initially disabled"

        app.destroy()

    def test_progress_bar_exists_with_correct_attributes(self) -> None:
        """Verify progress_bar widget exists with correct configuration."""
        app = DWGExtractorApp()

        assert hasattr(app, "progress_bar"), "App should have progress_bar attribute"
        assert app.progress_bar is not None

        # Check width
        assert (
            app.progress_bar.cget("width") == 400
        ), "progress_bar should have width of 400"

        # Check height
        assert (
            app.progress_bar.cget("height") == 20
        ), "progress_bar should have height of 20"

        # Check initial value is 0
        assert app.progress_bar.get() == 0, "progress_bar should initially be at 0"

        app.destroy()

    def test_status_label_exists_with_correct_attributes(self) -> None:
        """Verify status_label widget exists with correct configuration."""
        app = DWGExtractorApp()

        assert hasattr(app, "status_label"), "App should have status_label attribute"
        assert app.status_label is not None

        # Check initial text is empty
        assert (
            app.status_label.cget("text") == ""
        ), "status_label should initially be empty"

        app.destroy()

    def test_extract_button_enables_after_file_selection(
        self, mocker: MockerFixture
    ) -> None:
        """Verify extract_button becomes enabled after file selection."""
        app = DWGExtractorApp()

        # Mock filedialog.askopenfilename to return a file path
        mock_file_path = "/fake/path/test.dwg"
        mocker.patch(
            "tkinter.filedialog.askopenfilename", return_value=mock_file_path
        )

        # Verify extract_button is initially disabled
        assert (
            app.extract_button.cget("state") == "disabled"
        ), "extract_button should be initially disabled"

        # Simulate file selection
        app._browse_file()

        # Verify extract_button is now enabled
        assert (
            app.extract_button.cget("state") == "normal"
        ), "extract_button should be enabled after file selection"

        # Verify file path was stored
        assert (
            app.selected_file_path == mock_file_path
        ), "selected_file_path should be set to the mocked file path"

        app.destroy()

    def test_widgets_have_correct_parent_relationships(self) -> None:
        """Verify all widgets have proper parent frames."""
        app = DWGExtractorApp()

        # file_entry, progress_bar, and status_label should have a parent frame
        assert (
            app.file_entry.master is not None
        ), "file_entry should have a parent widget"
        assert (
            app.browse_button.master is not None
        ), "browse_button should have a parent widget"
        assert (
            app.extract_button.master is not None
        ), "extract_button should have a parent widget"
        assert (
            app.progress_bar.master is not None
        ), "progress_bar should have a parent widget"
        assert (
            app.status_label.master is not None
        ), "status_label should have a parent widget"

        # browse_button and extract_button should share the same parent (button_frame)
        assert (
            app.browse_button.master == app.extract_button.master
        ), "browse_button and extract_button should share the same parent frame"

        app.destroy()
