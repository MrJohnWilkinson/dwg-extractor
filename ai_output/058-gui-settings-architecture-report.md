# GUI Settings Architecture Report

## Executive Summary

This report analyzes the DXF Block Extractor's current settings architecture and proposes a comprehensive Advanced Settings window. The application currently exposes 6 user-configurable settings in the main GUI while 10+ performance and precision thresholds remain hardcoded. Implementing an Advanced Settings panel would provide power users with full control while maintaining simplicity for typical use cases.

## Table Summary

| Setting Category | Setting Name | Current Location | Default Value | Unit-Aware | Validation Range | Priority |
|-----------------|--------------|------------------|---------------|------------|------------------|----------|
| **Filters** | Precision Fix Amount | GUI (main.py:86) | 3.0 (mm) | Yes | 0.0 - 10.0 | Exists |
| **Filters** | Gap Bridge Amount | GUI (main.py:89) | 3.0 (mm) | Yes | 0.0 - 10,000 | Exists |
| **Filters** | Min Area Filter | GUI (main.py:93) | 100,000 sq mm | Yes | 0.0 - 1,000,000 | Exists |
| **Filters** | Min Side Filter | GUI (main.py:97) | 10 mm | Yes | 0.0 - 100,000 | Exists |
| **Units** | Unit Override | GUI (main.py:85) | Auto-detect | N/A | MM/CM/M/IN/FT | Exists |
| **Logging** | Log File Generation | GUI (main.py:100) | Disabled | N/A | Boolean | Exists |
| **Performance** | Polygon Count Threshold | constants.py:162 | 500 | No | 100 - 10,000 | High |
| **Performance** | Line Segment Threshold | constants.py:168 | 5,000 | No | 1,000 - 50,000 | High |
| **Performance** | Entity Count Threshold | constants.py:174 | 1,000 | No | 100 - 10,000 | High |
| **Performance** | Max Thread Workers | extractor.py:1301 | 8 | No | 1 - 32 | Medium |
| **Precision** | Arc Flattening Sagitta | constants.py:181 | 0.1 | Yes | 0.01 - 1.0 | Medium |
| **Precision** | Coord Dedup Epsilon | geometry.py:288 | 0.01 | No | 0.001 - 1.0 | Low |
| **Precision** | Rotation Tolerance | geometry.py:428 | 1.0 deg | No | 0.1 - 5.0 | Low |
| **Output** | Output Directory | N/A (uses input dir) | Same as input | N/A | Valid path | Medium |
| **Output** | Auto-open Excel | N/A (always on) | True | N/A | Boolean | Low |

## Relevant Files

- **app/core/constants.py** - Contains all hardcoded thresholds, filter defaults, and validation ranges. This is the single source of truth for default values.
- **app/main.py** - GUI implementation with current settings controls. Contains validation logic and event handlers for existing settings.
- **app/core/extractor.py** - Extraction logic that consumes settings. Shows how settings are passed through the extraction pipeline.
- **app/core/geometry.py** - Geometry processing with hardcoded precision values. Contains thresholds for content zone detection.
- **app/core/types.py** - TypedDict definitions that could be extended for settings configuration.

## Current Settings Architecture

### Existing GUI Controls (main.py lines 84-101)

```
Unit Selection:     [DXF/DWG dropdown]  (applies to all numeric filters)
                    ----------------------------------------
Precision Fix:      [x] Enabled         Amount: [3.0    ]
                    ----------------------------------------
Gap Bridge:         [ ] Enabled         Amount: [3.0    ]
                    ----------------------------------------
Min Area Filter:    [ ] Enabled         Amount: [100000 ]
                    ----------------------------------------
Min Side Filter:    [ ] Enabled         Amount: [10.0   ]
                    ----------------------------------------
Log File:           [ ] Generate        Level:  [DEBUG dropdown]
```

### Pattern Analysis

The current GUI uses a consistent pattern for filter settings:
1. **Checkbox** to enable/disable the feature
2. **Entry field** for numeric amount (disabled when checkbox unchecked)
3. **Unit-aware defaults** that update when unit dropdown changes
4. **Validation** via getter methods with range checking

## Proposed Advanced Settings Window

### ASCII Layout Diagram

