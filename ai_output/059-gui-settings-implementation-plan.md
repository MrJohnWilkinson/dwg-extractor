# GUI Settings Implementation Plan

## Executive Summary

This plan provides a sequenced implementation roadmap for the Advanced Settings window described in `ai_output/058-gui-settings-architecture-report.md`. The implementation is organized into 8 units following a dependency-driven sequence, ensuring each unit builds on prior work. Total scope covers data models, SettingsManager class, JSON persistence, Advanced Settings modal window, and pipeline integration.

## Table Summary

| Unit | Name | Dependencies | Files Modified/Created | Testing Focus |
|------|------|--------------|------------------------|---------------|
| 1 | Data Models | None | `types.py` | Type validation |
| 2 | Default Values Registry | Unit 1 | `constants.py` | Default lookups |
| 3 | SettingsManager Class | Units 1-2 | `settings.py` (new) | Load/save/validate |
| 4 | Platform-Specific Paths | Unit 3 | `settings.py` | Cross-platform paths |
| 5 | Main GUI Migration | Units 1-4 | `main.py` | Existing behavior preserved |
| 6 | Advanced Settings Window | Units 1-5 | `settings_window.py` (new) | Tab navigation, controls |
| 7 | Pipeline Integration | Units 1-6 | `extractor.py`, `geometry.py` | Settings propagation |
| 8 | Polish & Persistence | Units 1-7 | `settings_window.py`, `main.py` | Save as Default, Reset |

## Scope Definition

### In Scope

- **AppSettings TypedDict** with all 25 configurable fields from architecture report
- **SettingsManager class** for centralized settings access and validation
- **JSON persistence** using platform-specific config directories
- **Advanced Settings CTkToplevel modal** with 5 tabs (Filters, Performance, Precision, Output, Logging)
- **Migration of existing GUI controls** to use SettingsManager
- **Pipeline integration** to pass configurable thresholds to extractor and geometry modules
- **Per-section Reset buttons** and global "Save as Default" functionality
- **Input validation** with immediate visual feedback (red borders on invalid)
- **Unit tests** for SettingsManager and settings validation

### Out of Scope

- Cloud sync or remote storage of settings
- Multiple user profiles or preset management
- Settings import/export beyond JSON file location
- Undo/redo for settings changes
- Settings search or filtering within Advanced Settings window
- Migration from hypothetical older app versions
- Internationalization (i18n) of settings labels
- Accessibility (a11y) beyond standard CustomTkinter behavior

## Relevant Files

- **app/core/types.py** - Add AppSettings TypedDict and SettingsValidation types
- **app/core/constants.py** - Add default value registries for new settings (performance, precision)
- **app/core/settings.py** (new) - SettingsManager class with load/save/validate methods
- **app/main.py** - Refactor to use SettingsManager, add "Advanced Settings" button
- **app/core/settings_window.py** (new) - AdvancedSettingsWindow CTkToplevel modal
- **app/core/extractor.py** - Accept configurable thresholds via settings parameter
- **app/core/geometry.py** - Accept configurable precision values via parameters
- **app/tests/core/test_settings.py** (new) - Unit tests for SettingsManager

---

## Unit 1: Data Models

### Purpose
Define TypedDict structures for type-safe settings throughout the application.

### Implementation Steps

