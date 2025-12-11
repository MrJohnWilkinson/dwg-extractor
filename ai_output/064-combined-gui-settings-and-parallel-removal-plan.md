# Combined Implementation Plan: GUI Settings + Remove Parallel Processing

## Executive Summary

This plan combines the GUI Settings implementation (059) and Remove Parallel Processing (063) into a single sequenced roadmap for 100% completion. The parallel processing removal is executed first because it simplifies the extractor.py code that the GUI Settings plan modifies. The combined plan has 12 implementation phases organized for minimal rework and maximum stability.

## Table Summary

| Phase | Name | Source Plan | Files Modified | Dependencies |
|-------|------|-------------|----------------|--------------|
| **A1** | Remove Parallel Imports | 063 | `extractor.py` | None |
| **A2** | Delete _analyze_single_block | 063 | `extractor.py` | A1 |
| **A3** | Revert to Sequential Loop | 063 | `extractor.py` | A1, A2 |
| **A4** | Remove BlockAnalysisResult | 063 | `types.py` | A3 |
| **A5** | Update Parallel Tests | 063 | `test_extractor_parallel.py` | A3, A4 |
| **A6** | Archive Parallel Spec | 063 | `specs/archive/` | A5 |
| **B1** | Data Models | 059 Unit 1 | `types.py` | A4 |
| **B2** | Default Values Registry | 059 Unit 2 | `constants.py` | B1 |
| **B3** | SettingsManager Class | 059 Unit 3 | `settings.py` (new) | B1, B2 |
| **B4** | Platform-Specific Paths | 059 Unit 4 | `settings.py` | B3 |
| **C1** | Main GUI Migration | 059 Unit 5 | `main.py` | B1-B4 |
| **C2** | Advanced Settings Window | 059 Unit 6 | `settings_window.py` (new) | C1 |
| **D1** | Pipeline Integration | 059 Unit 7 | `extractor.py`, `geometry.py` | A3, C1 |
| **D2** | Polish & Persistence | 059 Unit 8 | `settings_window.py`, `main.py` | D1 |
| **E** | Full Validation Suite | Both | All | D2 |

## Relevant Files

- **app/core/extractor.py** - Remove parallel processing (A1-A3), add settings parameters (D1)
- **app/core/types.py** - Remove BlockAnalysisResult (A4), add AppSettings TypedDict (B1)
- **app/core/constants.py** - Add default value registries (B2)
- **app/core/settings.py** (new) - SettingsManager class (B3, B4)
- **app/core/settings_window.py** (new) - AdvancedSettingsWindow modal (C2)
- **app/core/geometry.py** - Accept configurable precision values (D1)
- **app/main.py** - Use SettingsManager, add Settings button (C1, D2)
- **app/tests/core/extractor/test_extractor_parallel.py** - Update for sequential behavior (A5)
- **app/tests/core/test_settings.py** (new) - Unit tests for SettingsManager (B3)
- **specs/058-unit-3-parallel-block-processing.md** - Archive to specs/archive/ (A6)

## Scope Adjustments

### Changes from Original Plans

1. **Removed `max_worker_threads` setting** - No longer needed after parallel processing removal
2. **Performance tab simplified** - Only contains early-exit thresholds, not thread settings
3. **AppSettings TypedDict reduced** - 24 fields instead of 25 (no max_worker_threads)
4. **Pipeline integration simplified** - No max_workers parameter needed

### Combined In-Scope

- All parallel processing removal from 063
- All GUI Settings features from 059 (minus worker thread setting)
- Full JSON persistence for settings
- Advanced Settings modal with 5 tabs
- Pipeline integration for configurable thresholds

### Combined Out-of-Scope

- Cloud sync, profiles, import/export
- ProcessPoolExecutor or alternative parallelism
- i18n, advanced a11y
- Settings undo/redo

---

## Phase A: Remove Parallel Processing

### A1: Remove Parallel Imports

**File:** `app/core/extractor.py:16`

