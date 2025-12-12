# Feature: Pipeline Integration + Polish (Unit 7 - Phases D1-D2)

## Feature Description

This specification covers the final integration phases (D1-D2) of the combined implementation plan (064-combined-gui-settings-and-parallel-removal-plan.md). Unit 7 wires the configurable settings from the SettingsManager through the extraction pipeline and adds output customization features.

**D1: Pipeline Integration** - Updates `extract_blocks()` in extractor.py to accept new early-exit threshold parameters, updates geometry.py functions to accept configurable epsilon and tolerance parameters, and updates main.py to pass threshold settings from SettingsManager to the extraction pipeline.

**D2: Polish & Persistence** - Implements output path customization with `_get_output_path()`, filename formatting with prefix and timestamp settings, wires auto_open_excel and show_success_dialog settings to existing behavior, and ensures settings file version field exists for future migration support.

**Scope:** D1 (Pipeline Integration) + D2 (Polish & Persistence)

**Prerequisites:**
- Unit 1-2 (A1-A6) completed: Parallel processing removed from extractor.py
- Unit 3 (B1-B2) completed: AppSettings TypedDict (24 fields), SETTINGS_VALIDATION_REGISTRY
- Unit 4 (B3-B4) completed: SettingsManager class with JSON persistence
- Unit 5 (C1) completed: Main GUI migration with Settings button
- Unit 6 (C2) completed: AdvancedSettingsWindow with 5 tabs
- Tests: 919 passing

## User Story

As a DXF Block Extractor user
I want my advanced settings to actually affect extraction behavior and output
So that I can fine-tune performance thresholds, control output file naming and location, and have a consistent experience across sessions

## Problem Statement

After Unit 6, the Advanced Settings Window allows users to view and modify 24 settings, but:

1. **Performance thresholds are not wired** - polygon_count_threshold, line_segment_threshold, entity_count_threshold settings exist but are not passed to the extraction pipeline
2. **Precision settings are not wired** - coord_dedup_epsilon and rotation_tolerance exist but geometry.py functions use hardcoded values
3. **Output settings have no effect** - output_directory, filename_prefix, include_timestamp settings are stored but ignored during Excel generation
4. **Behavior toggles are not connected** - auto_open_excel and show_success_dialog settings do not control the actual behavior
5. **Settings file lacks version** - Future migration will be difficult without a version field

## Solution Statement

Implement D1 and D2 phases to complete the settings integration:

**D1: Pipeline Integration**
1. Add three new parameters to `extract_blocks()`: polygon_count_threshold, line_segment_threshold, entity_count_threshold
2. Update `_detect_content_zone()` in geometry.py to use passed thresholds instead of constants
3. Update `_get_intersection_points()` to accept epsilon parameter
4. Update `_categorize_rotation()` to accept tolerance parameter
5. Update main.py `_extraction_worker()` to pass threshold settings from SettingsManager

**D2: Polish & Persistence**
1. Add `_get_output_path()` method to main.py for custom output directory support
2. Add `_format_filename()` method for prefix and timestamp handling
3. Wire auto_open_excel setting to `_open_excel_file()` call
4. Wire show_success_dialog setting to success messagebox display
5. Verify settings.py save() includes version field (already implemented in Unit 4)
6. Verify settings.py load() handles corrupted files gracefully (already implemented in Unit 4)
7. Optional: Add filename preview widget to Output tab in settings_window.py

## Relevant Files

Use these files to implement the feature:

- `app/core/extractor.py` - Main extraction function that needs new parameters
  - Add polygon_count_threshold, line_segment_threshold, entity_count_threshold parameters to `extract_blocks()` signature
  - Pass thresholds to `_detect_content_zone()` calls
  - Current signature at line 968-980

- `app/core/geometry.py` - Geometry functions that use hardcoded values
  - Update `_get_intersection_points()` at line 266 to accept epsilon parameter (currently hardcoded to 0.01)
  - Update `_categorize_rotation()` at line 397 to accept tolerance parameter (currently hardcoded to 1.0)
  - Update `_detect_content_zone()` at line 1041 to accept threshold parameters (currently uses constants)