1. Add `AppSettings` TypedDict to `app/core/types.py`:
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

       # Performance (new)
       polygon_count_threshold: int
       line_segment_threshold: int
       entity_count_threshold: int
       max_worker_threads: int

       # Precision (new)
       arc_flattening_sagitta: float
       coord_dedup_epsilon: float
       rotation_tolerance: float

       # Output (new)
       output_directory: str | None
       auto_open_excel: bool
       show_success_dialog: bool
       filename_prefix: str
       include_timestamp: bool

       # Logging (existing, formalized)
       generate_log_file: bool
       file_log_level: str
       log_viewer_level: str
       log_viewer_auto_scroll: bool
       log_viewer_max_lines: int
   ```

2. Add `SettingValidation` TypedDict for validation metadata:
   ```python
   class SettingValidation(TypedDict):
       min_value: float | int | None
       max_value: float | int | None
       default: float | int | bool | str | None
       unit_aware: bool
   ```

### Acceptance Criteria
- [ ] `AppSettings` TypedDict defined with all 25 fields
- [ ] `SettingValidation` TypedDict defined
- [ ] mypy passes with no errors
- [ ] Existing tests still pass

---

## Unit 2: Default Values Registry

### Purpose
Centralize all default values and validation ranges in constants.py.

### Implementation Steps

1. Add performance threshold defaults to `app/core/constants.py`:
   ```python
   DEFAULT_POLYGON_COUNT_THRESHOLD: int = 500
   DEFAULT_LINE_SEGMENT_THRESHOLD: int = 5000
   DEFAULT_ENTITY_COUNT_THRESHOLD: int = 1000
   DEFAULT_MAX_WORKER_THREADS: int = 8

   POLYGON_COUNT_THRESHOLD_MIN: int = 100
   POLYGON_COUNT_THRESHOLD_MAX: int = 10000
   LINE_SEGMENT_THRESHOLD_MIN: int = 1000
   LINE_SEGMENT_THRESHOLD_MAX: int = 50000
   ENTITY_COUNT_THRESHOLD_MIN: int = 100
   ENTITY_COUNT_THRESHOLD_MAX: int = 10000
   MAX_WORKER_THREADS_MIN: int = 1
   MAX_WORKER_THREADS_MAX: int = 32
   ```

2. Add precision setting defaults:
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

3. Add output setting defaults:
   ```python
   DEFAULT_AUTO_OPEN_EXCEL: bool = True
   DEFAULT_SHOW_SUCCESS_DIALOG: bool = True
   DEFAULT_INCLUDE_TIMESTAMP: bool = True
   DEFAULT_FILENAME_PREFIX: str = ""
   ```

4. Add logging setting defaults:
   ```python
   DEFAULT_LOG_VIEWER_LEVEL: str = "INFO"
   DEFAULT_LOG_VIEWER_AUTO_SCROLL: bool = True
   DEFAULT_LOG_VIEWER_MAX_LINES: int = 1000
   ```

5. Create `SETTINGS_VALIDATION_REGISTRY` dictionary mapping setting names to validation metadata.

### Acceptance Criteria
- [ ] All 25 settings have defaults defined
- [ ] All numeric settings have min/max ranges defined
- [ ] `SETTINGS_VALIDATION_REGISTRY` maps each setting to its validation metadata
- [ ] Existing hardcoded values in extractor.py and geometry.py documented for removal

---

## Unit 3: SettingsManager Class

### Purpose
Create centralized settings management with validation and type safety.

### Implementation Steps

1. Create `app/core/settings.py` with `SettingsManager` class:
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

2. Implement validation logic using `SETTINGS_VALIDATION_REGISTRY`.

3. Implement unit-aware default lookups for filter settings.

### Acceptance Criteria
- [ ] SettingsManager instantiates without errors
- [ ] `get()` returns default when setting not explicitly set
- [ ] `set()` validates and rejects out-of-range values
- [ ] `validate()` provides helpful error messages
- [ ] `get_default()` handles unit-aware settings correctly
- [ ] `reset_section()` resets only settings in specified section
- [ ] Unit tests cover all public methods

---

## Unit 4: Platform-Specific Paths

### Purpose
Implement cross-platform settings file location following OS conventions.

### Implementation Steps

1. Add path resolution to `SettingsManager.__init__()`:
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

2. Implement `load()` and `save()` methods:
   ```python
   def load(self) -> bool:
       """Load settings from JSON file. Returns True if file existed."""

   def save(self) -> bool:
       """Save settings to JSON file. Returns True on success."""
   ```

3. Create config directory if it doesn't exist on first save.

4. Handle JSON decode errors gracefully (fall back to defaults).

### Acceptance Criteria
- [ ] Config path follows platform conventions (APPDATA, XDG_CONFIG_HOME, etc.)
- [ ] `load()` handles missing file gracefully (returns defaults)
- [ ] `load()` handles corrupted JSON gracefully (returns defaults with warning)
- [ ] `save()` creates parent directories if needed
- [ ] Settings persist across application restarts

---

## Unit 5: Main GUI Migration

### Purpose
Migrate existing main.py settings to use SettingsManager without changing user-visible behavior.

### Implementation Steps

1. Add SettingsManager instance to `DXFExtractorApp.__init__()`:
   ```python
   self.settings = SettingsManager()
   self.settings.load()
   ```

2. Initialize GUI control variables from SettingsManager:
   ```python
   self.precision_fix_var = ctk.BooleanVar(
       value=self.settings.get("precision_fix_enabled")
   )
   ```

3. Update getter methods to delegate to SettingsManager:
   ```python
   def _get_precision_fix_amount(self) -> float | None:
       if not self.precision_fix_var.get():
           return None
       amount = float(self.precision_fix_amount_var.get())
       valid, _ = self.settings.validate("precision_fix_amount", amount)
       return amount if valid else None
   ```

4. Add "Advanced Settings" button to main window:
   ```python
   self.advanced_settings_button = ctk.CTkButton(
       button_frame,
       text="Settings",
       width=80,
       command=self._open_advanced_settings,
   )
   ```

5. Ensure all existing functionality works identically.

### Acceptance Criteria
- [ ] Existing filter controls function identically to before
- [ ] Default values populate from SettingsManager
- [ ] Validation uses SettingsManager.validate()
- [ ] "Settings" button visible in main window
- [ ] No visual changes to existing UI layout
- [ ] All existing tests pass

---

## Unit 6: Advanced Settings Window

### Purpose
Create tabbed modal window for advanced settings configuration.

### Implementation Steps

1. Create `app/core/settings_window.py` with `AdvancedSettingsWindow` class:
   ```python
   class AdvancedSettingsWindow(ctk.CTkToplevel):
       """Modal window for advanced settings configuration."""

       def __init__(self, parent: ctk.CTk, settings: SettingsManager) -> None:
           """Initialize with parent window and settings manager."""
   ```

2. Implement tab structure using `CTkTabview`:
   - Filters tab (move existing controls here, add descriptions)
   - Performance tab (polygon/line/entity thresholds, worker threads)
   - Precision tab (arc sagitta, epsilon, rotation tolerance)
   - Output tab (directory, auto-open, filename format)
   - Logging tab (viewer settings, file logging)

3. Implement control creation pattern:
   ```python
   def _create_numeric_setting(
       self,
       parent: ctk.CTkFrame,
       label: str,
       description: str,
       variable: ctk.StringVar,
       range_text: str,
   ) -> ctk.CTkFrame:
       """Create standard numeric setting control with label, entry, description."""
   ```

4. Implement per-section reset buttons:
   ```python
   def _reset_filters(self) -> None:
       """Reset filter settings to defaults for current unit."""
   ```

5. Implement Apply/Cancel/Save as Default buttons:
   ```python
   def _apply_settings(self) -> None:
       """Validate and apply settings to SettingsManager (session only)."""

   def _save_as_default(self) -> None:
       """Apply settings and persist to JSON file."""

   def _cancel(self) -> None:
       """Close window without applying changes."""
   ```

6. Implement validation feedback (red border on invalid entry).

### Acceptance Criteria
- [ ] Window opens as modal (blocks main window)
- [ ] All 5 tabs render correctly
- [ ] Each setting has label, entry/control, description, and valid range shown
- [ ] Per-section Reset buttons restore section defaults
- [ ] Apply button validates and closes window
- [ ] Cancel button closes without changes
- [ ] Save as Default persists to JSON
- [ ] Invalid entries show red border with validation message

---

## Unit 7: Pipeline Integration

### Purpose
Wire configurable settings through extraction and geometry processing pipelines.

### Implementation Steps

1. Update `extract_blocks()` signature in `app/core/extractor.py`:
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
       # New parameters
       polygon_count_threshold: int | None = None,
       line_segment_threshold: int | None = None,
       entity_count_threshold: int | None = None,
       max_worker_threads: int | None = None,
   ) -> ExtractionResult:
   ```