```
+===========================================================================+
|                        ADVANCED SETTINGS                              [X] |
+===========================================================================+
|  [ FILTERS ]  [ PERFORMANCE ]  [ PRECISION ]  [ OUTPUT ]  [ LOGGING ]     |
+---------------------------------------------------------------------------+
|                                                                           |
|  FILTER SETTINGS                                                          |
|  ---------------                                                          |
|                                                                           |
|  Unit System:  [MM   v]  (affects all filter defaults below)              |
|                                                                           |
|  +---------------------------------------------------------------+        |
|  | PRECISION FIX                                                 |        |
|  | [x] Enable    Amount: [  3.0  ] mm   Range: 0.0 - 10.0        |        |
|  | Fixes floating-point artifacts at line endpoints              |        |
|  +---------------------------------------------------------------+        |
|                                                                           |
|  +---------------------------------------------------------------+        |
|  | GAP BRIDGE                                                    |        |
|  | [ ] Enable    Amount: [  3.0  ] mm   Range: 0.0 - 10,000      |        |
|  | Bridges intentional small gaps in drawings                    |        |
|  | Note: Mutually exclusive with Precision Fix                   |        |
|  +---------------------------------------------------------------+        |
|                                                                           |
|  +---------------------------------------------------------------+        |
|  | MIN AREA FILTER                                               |        |
|  | [ ] Enable    Amount: [100000 ] sq mm   Range: 0 - 1,000,000  |        |
|  | Filters polygons with net area below threshold                |        |
|  +---------------------------------------------------------------+        |
|                                                                           |
|  +---------------------------------------------------------------+        |
|  | MIN SIDE FILTER                                               |        |
|  | [ ] Enable    Amount: [  10.0 ] mm   Range: 0 - 100,000       |        |
|  | Filters polygons with shortest side below threshold           |        |
|  +---------------------------------------------------------------+        |
|                                                                           |
|  [Reset Filters to Defaults]                                              |
|                                                                           |
+---------------------------------------------------------------------------+
|                  [Apply]    [Cancel]    [Save as Default]                 |
+===========================================================================+


+===========================================================================+
|  [ FILTERS ]  [*PERFORMANCE*]  [ PRECISION ]  [ OUTPUT ]  [ LOGGING ]     |
+---------------------------------------------------------------------------+
|                                                                           |
|  PERFORMANCE THRESHOLDS                                                   |
|  ----------------------                                                   |
|                                                                           |
|  These thresholds control when expensive geometry operations are skipped. |
|  Lower values = faster processing, but may skip content zone detection.   |
|  Higher values = more thorough analysis, but slower on complex drawings.  |
|                                                                           |
|  +---------------------------------------------------------------+        |
|  | POLYGON COUNT THRESHOLD                         [    500    ] |        |
|  | Max polygons for net area calculation                         |        |
|  | Range: 100 - 10,000   Default: 500                            |        |
|  +---------------------------------------------------------------+        |
|                                                                           |
|  +---------------------------------------------------------------+        |
|  | LINE SEGMENT THRESHOLD                          [   5000    ] |        |
|  | Max LINE segments for cycle detection                         |        |
|  | Range: 1,000 - 50,000   Default: 5,000                        |        |
|  +---------------------------------------------------------------+        |
|                                                                           |
|  +---------------------------------------------------------------+        |
|  | ENTITY COUNT THRESHOLD                          [   1000    ] |        |
|  | Max entities for content zone analysis                        |        |
|  | Range: 100 - 10,000   Default: 1,000                          |        |
|  +---------------------------------------------------------------+        |
|                                                                           |
|  +---------------------------------------------------------------+        |
|  | PARALLEL PROCESSING                                           |        |
|  | Max Worker Threads: [   8   ]   Range: 1 - 32                 |        |
|  | Recommended: Number of CPU cores (auto-detect: 8)             |        |
|  +---------------------------------------------------------------+        |
|                                                                           |
|  [Reset Performance to Defaults]                                          |
|                                                                           |
+---------------------------------------------------------------------------+


+===========================================================================+
|  [ FILTERS ]  [ PERFORMANCE ]  [*PRECISION*]  [ OUTPUT ]  [ LOGGING ]     |
+---------------------------------------------------------------------------+
|                                                                           |
|  PRECISION SETTINGS                                                       |
|  ------------------                                                       |
|                                                                           |
|  These settings control geometric precision and tolerance values.         |
|                                                                           |
|  +---------------------------------------------------------------+        |
|  | ARC FLATTENING SAGITTA                          [   0.1    ] |        |
|  | Max distance from arc to chord during flattening              |        |
|  | Smaller = more precise, more segments                         |        |
|  | Range: 0.01 - 1.0   Default: 0.1                              |        |
|  +---------------------------------------------------------------+        |
|                                                                           |
|  +---------------------------------------------------------------+        |
|  | COORDINATE DEDUPLICATION EPSILON                [   0.01   ] |        |
|  | Tolerance for merging nearby intersection points              |        |
|  | Range: 0.001 - 1.0   Default: 0.01                            |        |
|  +---------------------------------------------------------------+        |
|                                                                           |
|  +---------------------------------------------------------------+        |
|  | ROTATION CATEGORIZATION TOLERANCE               [   1.0    ] deg        |
|  | Tolerance for categorizing rotations as 0/90/180/270          |        |
|  | Range: 0.1 - 5.0   Default: 1.0                               |        |
|  +---------------------------------------------------------------+        |
|                                                                           |
|  [Reset Precision to Defaults]                                            |
|                                                                           |
+---------------------------------------------------------------------------+


+===========================================================================+
|  [ FILTERS ]  [ PERFORMANCE ]  [ PRECISION ]  [*OUTPUT*]  [ LOGGING ]     |
+---------------------------------------------------------------------------+
|                                                                           |
|  OUTPUT SETTINGS                                                          |
|  ---------------                                                          |
|                                                                           |
|  +---------------------------------------------------------------+        |
|  | OUTPUT DIRECTORY                                              |        |
|  | ( ) Same as input file (default)                              |        |
|  | ( ) Custom directory:                                         |        |
|  |     [C:\Users\John\Documents\DXF_Exports     ] [Browse...]    |        |
|  +---------------------------------------------------------------+        |
|                                                                           |
|  +---------------------------------------------------------------+        |
|  | POST-EXTRACTION BEHAVIOR                                      |        |
|  | [x] Auto-open Excel file after extraction                     |        |
|  | [x] Show success dialog                                       |        |
|  +---------------------------------------------------------------+        |
|                                                                           |
|  +---------------------------------------------------------------+        |
|  | FILENAME FORMAT                                               |        |
|  | Prefix: [                ] (optional)                         |        |
|  | Include timestamp: [x]                                        |        |
|  | Preview: FILENAME_prefix_20251211_143052.xlsx                 |        |
|  +---------------------------------------------------------------+        |
|                                                                           |
|  [Reset Output to Defaults]                                               |
|                                                                           |
+---------------------------------------------------------------------------+


+===========================================================================+
|  [ FILTERS ]  [ PERFORMANCE ]  [ PRECISION ]  [ OUTPUT ]  [*LOGGING*]     |
+---------------------------------------------------------------------------+
|                                                                           |
|  LOGGING SETTINGS                                                         |
|  ----------------                                                         |
|                                                                           |
|  +---------------------------------------------------------------+        |
|  | LOG VIEWER                                                    |        |
|  | Display Level: [INFO      v]                                  |        |
|  | [x] Auto-scroll to latest                                     |        |
|  | [ ] Word wrap long lines                                      |        |
|  | Max lines in buffer: [  1000  ]                               |        |
|  +---------------------------------------------------------------+        |
|                                                                           |
|  +---------------------------------------------------------------+        |
|  | FILE LOGGING                                                  |        |
|  | [x] Generate log file during extraction                       |        |
|  | File Level: [DEBUG     v]                                     |        |
|  | Log location: Same directory as Excel output                  |        |
|  +---------------------------------------------------------------+        |
|                                                                           |
|  [Reset Logging to Defaults]                                              |
|                                                                           |
+---------------------------------------------------------------------------+
```