- `app/core/constants.py` - Contains default values for thresholds
  - POLYGON_COUNT_THRESHOLD (line 169)
  - LINE_SEGMENT_THRESHOLD (line 175)
  - ENTITY_COUNT_THRESHOLD (line 181)
  - DEFAULT_COORD_DEDUP_EPSILON (line 338)
  - DEFAULT_ROTATION_TOLERANCE (line 339)

- `app/main.py` - Main GUI that calls extract_blocks()
  - Update `_extraction_worker()` to pass threshold settings
  - Add `_get_output_path()` method for output directory customization
  - Add `_format_filename()` method for prefix/timestamp support
  - Update `_show_success_ui()` to respect show_success_dialog setting
  - Update `_show_success()` to respect auto_open_excel setting

- `app/core/settings.py` - SettingsManager class
  - Verify SETTINGS_VERSION is included in save() output (line 49)
  - Verify load() handles corrupted JSON gracefully (line 333)

- `app/core/settings_window.py` - Advanced Settings Window
  - Optional: Add filename preview widget to Output tab

- `app/tests/core/extractor/test_extractor_core.py` - Extractor tests
  - Add tests for new threshold parameters

- `app/tests/core/test_geometry.py` - Geometry tests
  - Add tests for parameterized epsilon and tolerance

### New Files

None - this unit modifies existing files only.

## Implementation Plan

### Phase 1: Foundation (D1 - Parameter Updates)

Update function signatures to accept configurable parameters while maintaining backward compatibility with default values:

1. Update `_get_intersection_points()` to accept `epsilon` parameter with default from constants
2. Update `_categorize_rotation()` to accept `tolerance` parameter with default from constants
3. Update `_detect_content_zone()` to accept threshold parameters with defaults from constants
4. Update `extract_blocks()` to accept threshold parameters and pass them through

### Phase 2: Core Implementation (D1 - Pipeline Wiring)

Wire the new parameters through the extraction pipeline:

1. Update main.py `_extraction_worker()` to read threshold settings from SettingsManager
2. Pass threshold values to `extract_blocks()` call
3. Ensure defaults are used when settings are not explicitly set

### Phase 3: Integration (D2 - Output Customization)

Implement output path and filename customization:

1. Add `_get_output_path()` method to main.py
2. Add `_format_filename()` method to main.py
3. Update Excel file generation to use custom output path
4. Wire auto_open_excel and show_success_dialog settings to behavior
5. Optional: Add filename preview to Advanced Settings Output tab

## Step by Step Tasks

IMPORTANT: Execute every step in order, top to bottom.

### Step 1: Update geometry.py _get_intersection_points() Signature

Update the function to accept an optional epsilon parameter:

**File:** `app/core/geometry.py`

Change from:
```python
def _get_intersection_points(block_def: BlockLayout) -> tuple[list[float], list[float]]:
    """..."""
    epsilon = 0.01  # Tolerance for floating-point comparison
```

To:
```python
def _get_intersection_points(
    block_def: BlockLayout,
    epsilon: float = DEFAULT_COORD_DEDUP_EPSILON,
) -> tuple[list[float], list[float]]:
    """
    Identify unique vertical and horizontal intersection points in a block definition.

    ...existing docstring...

    Args:
        block_def: ezdxf block definition object
        epsilon: Tolerance for floating-point comparison when deduplicating
                 coordinates. Default: DEFAULT_COORD_DEDUP_EPSILON (0.01)

    Returns:
        Tuple of (sorted_vertical_points, sorted_horizontal_points)
    """
    # Remove hardcoded epsilon = 0.01 line (parameter now provides this)
```

Add import at top of file:
```python
from .constants import (
    ARC_FLATTENING_SAGITTA,
    DEFAULT_COORD_DEDUP_EPSILON,
    DEFAULT_ROTATION_TOLERANCE,
    ENTITY_COUNT_THRESHOLD,
    LINE_SEGMENT_THRESHOLD,
    POLYGON_COUNT_THRESHOLD,
)
```

### Step 2: Update geometry.py _categorize_rotation() Signature

Update the function to accept an optional tolerance parameter:

**File:** `app/core/geometry.py`

Change from:
```python
def _categorize_rotation(angle: float) -> str:
    """..."""
    # Normalize angle to 0-360 range
    normalized = angle % 360

    # Check for standard angles with +/-1 degree tolerance
    if abs(normalized - 0) <= 1 or abs(normalized - 360) <= 1:
```