2. Replace hardcoded `max_workers = 8` with parameter:
   ```python
   max_workers = max_worker_threads or DEFAULT_MAX_WORKER_THREADS
   max_workers = min(max_workers, max(1, len(block_defs_list)))
   ```

3. Pass thresholds to geometry functions where currently hardcoded.

4. Update `_get_intersection_points()` in `app/core/geometry.py` to accept epsilon:
   ```python
   def _get_intersection_points(
       block_def: BlockLayout,
       epsilon: float = DEFAULT_COORD_DEDUP_EPSILON,
   ) -> tuple[list[float], list[float]]:
   ```

5. Update `_categorize_rotation()` to accept tolerance:
   ```python
   def _categorize_rotation(
       angle: float,
       tolerance: float = DEFAULT_ROTATION_TOLERANCE,
   ) -> str:
   ```

6. Update main.py extraction call to pass settings:
   ```python
   extraction_result = extract_blocks(
       self.selected_file_path,
       self.abort_event,
       # ... existing params ...
       polygon_count_threshold=self.settings.get("polygon_count_threshold"),
       line_segment_threshold=self.settings.get("line_segment_threshold"),
       entity_count_threshold=self.settings.get("entity_count_threshold"),
       max_worker_threads=self.settings.get("max_worker_threads"),
   )
   ```