```python
# DELETE this line:
from concurrent.futures import ThreadPoolExecutor, as_completed
```

**Validation:** `uv run mypy app/core/extractor.py` - expect errors (imports still referenced)

---

### A2: Delete _analyze_single_block Function

**File:** `app/core/extractor.py:879-982`

Delete the entire `_analyze_single_block()` function (104 lines). This function was created specifically for parallel processing and will be inlined back into the main loop.

**Validation:** `uv run mypy app/core/extractor.py` - expect errors (function calls remain)

---

### A3: Replace Phase 2 with Sequential Loop

**File:** `app/core/extractor.py:1299-1354`

Replace the `ThreadPoolExecutor` block with sequential processing:

```python
# PHASE 2: Sequential block geometry analysis
for block_def in doc.blocks:
    block_name = block_def.name

    # Skip modelspace/paperspace blocks
    if block_name in ("*Model_Space", "*Paper_Space") or block_name.startswith(
        "*Paper_Space"
    ):
        continue

    # Handle anonymous blocks starting with *U (dynamic block instances)
    if block_name.startswith("*U"):
        if block_name in anonymous_to_resolved:
            effective_name = anonymous_to_resolved[block_name]
        else:
            continue  # Skip unresolved *U blocks
    elif block_name.startswith("A$C"):
        if block_name in anonymous_to_resolved:
            effective_name = anonymous_to_resolved[block_name]
        else:
            effective_name = block_name
    elif block_name.startswith("*"):
        continue  # Skip other system blocks
    else:
        effective_name = block_name

    # Count entities
    entity_count = sum(1 for _ in block_def)
    block_entities[effective_name] = entity_count

    # Scan for nested INSERTs
    for entity in block_def:
        if entity.dxftype() == "INSERT":
            nested_name = entity.dxf.name
            if nested_name in anonymous_to_resolved:
                nested_name = anonymous_to_resolved[nested_name]
            if nested_name not in nested_block_parents:
                nested_block_parents[nested_name] = set()
            nested_block_parents[nested_name].add(effective_name)

    # Analyze block geometry
    bbox = _get_block_bounding_box(block_def)
    native_width = round(bbox[2] - bbox[0], 2)
    native_height = round(bbox[3] - bbox[1], 2)

    vertical_points, horizontal_points = _get_intersection_points(block_def)
    vertical_segments = _calculate_segments(vertical_points)
    horizontal_segments = _calculate_segments(horizontal_points)

    block_trimming_data[effective_name] = {
        "native_width": native_width,
        "native_height": native_height,
        "vertical_segments": vertical_segments,
        "horizontal_segments": horizontal_segments,
    }

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
    block_content_zone_data[effective_name] = content_zone

logger.info(f"Analyzed {len(block_entities)} block definitions")
logger.info(f"Analyzed geometry for {len(block_trimming_data)} block definitions")
```

**Key changes:**
- Remove `ThreadPoolExecutor` context manager
- Remove `futures` dictionary and `as_completed()` iterator
- Remove exception handling for `future.result()`
- Update logging messages (remove "parallel" and "workers" references)

**Validation:** `uv run mypy app/core/extractor.py` - should pass

---

### A4: Remove BlockAnalysisResult TypedDict

**File:** `app/core/types.py:274-291`

Delete the `BlockAnalysisResult` class:

```python
# DELETE this entire TypedDict:
class BlockAnalysisResult(TypedDict):
    """..."""
    entity_count: int
    trimming_data: BlockTrimmingData
    content_zone_data: ContentZoneData
    nested_inserts: list[str]
```

Also remove any import of `BlockAnalysisResult` from `extractor.py` if present.

**Validation:** `uv run mypy app/core/types.py` - should pass

---

### A5: Update Parallel Tests

**File:** `app/tests/core/extractor/test_extractor_parallel.py`

Rename file to `test_extractor_consistency.py` and update tests:

1. **Remove thread-specific tests:**
   - Remove `TestParallelProcessingThreadSafety.test_multiple_concurrent_extractions`
   - Simplify thread safety verification