To:
```python
def _categorize_rotation(
    angle: float,
    tolerance: float = DEFAULT_ROTATION_TOLERANCE,
) -> str:
    """
    Categorize a rotation angle into standard rotation categories.

    ...existing docstring...

    Args:
        angle: Rotation angle in degrees (can be negative or > 360)
        tolerance: Tolerance in degrees for matching standard angles.
                   Default: DEFAULT_ROTATION_TOLERANCE (1.0)

    Returns:
        String representing rotation category: '0', '90', '180', '270', or 'other'
    """
    # Normalize angle to 0-360 range
    normalized = angle % 360

    # Check for standard angles with configurable tolerance
    if abs(normalized - 0) <= tolerance or abs(normalized - 360) <= tolerance:
        result = "0"
    elif abs(normalized - 90) <= tolerance:
        result = "90"
    elif abs(normalized - 180) <= tolerance:
        result = "180"
    elif abs(normalized - 270) <= tolerance:
        result = "270"
    else:
        result = "other"
```

### Step 3: Update geometry.py _detect_content_zone() Signature

Update the function to accept threshold parameters:

**File:** `app/core/geometry.py`

Change from:
```python
def _detect_content_zone(
    block_def: BlockLayout,
    block_bbox: tuple[float, float, float, float],
    abort_event: threading.Event | None = None,
    precision_tolerance: float = 1e-6,
    gap_bridge_tolerance: float = 0.0,
    min_area_filter: float = 0.0,
    min_side_filter: float = 0.0,
) -> ContentZoneData:
```

To:
```python
def _detect_content_zone(
    block_def: BlockLayout,
    block_bbox: tuple[float, float, float, float],
    abort_event: threading.Event | None = None,
    precision_tolerance: float = 1e-6,
    gap_bridge_tolerance: float = 0.0,
    min_area_filter: float = 0.0,
    min_side_filter: float = 0.0,
    *,
    polygon_count_threshold: int = POLYGON_COUNT_THRESHOLD,
    line_segment_threshold: int = LINE_SEGMENT_THRESHOLD,
    entity_count_threshold: int = ENTITY_COUNT_THRESHOLD,
) -> ContentZoneData:
    """
    Detect content zone and calculate trim values.

    ...existing docstring...

    Args:
        ...existing args...
        polygon_count_threshold: Maximum polygons for net area calculation.
            Blocks exceeding this skip content zone detection.
            Default: POLYGON_COUNT_THRESHOLD (500)
        line_segment_threshold: Maximum edges for region detection.
            Blocks exceeding this skip region detection.
            Default: LINE_SEGMENT_THRESHOLD (5000)
        entity_count_threshold: Maximum entities for content zone detection.
            Blocks exceeding this skip content zone entirely.
            Default: ENTITY_COUNT_THRESHOLD (1000)

    Returns:
        ContentZoneData with detected trim values
    """
```

Update the threshold checks inside the function to use the parameters instead of constants:

```python
    # UNIT 1: Fast entity count pre-check (O(n), no coordinate extraction)
    entity_count = sum(1 for _ in block_def)
    if entity_count > entity_count_threshold:
        logger.warning(
            f"[{block_name}] Skipping content zone: "
            f"{entity_count} entities exceeds threshold {entity_count_threshold}"
        )
        return _empty_content_zone_data()

    # UNIT 2: Fast edge count estimation (no coordinate extraction)
    estimated_edge_count = _estimate_edge_count(block_def)
    if estimated_edge_count > line_segment_threshold:
        logger.warning(
            f"[{block_name}] Skipping region detection: "
            f"~{estimated_edge_count} estimated edges exceeds threshold {line_segment_threshold}"
        )
        # ... return early ...

    # Check polygon count BEFORE net area calculation
    if len(all_shapes) > polygon_count_threshold:
        logger.warning(
            f"[{block_name}] Skipping content zone: "
            f"{len(all_shapes)} polygons exceeds threshold {polygon_count_threshold}"
        )
        # ... return early ...
```

### Step 4: Update extractor.py extract_blocks() Signature

Add the new threshold parameters to the extraction function:

**File:** `app/core/extractor.py`