### Acceptance Criteria
- [ ] All configurable thresholds flow from settings to processing code
- [ ] Default values used when settings not explicitly set
- [ ] Existing behavior unchanged when using defaults
- [ ] Performance tests confirm thresholds are respected
- [ ] Tests verify settings propagation

---

## Unit 8: Polish & Persistence

### Purpose
Final integration, save/load behavior, and edge case handling.

### Implementation Steps

1. Implement output directory functionality:
   ```python
   def _get_output_path(self, input_path: Path) -> Path:
       """Get output file path respecting output directory setting."""
       custom_dir = self.settings.get("output_directory")
       if custom_dir:
           return Path(custom_dir) / self._format_filename(input_path)
       return input_path.parent / self._format_filename(input_path)
   ```

2. Implement filename formatting:
   ```python
   def _format_filename(self, input_path: Path) -> str:
       """Format output filename with prefix and optional timestamp."""
       prefix = self.settings.get("filename_prefix")
       include_ts = self.settings.get("include_timestamp")
       # Build filename: {stem}_{prefix}_{timestamp}.xlsx
   ```

3. Implement auto-open toggle:
   ```python
   if self.settings.get("auto_open_excel"):
       self._open_excel_file(excel_path)
   ```

4. Implement success dialog toggle:
   ```python
   if self.settings.get("show_success_dialog"):
       messagebox.showinfo(...)
   ```

5. Add settings migration for future versions (version field in JSON).

6. Add error recovery for corrupted settings file.

7. Implement filename preview in Output tab of Advanced Settings.

### Acceptance Criteria
- [ ] Custom output directory is used when configured
- [ ] Filename prefix and timestamp settings work correctly
- [ ] Auto-open Excel respects setting
- [ ] Success dialog respects setting
- [ ] Settings file includes version for future migration
- [ ] Corrupted settings file handled gracefully
- [ ] Filename preview updates live in Output tab

---

## Implementation Sequence Diagram

```
Unit 1 ──────────────────────────────────────────────────────────────►
        ▼
Unit 2 ──────────────────────────────────────────────────────────────►
        │     ▼
        └────► Unit 3 ───────────────────────────────────────────────►
                      ▼
              Unit 4 ─────────────────────────────────────────────────►
                      │     ▼
                      └────► Unit 5 ──────────────────────────────────►
                                    ▼
                            Unit 6 ───────────────────────────────────►
                                    │     ▼
                                    └────► Unit 7 ────────────────────►
                                                  ▼
                                          Unit 8 ─────────────────────►
```

## Testing Strategy

| Unit | Test Type | Key Tests |
|------|-----------|-----------|
| 1 | Type checking | mypy strict mode passes |
| 2 | Unit | Default values correct, ranges valid |
| 3 | Unit | Validation logic, type coercion, error messages |
| 4 | Unit | Path generation per platform, file I/O |
| 5 | Integration | Existing behavior unchanged |
| 6 | Manual/GUI | Tab navigation, control interactions |
| 7 | Integration | Settings flow through pipeline |
| 8 | E2E | Full workflow with custom settings |

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| Breaking existing GUI behavior | Unit 5 has extensive regression tests |
| Settings file corruption | Graceful fallback to defaults with warning |
| Thread safety in SettingsManager | Use threading.Lock for concurrent access |
| Performance regression from parameterization | Benchmark before/after |
| Cross-platform path issues | CI tests on Windows/Linux/macOS |

## Next Steps

1. Begin with Unit 1 (Data Models) - foundation for all subsequent work
2. Implement Units 2-4 before touching main.py (minimize risk)
3. Unit 5 (Main GUI Migration) is the critical risk point - test thoroughly
4. Units 6-8 add new functionality on solid foundation