2. **Keep result consistency tests:**
   - `test_consistent_results` - verify multiple runs produce identical results
   - `test_with_dynamic_blocks` - verify dynamic block resolution
   - `test_with_nested_blocks` - verify nested block tracking
   - `test_abort_event` - verify abort functionality
   - `test_empty_file` - verify edge case handling
   - `test_block_trimming_data` - verify data structure
   - `test_content_zone_data` - verify content zone detection

3. **Update docstrings** to remove parallel processing references

**Validation:** `uv run pytest app/tests/core/extractor/ -v`

---

### A6: Archive Original Spec

```bash
mkdir -p specs/archive
mv specs/058-unit-3-parallel-block-processing.md specs/archive/
```

---

## Phase B: GUI Settings Infrastructure

### B1: Data Models

**Purpose:** Define TypedDict structures for type-safe settings throughout the application.

**File:** `app/core/types.py`

Add `AppSettings` TypedDict (24 fields - excludes max_worker_threads):

```python
class AppSettings(TypedDict, total=False):
    # Filters (existing)
    unit_override: int | None
    precision_fix_enabled: bool
    precision_fix_amount: float | None
    gap_bridge_enabled: bool
    gap_bridge_amount: float | None
    min_area_filter_enabled: bool
    min_area_filter_amount: float | None
    min_side_filter_enabled: bool
    min_side_filter_amount: float | None

    # Performance (early-exit thresholds only - no thread settings)
    polygon_count_threshold: int
    line_segment_threshold: int
    entity_count_threshold: int

    # Precision
    arc_flattening_sagitta: float
    coord_dedup_epsilon: float
    rotation_tolerance: float

    # Output
    output_directory: str | None
    auto_open_excel: bool
    show_success_dialog: bool
    filename_prefix: str
    include_timestamp: bool

    # Logging
    generate_log_file: bool
    file_log_level: str
    log_viewer_level: str
    log_viewer_auto_scroll: bool
    log_viewer_max_lines: int
```

Add `SettingValidation` TypedDict:

```python
class SettingValidation(TypedDict):
    min_value: float | int | None
    max_value: float | int | None
    default: float | int | bool | str | None
    unit_aware: bool
```

**Acceptance Criteria:**
- [ ] `AppSettings` TypedDict defined with all 24 fields
- [ ] `SettingValidation` TypedDict defined
- [ ] mypy passes with no errors
- [ ] Existing tests still pass

---

### B2: Default Values Registry

**Purpose:** Centralize all default values and validation ranges in constants.py.

**File:** `app/core/constants.py`

Add performance threshold defaults (early-exit only, no thread settings):

```python
DEFAULT_POLYGON_COUNT_THRESHOLD: int = 500
DEFAULT_LINE_SEGMENT_THRESHOLD: int = 5000
DEFAULT_ENTITY_COUNT_THRESHOLD: int = 1000

POLYGON_COUNT_THRESHOLD_MIN: int = 100
POLYGON_COUNT_THRESHOLD_MAX: int = 10000
LINE_SEGMENT_THRESHOLD_MIN: int = 1000
LINE_SEGMENT_THRESHOLD_MAX: int = 50000
ENTITY_COUNT_THRESHOLD_MIN: int = 100
ENTITY_COUNT_THRESHOLD_MAX: int = 10000
```

Add precision setting defaults:

```python
DEFAULT_ARC_FLATTENING_SAGITTA: float = 0.1
DEFAULT_COORD_DEDUP_EPSILON: float = 0.01
DEFAULT_ROTATION_TOLERANCE: float = 1.0

ARC_FLATTENING_SAGITTA_MIN: float = 0.01
ARC_FLATTENING_SAGITTA_MAX: float = 1.0
COORD_DEDUP_EPSILON_MIN: float = 0.001
COORD_DEDUP_EPSILON_MAX: float = 1.0
ROTATION_TOLERANCE_MIN: float = 0.1
ROTATION_TOLERANCE_MAX: float = 5.0
```