Change from:
```python
def extract_blocks(
    file_path: str,
    abort_event: threading.Event | None = None,
    unit_override: int | None = None,
    gap_bridge_enabled: bool = False,
    gap_bridge_amount: float | None = None,
    precision_fix_enabled: bool = True,
    precision_fix_amount: float | None = None,
    min_area_filter_enabled: bool = False,
    min_area_filter_amount: float | None = None,
    min_side_filter_enabled: bool = False,
    min_side_filter_amount: float | None = None,
) -> ExtractionResult:
```

To:
```python
def extract_blocks(
    file_path: str,
    abort_event: threading.Event | None = None,
    *,
    unit_override: int | None = None,
    gap_bridge_enabled: bool = False,
    gap_bridge_amount: float | None = None,
    precision_fix_enabled: bool = True,
    precision_fix_amount: float | None = None,
    min_area_filter_enabled: bool = False,
    min_area_filter_amount: float | None = None,
    min_side_filter_enabled: bool = False,
    min_side_filter_amount: float | None = None,
    # New parameters (early-exit thresholds)
    polygon_count_threshold: int | None = None,
    line_segment_threshold: int | None = None,
    entity_count_threshold: int | None = None,
) -> ExtractionResult:
    """
    Extract comprehensive CAD analysis from a DXF file.

    ...existing docstring...

    Args:
        ...existing args...
        polygon_count_threshold: Maximum polygons for content zone calculation.
            None uses default (500). Blocks exceeding this skip content zone.
        line_segment_threshold: Maximum edges for region detection.
            None uses default (5000). Blocks exceeding this skip region detection.
        entity_count_threshold: Maximum entities for content zone detection.
            None uses default (1000). Blocks exceeding this skip content zone.

    Returns:
        ExtractionResult TypedDict containing all analysis data.
    """
```

Add import for threshold constants:
```python
from .constants import (
    DEFAULT_GAP_CLOSURE_TOLERANCE,
    DEFAULT_MIN_AREA_FILTER,
    DEFAULT_MIN_SIDE_FILTER,
    DXF_INSUNITS_MAP,
    ENTITY_COUNT_THRESHOLD,
    LINE_SEGMENT_THRESHOLD,
    POLYGON_COUNT_THRESHOLD,
    SUPPORTED_EXTENSIONS,
)
```

### Step 5: Update extractor.py to Pass Thresholds to _detect_content_zone()

Update the _detect_content_zone() call inside extract_blocks():

**File:** `app/core/extractor.py`

Find the call to `_detect_content_zone()` in the PHASE 2 block (around line 1248) and update it:

Change from:
```python
            # Detect content zone
            content_zone = _detect_content_zone(
                block_def,
                bbox,
                abort_event,
                precision_tolerance,
                gap_bridge_tolerance,
                min_area,
                min_side,
            )
```

To:
```python
            # Detect content zone
            # Use passed thresholds or fall back to constants
            effective_polygon_threshold = (
                polygon_count_threshold
                if polygon_count_threshold is not None
                else POLYGON_COUNT_THRESHOLD
            )
            effective_line_threshold = (
                line_segment_threshold
                if line_segment_threshold is not None
                else LINE_SEGMENT_THRESHOLD
            )
            effective_entity_threshold = (
                entity_count_threshold
                if entity_count_threshold is not None
                else ENTITY_COUNT_THRESHOLD
            )

            content_zone = _detect_content_zone(
                block_def,
                bbox,
                abort_event,
                precision_tolerance,
                gap_bridge_tolerance,
                min_area,
                min_side,
                polygon_count_threshold=effective_polygon_threshold,
                line_segment_threshold=effective_line_threshold,
                entity_count_threshold=effective_entity_threshold,
            )
```

### Step 6: Update main.py _extraction_worker() to Pass Thresholds

Update the extraction call in main.py to pass threshold settings:

**File:** `app/main.py`

In `_extraction_worker()`, update the `extract_blocks()` call:

Change from:
```python
            extraction_result = extract_blocks(
                self.selected_file_path,
                self.abort_event,
                unit_override=unit_override,
                gap_bridge_enabled=gap_bridge_enabled,
                gap_bridge_amount=gap_bridge_amount,
                precision_fix_enabled=precision_fix_enabled,
                precision_fix_amount=precision_fix_amount,
                min_area_filter_enabled=min_area_filter_enabled,
                min_area_filter_amount=min_area_filter_amount,
                min_side_filter_enabled=min_side_filter_enabled,
                min_side_filter_amount=min_side_filter_amount,
            )
```