## Implementation Recommendations

### 1. Settings Data Model

Create a new TypedDict for all configurable settings:

```python
class AppSettings(TypedDict):
    # Filters
    unit_override: int | None
    precision_fix_enabled: bool
    precision_fix_amount: float | None
    gap_bridge_enabled: bool
    gap_bridge_amount: float | None
    min_area_filter_enabled: bool
    min_area_filter_amount: float | None
    min_side_filter_enabled: bool
    min_side_filter_amount: float | None

    # Performance
    polygon_count_threshold: int
    line_segment_threshold: int
    entity_count_threshold: int
    max_worker_threads: int

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
    log_viewer_level: str
    log_viewer_auto_scroll: bool
    log_viewer_word_wrap: bool
    log_viewer_max_lines: int
    generate_log_file: bool
    file_log_level: str
```

### 2. Settings Persistence

Store settings in a JSON file in the application directory:

```
~/.dxf-extractor/settings.json
```

Or use platform-appropriate locations:
- Windows: `%APPDATA%\DXFExtractor\settings.json`
- Linux: `~/.config/dxf-extractor/settings.json`
- macOS: `~/Library/Application Support/DXFExtractor/settings.json`

### 3. Validation Strategy

| Setting Type | Validation Approach |
|-------------|---------------------|
| Numeric (int) | Range check with min/max, type coercion |
| Numeric (float) | Range check, handle scientific notation |
| Boolean | Direct checkbox state |
| Path | Validate exists, is writable |
| Dropdown | Restrict to predefined values |

### 4. Unit-Aware Defaults

Extend the existing pattern in constants.py:

```python
DEFAULT_ARC_FLATTENING_SAGITTA: dict[int, float] = {
    0: 0.1,    # Unitless
    1: 0.004,  # Inches
    2: 0.0003, # Feet
    4: 0.1,    # Millimeters
    5: 0.01,   # Centimeters
    6: 0.0001, # Meters
}
```

## GUI Best Practices Applied

1. **Progressive Disclosure** - Basic settings in main window, advanced in modal
2. **Grouped Organization** - Tab-based categorization
3. **Inline Help** - Descriptions below each setting with valid ranges
4. **Live Preview** - Show effects where applicable (filename preview)
5. **Reset Options** - Per-section and global reset buttons
6. **Mutual Exclusivity** - Visual indication when settings conflict
7. **Validation Feedback** - Immediate red border on invalid input
8. **Save Options** - Apply for session vs. Save as Default

## Next Steps

1. **Phase 1**: Move existing main.py settings to dedicated SettingsManager class
2. **Phase 2**: Create AdvancedSettingsWindow as CTkToplevel modal
3. **Phase 3**: Add settings persistence with JSON file
4. **Phase 4**: Expose performance thresholds in GUI
5. **Phase 5**: Add output customization options
6. **Phase 6**: Implement "Save as Default" functionality