Add output setting defaults:

```python
DEFAULT_AUTO_OPEN_EXCEL: bool = True
DEFAULT_SHOW_SUCCESS_DIALOG: bool = True
DEFAULT_INCLUDE_TIMESTAMP: bool = True
DEFAULT_FILENAME_PREFIX: str = ""
```

Add logging setting defaults:

```python
DEFAULT_LOG_VIEWER_LEVEL: str = "INFO"
DEFAULT_LOG_VIEWER_AUTO_SCROLL: bool = True
DEFAULT_LOG_VIEWER_MAX_LINES: int = 1000
```

Create `SETTINGS_VALIDATION_REGISTRY` dictionary mapping setting names to validation metadata.

**Acceptance Criteria:**
- [ ] All 24 settings have defaults defined
- [ ] All numeric settings have min/max ranges defined
- [ ] `SETTINGS_VALIDATION_REGISTRY` maps each setting to its validation metadata

---

### B3: SettingsManager Class

**Purpose:** Create centralized settings management with validation and type safety.

**File:** `app/core/settings.py` (new)

```python
class SettingsManager:
    """Manages application settings with validation and persistence."""

    def __init__(self, config_path: Path | None = None) -> None:
        """Initialize with optional custom config path."""

    def get(self, key: str) -> Any:
        """Get setting value with fallback to default."""

    def set(self, key: str, value: Any) -> bool:
        """Set and validate setting value. Returns True if valid."""

    def validate(self, key: str, value: Any) -> tuple[bool, str]:
        """Validate value against setting constraints. Returns (valid, error_msg)."""

    def get_default(self, key: str, unit_code: int | None = None) -> Any:
        """Get default value for setting, optionally unit-aware."""

    def reset_section(self, section: str) -> None:
        """Reset all settings in section to defaults."""

    def reset_all(self) -> None:
        """Reset all settings to defaults."""

    def to_dict(self) -> AppSettings:
        """Export current settings as AppSettings dict."""

    def from_dict(self, settings: AppSettings) -> None:
        """Import settings from AppSettings dict with validation."""
```

**Acceptance Criteria:**
- [ ] SettingsManager instantiates without errors
- [ ] `get()` returns default when setting not explicitly set
- [ ] `set()` validates and rejects out-of-range values
- [ ] `validate()` provides helpful error messages
- [ ] `get_default()` handles unit-aware settings correctly
- [ ] `reset_section()` resets only settings in specified section
- [ ] Unit tests cover all public methods

---

### B4: Platform-Specific Paths

**Purpose:** Implement cross-platform settings file location following OS conventions.

**File:** `app/core/settings.py`

Add path resolution:

```python
def _get_config_path(self) -> Path:
    """Get platform-appropriate config file path."""
    if sys.platform == "win32":
        base = Path(os.environ.get("APPDATA", "~"))
        return base / "DXFExtractor" / "settings.json"
    elif sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / "DXFExtractor" / "settings.json"
    else:  # Linux and others
        xdg_config = os.environ.get("XDG_CONFIG_HOME", "~/.config")
        return Path(xdg_config).expanduser() / "dxf-extractor" / "settings.json"
```

Implement `load()` and `save()` methods:

```python
def load(self) -> bool:
    """Load settings from JSON file. Returns True if file existed."""

def save(self) -> bool:
    """Save settings to JSON file. Returns True on success."""
```

**Acceptance Criteria:**
- [ ] Config path follows platform conventions (APPDATA, XDG_CONFIG_HOME, etc.)
- [ ] `load()` handles missing file gracefully (returns defaults)
- [ ] `load()` handles corrupted JSON gracefully (returns defaults with warning)
- [ ] `save()` creates parent directories if needed
- [ ] Settings persist across application restarts

---

## Phase C: Main GUI Integration

### C1: Main GUI Migration

**Purpose:** Migrate existing main.py settings to use SettingsManager without changing user-visible behavior.

**File:** `app/main.py`