To:
```python
            # Get threshold settings from SettingsManager
            polygon_threshold = self.settings.get("polygon_count_threshold")
            line_threshold = self.settings.get("line_segment_threshold")
            entity_threshold = self.settings.get("entity_count_threshold")

            self.logger.debug(
                f"Threshold settings: polygon={polygon_threshold}, "
                f"line={line_threshold}, entity={entity_threshold}"
            )

            extraction_result = extract_blocks(
                self.selected_file_path,
                self.abort_event,
                unit_override=unit_override,
                gap_bridge_enabled=gap_bridge_enabled,
                gap_bridge_amount=gap_bridge_amount,
                precision_fix_enabled=precision_fix_enabled,
                precision_fix_amount=precision_fix_amount,
                min_area_filter_enabled=min_area_filter_enabled,
                min_area_filter_amount=min_area_filter_amount,
                min_side_filter_enabled=min_side_filter_enabled,
                min_side_filter_amount=min_side_filter_amount,
                polygon_count_threshold=polygon_threshold,
                line_segment_threshold=line_threshold,
                entity_count_threshold=entity_threshold,
            )
```

### Step 7: Add _format_filename() Method to main.py

Add a method to format output filenames with optional prefix and timestamp:

**File:** `app/main.py`

Add this method to the `DXFExtractorApp` class:

```python
    def _format_filename(self, input_path: Path) -> str:
        """Format output filename with optional prefix and timestamp.

        Args:
            input_path: Path to the input DXF file

        Returns:
            Formatted filename (without directory) for the output Excel file
        """
        base_name = input_path.stem

        # Get settings
        prefix = self.settings.get("filename_prefix") or ""
        include_timestamp = self.settings.get("include_timestamp")

        # Build filename parts
        parts = []

        if prefix:
            parts.append(prefix)

        parts.append(base_name)

        if include_timestamp:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            parts.append(timestamp)

        # Join with underscore and add extension
        filename = "_".join(parts) + ".xlsx"

        self.logger.debug(f"Formatted filename: {filename}")
        return filename
```

### Step 8: Add _get_output_path() Method to main.py

Add a method to determine the output file path:

**File:** `app/main.py`

Add this method to the `DXFExtractorApp` class:

```python
    def _get_output_path(self, input_path: Path) -> Path:
        """Get output file path respecting output directory setting.

        Args:
            input_path: Path to the input DXF file

        Returns:
            Full path for the output Excel file
        """
        filename = self._format_filename(input_path)

        # Check for custom output directory
        custom_dir = self.settings.get("output_directory")

        if custom_dir:
            output_dir = Path(custom_dir)
            # Verify directory exists or can be created
            if not output_dir.exists():
                try:
                    output_dir.mkdir(parents=True, exist_ok=True)
                    self.logger.info(f"Created output directory: {output_dir}")
                except OSError as e:
                    self.logger.warning(
                        f"Cannot create output directory {output_dir}: {e}. "
                        "Using input file directory."
                    )
                    output_dir = input_path.parent
        else:
            # Default: same directory as input file
            output_dir = input_path.parent

        output_path = output_dir / filename
        self.logger.debug(f"Output path: {output_path}")
        return output_path
```

### Step 9: Update _extraction_worker() to Use Custom Output Path

Update the Excel generation to use the new output path method:

**File:** `app/main.py`

In `_extraction_worker()`, change the Excel generation section:

Change from:
```python
            # Step 3: Generate Excel
            self._update_progress(0.7, "Generating Excel...")

            excel_path = write_excel(extraction_result, self.selected_file_path)
            self.output_excel_path = excel_path
```

To:
```python
            # Step 3: Generate Excel
            self._update_progress(0.7, "Generating Excel...")

            # Determine output path with custom directory and filename formatting
            input_path = Path(self.selected_file_path)
            output_path = self._get_output_path(input_path)

            excel_path = write_excel(
                extraction_result,
                self.selected_file_path,
                output_path=str(output_path),
            )
            self.output_excel_path = excel_path
```

### Step 10: Update excel_writer.py write_excel() to Accept output_path

Update write_excel() to accept an optional output_path parameter:

**File:** `app/core/excel_writer.py`

Update the function signature (find the write_excel function and update it):

Change from:
```python
def write_excel(extraction_result: ExtractionResult, input_file_path: str) -> str:
    """Write extraction results to an Excel file."""
```

To:
```python
def write_excel(
    extraction_result: ExtractionResult,
    input_file_path: str,
    output_path: str | None = None,
) -> str:
    """Write extraction results to an Excel file.

    Args:
        extraction_result: Extraction result data to write
        input_file_path: Path to the input DXF file (used for default output naming)
        output_path: Optional custom output path. If None, generates path from input file.

    Returns:
        Path to the created Excel file
    """
```

Update the output path logic inside the function:

Change from (find the section that generates the output filename):
```python
    # Generate output filename
    input_path = Path(input_file_path)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_filename = f"{input_path.stem}_{timestamp}.xlsx"
    output_path = input_path.parent / output_filename
```

To:
```python
    # Determine output path
    if output_path:
        final_output_path = Path(output_path)
    else:
        # Default: generate timestamped filename in same directory as input
        input_path = Path(input_file_path)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"{input_path.stem}_{timestamp}.xlsx"
        final_output_path = input_path.parent / output_filename
```

Update the workbook.save() call to use final_output_path and return it:
```python
    workbook.save(str(final_output_path))
    return str(final_output_path)
```

### Step 11: Wire auto_open_excel Setting

Update the success handling to respect the auto_open_excel setting:

**File:** `app/main.py`

Update `_show_success_ui()` method:

Change from:
```python
    def _show_success_ui(self, excel_path: str) -> None:
        """Actually show success dialog (must run on main thread)."""
        self.logger.info(f"Extraction completed successfully, Excel file: {excel_path}")

        messagebox.showinfo(
            "Success",
            f"Extraction complete!\n\nExcel file created:\n{Path(excel_path).name}",
        )

        # Enable Open Folder button
        self.open_folder_button.configure(state="normal")

        # Auto-open Excel file
        self._open_excel_file(excel_path)
```

To:
```python
    def _show_success_ui(self, excel_path: str) -> None:
        """Actually show success dialog (must run on main thread)."""
        self.logger.info(f"Extraction completed successfully, Excel file: {excel_path}")

        # Show success dialog if enabled
        show_dialog = self.settings.get("show_success_dialog")
        if show_dialog:
            messagebox.showinfo(
                "Success",
                f"Extraction complete!\n\nExcel file created:\n{Path(excel_path).name}",
            )

        # Enable Open Folder button
        self.open_folder_button.configure(state="normal")

        # Auto-open Excel file if enabled
        auto_open = self.settings.get("auto_open_excel")
        if auto_open:
            self._open_excel_file(excel_path)
```

### Step 12: Verify Settings Version and Error Handling

Verify that settings.py already implements version field and error handling correctly:

**File:** `app/core/settings.py`

Verify the following exists (should already be implemented from Unit 4):

1. `SETTINGS_VERSION` constant at module level (line ~49)
2. `save()` method includes version in output (line ~387)
3. `load()` method handles JSON decode errors gracefully (line ~349)

If not present, these should already exist from Unit 4 implementation.

### Step 13: Add Tests for New extract_blocks() Parameters

Add tests to verify the new threshold parameters work correctly:

**File:** `app/tests/core/extractor/test_extractor_core.py`

Add these test cases:

```python
class TestExtractBlocksThresholdParameters:
    """Test threshold parameter handling in extract_blocks()."""

    def test_extract_blocks_accepts_threshold_parameters(
        self, sample_drawing_path: str
    ) -> None:
        """Verify extract_blocks accepts new threshold parameters."""
        result = extract_blocks(
            sample_drawing_path,
            polygon_count_threshold=100,
            line_segment_threshold=1000,
            entity_count_threshold=500,
        )
        assert "block_counts" in result

    def test_extract_blocks_none_thresholds_use_defaults(
        self, sample_drawing_path: str
    ) -> None:
        """Verify None threshold values fall back to defaults."""
        # Should not raise and should use defaults
        result = extract_blocks(
            sample_drawing_path,
            polygon_count_threshold=None,
            line_segment_threshold=None,
            entity_count_threshold=None,
        )
        assert "block_counts" in result

    def test_extract_blocks_low_thresholds_skip_content_zone(
        self, high_entity_count_path: str
    ) -> None:
        """Verify low thresholds cause content zone detection to be skipped."""
        result = extract_blocks(
            high_entity_count_path,
            entity_count_threshold=10,  # Very low threshold
        )
        # Content zone should be skipped for complex blocks
        for block_name, cz_data in result["block_content_zone_data"].items():
            # Blocks with high entity counts should have content_zone_detected=False
            # when threshold is very low
            pass  # This is structural - actual assertion depends on test file
```