1. Add SettingsManager instance to `DXFExtractorApp.__init__()`:
   ```python
   self.settings = SettingsManager()
   self.settings.load()
   ```

2. Initialize GUI control variables from SettingsManager.

3. Update getter methods to delegate to SettingsManager.

4. Add "Advanced Settings" button to main window:
   ```python
   self.advanced_settings_button = ctk.CTkButton(
       button_frame,
       text="Settings",
       width=80,
       command=self._open_advanced_settings,
   )
   ```

**Acceptance Criteria:**
- [ ] Existing filter controls function identically to before
- [ ] Default values populate from SettingsManager
- [ ] Validation uses SettingsManager.validate()
- [ ] "Settings" button visible in main window
- [ ] No visual changes to existing UI layout
- [ ] All existing tests pass

---

### C2: Advanced Settings Window

**Purpose:** Create tabbed modal window for advanced settings configuration.

**File:** `app/core/settings_window.py` (new)

```python
class AdvancedSettingsWindow(ctk.CTkToplevel):
    """Modal window for advanced settings configuration."""

    def __init__(self, parent: ctk.CTk, settings: SettingsManager) -> None:
        """Initialize with parent window and settings manager."""
```

Implement tab structure using `CTkTabview`:
- **Filters tab** - move existing controls here, add descriptions
- **Performance tab** - polygon/line/entity early-exit thresholds (NO worker threads)
- **Precision tab** - arc sagitta, epsilon, rotation tolerance
- **Output tab** - directory, auto-open, filename format
- **Logging tab** - viewer settings, file logging

Implement per-section reset buttons and Apply/Cancel/Save as Default buttons.

Implement validation feedback (red border on invalid entry).

**Acceptance Criteria:**
- [ ] Window opens as modal (blocks main window)
- [ ] All 5 tabs render correctly
- [ ] Each setting has label, entry/control, description, and valid range shown
- [ ] Per-section Reset buttons restore section defaults
- [ ] Apply button validates and closes window
- [ ] Cancel button closes without changes
- [ ] Save as Default persists to JSON
- [ ] Invalid entries show red border with validation message

---

## Phase D: Pipeline Integration

### D1: Pipeline Integration

**Purpose:** Wire configurable settings through extraction and geometry processing pipelines.

**File:** `app/core/extractor.py`

Update `extract_blocks()` signature (NO max_worker_threads - removed with parallel):

```python
def extract_blocks(
    file_path: str,
    abort_event: threading.Event | None = None,
    *,
    # Existing parameters
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
```

**File:** `app/core/geometry.py`

Update `_get_intersection_points()` to accept epsilon:
```python
def _get_intersection_points(
    block_def: BlockLayout,
    epsilon: float = DEFAULT_COORD_DEDUP_EPSILON,
) -> tuple[list[float], list[float]]:
```

Update `_categorize_rotation()` to accept tolerance:
```python
def _categorize_rotation(
    angle: float,
    tolerance: float = DEFAULT_ROTATION_TOLERANCE,
) -> str:
```

**File:** `app/main.py`

Update extraction call to pass settings:
```python
extraction_result = extract_blocks(
    self.selected_file_path,
    self.abort_event,
    # ... existing params ...
    polygon_count_threshold=self.settings.get("polygon_count_threshold"),
    line_segment_threshold=self.settings.get("line_segment_threshold"),
    entity_count_threshold=self.settings.get("entity_count_threshold"),
)
```

**Acceptance Criteria:**
- [ ] All configurable thresholds flow from settings to processing code
- [ ] Default values used when settings not explicitly set
- [ ] Existing behavior unchanged when using defaults
- [ ] Tests verify settings propagation

---

### D2: Polish & Persistence

**Purpose:** Final integration, save/load behavior, and edge case handling.

**Files:** `app/main.py`, `app/core/settings_window.py`

Implement output directory functionality:
```python
def _get_output_path(self, input_path: Path) -> Path:
    """Get output file path respecting output directory setting."""
    custom_dir = self.settings.get("output_directory")
    if custom_dir:
        return Path(custom_dir) / self._format_filename(input_path)
    return input_path.parent / self._format_filename(input_path)
```