### Step 14: Add Tests for geometry.py Parameter Changes

Add tests for the updated geometry functions:

**File:** `app/tests/core/test_geometry.py`

Add these test cases:

```python
class TestGetIntersectionPointsEpsilon:
    """Test _get_intersection_points with configurable epsilon."""

    def test_default_epsilon_deduplicates_close_points(self) -> None:
        """Verify default epsilon deduplicates points within 0.01."""
        # Test with a simple block containing close points
        pass  # Implement based on existing test patterns

    def test_custom_epsilon_respected(self) -> None:
        """Verify custom epsilon value is used for deduplication."""
        pass  # Implement based on existing test patterns


class TestCategorizeRotationTolerance:
    """Test _categorize_rotation with configurable tolerance."""

    def test_default_tolerance_one_degree(self) -> None:
        """Verify default tolerance of 1 degree."""
        from app.core.geometry import _categorize_rotation

        assert _categorize_rotation(0.5) == "0"
        assert _categorize_rotation(89.5) == "90"
        assert _categorize_rotation(1.5) == "other"

    def test_custom_tolerance_respected(self) -> None:
        """Verify custom tolerance value is used."""
        from app.core.geometry import _categorize_rotation

        # With tolerance=2.0, 1.5 should match 0
        assert _categorize_rotation(1.5, tolerance=2.0) == "0"
        # With tolerance=0.1, 0.5 should NOT match 0
        assert _categorize_rotation(0.5, tolerance=0.1) == "other"


class TestDetectContentZoneThresholds:
    """Test _detect_content_zone with configurable thresholds."""

    def test_custom_thresholds_accepted(self) -> None:
        """Verify custom threshold parameters are accepted."""
        # This tests the function signature, actual behavior tested in integration
        pass  # Implement based on existing test patterns
```

### Step 15: Run Type Checking

Verify all changes pass type checking:

```bash
uv run mypy app/core/geometry.py
uv run mypy app/core/extractor.py
uv run mypy app/core/excel_writer.py
uv run mypy app/main.py
uv run mypy app/
```

### Step 16: Run Linting and Formatting

Verify all changes pass linting:

```bash
uv run ruff check app/core/geometry.py
uv run ruff check app/core/extractor.py
uv run ruff check app/core/excel_writer.py
uv run ruff check app/main.py
uv run ruff check app/
uv run ruff format app/ --check
```

### Step 17: Run Full Test Suite

Run all tests to ensure no regressions:

```bash
uv run pytest app/tests/ -v
```

### Step 18: Manual Verification (Optional - Skip in WSL)

If running on a system with GUI support:

1. Launch application: `uv run python app/main.py`
2. Open Settings, go to Performance tab
3. Change polygon_count_threshold to 50 (very low)
4. Click Apply
5. Extract a complex DXF file
6. Verify log shows "Skipping content zone" for blocks with many polygons
7. Test output settings:
   - Set custom output_directory
   - Set filename_prefix to "test_"
   - Enable include_timestamp
   - Extract a file
   - Verify file is saved to custom directory with prefix and timestamp
8. Test behavior toggles:
   - Disable auto_open_excel
   - Extract a file
   - Verify Excel file is NOT auto-opened
   - Disable show_success_dialog
   - Extract a file
   - Verify no success dialog appears

## Testing Strategy

### Unit Tests

- Test `extract_blocks()` accepts new threshold parameters
- Test `extract_blocks()` uses defaults when thresholds are None
- Test `_get_intersection_points()` accepts and uses epsilon parameter
- Test `_categorize_rotation()` accepts and uses tolerance parameter
- Test `_detect_content_zone()` accepts and uses threshold parameters
- Test `_format_filename()` with various prefix/timestamp combinations
- Test `_get_output_path()` with custom directory and default behavior

### Integration Tests

- Test full extraction pipeline with custom thresholds
- Test output file creation in custom directory
- Test filename formatting end-to-end

### Edge Cases