Implement filename formatting, auto-open toggle, success dialog toggle.

Add settings migration for future versions (version field in JSON).

Add error recovery for corrupted settings file.

Implement filename preview in Output tab of Advanced Settings.

**Acceptance Criteria:**
- [ ] Custom output directory is used when configured
- [ ] Filename prefix and timestamp settings work correctly
- [ ] Auto-open Excel respects setting
- [ ] Success dialog respects setting
- [ ] Settings file includes version for future migration
- [ ] Corrupted settings file handled gracefully
- [ ] Filename preview updates live in Output tab

---

## Phase E: Full Validation Suite

Run complete validation:

```bash
# Type checking
uv run mypy app/

# Extractor tests (verifies sequential behavior)
uv run pytest app/tests/core/extractor/ -v

# Full test suite
uv run pytest app/tests/ -v

# Linting
uv run ruff check app/

# Format verification
uv run ruff format app/ --check
```

---

## Implementation Sequence Diagram

```
Phase A (Remove Parallel)
  A1 ─► A2 ─► A3 ─► A4 ─► A5 ─► A6
                    │
                    ▼
Phase B (Settings Infrastructure)
  B1 ─────────────► B2 ─► B3 ─► B4
                              │
                              ▼
Phase C (GUI Integration)
  C1 ─────────────────────────► C2
                                │
                                ▼
Phase D (Pipeline + Polish)
  D1 ─────────────────────────► D2
                                │
                                ▼
Phase E (Validation)
  Full Test Suite
```

---

## Testing Strategy

| Phase | Test Type | Key Tests |
|-------|-----------|-----------|
| A3-A5 | Unit + Integration | Sequential extraction produces consistent results |
| B1 | Type checking | mypy strict mode passes |
| B2 | Unit | Default values correct, ranges valid |
| B3-B4 | Unit | Validation logic, path generation, file I/O |
| C1 | Integration | Existing behavior unchanged |
| C2 | Manual/GUI | Tab navigation, control interactions |
| D1 | Integration | Settings flow through pipeline |
| D2 | E2E | Full workflow with custom settings |

---

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| Breaking extraction during parallel removal | A5 has comprehensive consistency tests |
| Breaking existing GUI behavior | C1 has extensive regression tests |
| Settings file corruption | Graceful fallback to defaults with warning |
| Thread safety in SettingsManager | Use threading.Lock for concurrent access |
| Cross-platform path issues | Test on WSL, Windows (if available) |

---

## Rollback Plan

If issues arise at any phase:

```bash
# Phase A rollback
git checkout -- app/core/extractor.py app/core/types.py
git checkout -- app/tests/core/extractor/test_extractor_parallel.py

# Phase B-D rollback (if settings infrastructure breaks)
git checkout -- app/core/types.py app/core/constants.py
rm -f app/core/settings.py app/core/settings_window.py
git checkout -- app/main.py
```

---

## Expected Outcomes

| Metric | Before | After |
|--------|--------|-------|
| Lines in extractor.py | ~1600 | ~1540 (60 fewer - parallel removed) |
| Lines in types.py | 291 | ~295 (BlockAnalysisResult removed, AppSettings added) |
| Thread safety risks | Medium | None |
| Code complexity | Higher | Lower (simpler extraction loop) |
| Settings persistence | None | Full JSON persistence |
| UI configurability | Limited | Full Advanced Settings modal |
| Total new files | 0 | 2 (settings.py, settings_window.py) |

---

## Next Steps

1. **Begin Phase A1** - Remove parallel imports from extractor.py
2. **Complete Phase A** (A1-A6) before starting Phase B
3. **Phase B** builds settings infrastructure
4. **Phase C** integrates with main GUI
5. **Phase D** wires settings through pipeline
6. **Phase E** validates full implementation
7. Commit changes with detailed message referencing this plan