- Threshold set to 0 (should still work, just skip everything)
- Threshold set to very high value (should never trigger skip)
- Empty filename_prefix (should not add underscore)
- Non-existent output_directory (should create or fall back)
- Invalid output_directory (read-only, etc.) should fall back gracefully
- include_timestamp=False with empty prefix (just base filename)
- Both auto_open_excel and show_success_dialog disabled

### Playwright MCP Tests

- Skip GUI tests in WSL per README.md guidance
- E2E tests may be added in a future unit if GUI testing infrastructure is established

## Acceptance Criteria

- [ ] `extract_blocks()` accepts polygon_count_threshold, line_segment_threshold, entity_count_threshold parameters
- [ ] `_detect_content_zone()` uses passed threshold values instead of constants
- [ ] `_get_intersection_points()` accepts epsilon parameter with default from constants
- [ ] `_categorize_rotation()` accepts tolerance parameter with default from constants
- [ ] main.py passes threshold settings from SettingsManager to extract_blocks()
- [ ] Default values used when settings are not explicitly set (None values)
- [ ] Existing behavior unchanged when using defaults
- [ ] `_format_filename()` method formats filenames with prefix and timestamp
- [ ] `_get_output_path()` method returns correct path for custom directory
- [ ] Custom output directory is created if it doesn't exist
- [ ] Falls back to input file directory if custom directory cannot be created
- [ ] auto_open_excel setting controls whether Excel is auto-opened
- [ ] show_success_dialog setting controls whether success dialog appears
- [ ] Settings file includes version field (verified from Unit 4)
- [ ] Corrupted settings file handled gracefully (verified from Unit 4)
- [ ] mypy passes with no errors on all modified files
- [ ] ruff check passes with no errors
- [ ] ruff format passes with no changes needed
- [ ] All existing tests pass (919+ tests)
- [ ] New tests for threshold parameters pass

## Validation Commands

Execute every command to validate the feature works correctly with zero regressions.

- `uv run mypy app/core/geometry.py` - Type check geometry module
- `uv run mypy app/core/extractor.py` - Type check extractor module
- `uv run mypy app/core/excel_writer.py` - Type check excel_writer module
- `uv run mypy app/main.py` - Type check main module
- `uv run mypy app/` - Full type check for any cascading issues
- `uv run ruff check app/core/geometry.py` - Lint geometry module
- `uv run ruff check app/core/extractor.py` - Lint extractor module
- `uv run ruff check app/core/excel_writer.py` - Lint excel_writer module
- `uv run ruff check app/main.py` - Lint main module
- `uv run ruff check app/` - Lint entire app directory
- `uv run ruff format app/ --check` - Check formatting for entire app
- `uv run pytest app/tests/core/test_geometry.py -v` - Run geometry tests
- `uv run pytest app/tests/core/extractor/ -v` - Run extractor tests
- `uv run pytest app/tests/ -v` - Run full test suite (should be 919+ tests, all passing)

## Notes

1. **Keyword-only arguments** - The new threshold parameters use `*` to make them keyword-only, preventing positional argument confusion with the existing parameters.

2. **None vs default handling** - Using `None` to indicate "use default" allows distinguishing between "user didn't set this" and "user explicitly set this to the default value". The effective threshold is computed at the call site.

3. **Backward compatibility** - All new parameters have defaults, ensuring existing code calling `extract_blocks()` without the new parameters continues to work.

4. **Output directory fallback** - If the custom output directory cannot be created (permissions, invalid path, etc.), the code falls back to the input file's directory rather than failing.

5. **Filename timestamp format** - Uses `%Y%m%d_%H%M%S` format (e.g., "20251211_143052") for sortability and uniqueness.

6. **Settings version** - The SETTINGS_VERSION constant was added in Unit 4 and is already included in saved JSON. This allows future migration logic to handle schema changes.

7. **Filename preview (Optional)** - A live filename preview in the Output tab of Advanced Settings is marked as optional. It would show users what their filename will look like with current prefix/timestamp settings. This can be added if time permits but is not required for acceptance.

8. **After this unit completes**:
   - All 24 settings are fully wired to application behavior
   - Performance thresholds affect content zone detection
   - Output settings control file location and naming
   - Behavior toggles control auto-open and dialog display
   - Phase E (Full Validation Suite) can proceed to verify the complete implementation
