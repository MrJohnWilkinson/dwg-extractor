# Precision Tolerance GUI Implementation Plan

## Executive Summary

This plan addresses the precision error issue where coordinate errors of ~0.0003 units exceed the current 1e-6 precision fix tolerance, causing incorrect polygon counts. The solution increases default tolerance to 0.01mm and adds user-configurable tolerance settings with clean GUI separation between units, precision fix, and gap bridge settings.

## Table Summary

| Unit | Code | Current Precision | New Default Precision | Gap Bridge Default |
|------|------|-------------------|----------------------|-------------------|
| Millimeters (MM) | 4 | 1e-6 (0.000001) | 0.01 | 0.5 |
| Centimeters (CM) | 5 | 1e-5 (0.00001) | 0.001 | 0.05 |
| Meters (M) | 6 | 1e-4 (0.0001) | 0.00001 | 0.001 |
| Inches (IN) | 1 | 1e-6 (0.000001) | 0.0005 | 0.01 |
| Feet (FT) | 2 | 1e-5 (0.00001) | 0.00005 | 0.1 |
| Unitless | 0 | 1e-6 (0.000001) | 0.01 | 0.1 |

**Unit Conversion Notes:**
- 0.01mm = 0.001cm = 0.00001m (exact metric equivalence)
- 0.01mm x 0.0393701 = 0.000394" (metric to imperial conversion)
- 0.0005" (half a thousandth) is standard imperial tolerance (slightly larger than exact 0.01mm equivalent)
- 0.0005" / 12 = 0.000042' rounded to 0.00005' for feet

## Relevant Files

- **app/core/constants.py** - Contains `PRECISION_SNAP_TOLERANCE` dict and `DEFAULT_GAP_BRIDGE_TOLERANCE` dict. Must add `DEFAULT_PRECISION_FIX_TOLERANCE` dict with new values and update input constraints.
- **app/core/extractor.py** - Contains `get_snap_tolerances()` function that calculates tolerance values. Must update to accept custom precision amount parameter.
- **app/main.py** - Contains GUI with current single-row options layout. Must restructure to three rows with precision fix amount entry field.
- **app/core/geometry.py** - Contains `_detect_content_zone()` and `_extract_paint_bucket_regions()` that use the tolerances. No changes needed (already parameterized).

## Current Architecture

### Tolerance Flow
```
main.py (GUI)
    ├── precision_fix_var (bool) - checkbox enabled/disabled
    ├── gap_bridge_var (bool) - checkbox enabled/disabled
    └── gap_bridge_amount_var (str) - entry field value
            ↓
extractor.py::get_snap_tolerances()
    ├── Returns (precision_tolerance, gap_bridge_tolerance)
    └── Uses PRECISION_SNAP_TOLERANCE[unit_code] when precision_fix_enabled
            ↓
geometry.py::_detect_content_zone()
    └── Passes tolerances to _extract_paint_bucket_regions()
            ↓
geometry.py::_extract_paint_bucket_regions()
    ├── Stage 1: _snap_linestring_coords(precision_tolerance)
    └── Stage 2: snap(merged, merged, gap_bridge_tolerance)
```

### Current GUI Layout (Single Row)
```
┌──────────────────────────────────────────────────────────────────────┐
│ Units: [DXF/DWG ▼]  ☑ Precision Fix:  ☑ Gap Bridge: [100.0    ]     │
└──────────────────────────────────────────────────────────────────────┘
```

## Proposed GUI Layout (Three Rows)

```
┌──────────────────────────────────────────────────────────────────────┐
│                                                                      │
│  Units: [DXF/DWG ▼]  ← Applies to both precision fix and gap bridge │
│                                                                      │
│  ────────────────────────────────────────────────────────────────── │
│                                                                      │
│  ☑ Precision Fix     Amount: [0.01    ]  ← default varies by unit   │
│                                                                      │
│  ────────────────────────────────────────────────────────────────── │
│                                                                      │
│  ☐ Gap Bridge        Amount: [0.5     ]  ← default varies by unit   │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

## Implementation Steps

### Step 1: Update constants.py

Add new `DEFAULT_PRECISION_FIX_TOLERANCE` dict with increased tolerances:

```python
# Stage 1: Default precision fix tolerances (user-configurable)
# These fix floating-point artifacts AND small coordinate precision errors
# Values increased from nanometer scale to practical CAD tolerance scale
DEFAULT_PRECISION_FIX_TOLERANCE: dict[int, float] = {
    0: 0.01,     # Unitless: use mm-equivalent default
    1: 0.0005,   # Inches: 0.5 mils (half a thousandth)
    2: 0.00005,  # Feet: ~0.5 mils in feet
    4: 0.01,     # Millimeters: 0.01mm (10 micrometers)
    5: 0.001,    # Centimeters: 0.001cm = 0.01mm
    6: 0.00001,  # Meters: 0.00001m = 0.01mm
}

# Input constraints for precision fix amount
PRECISION_FIX_MIN: float = 0.0
PRECISION_FIX_MAX: float = 10.0
```

Keep existing `PRECISION_SNAP_TOLERANCE` as a fallback for backward compatibility (optional).

### Step 2: Update extractor.py

Modify `get_snap_tolerances()` signature to accept custom precision amount:

```python
def get_snap_tolerances(
    detected_units: int,
    override_units: int | None,
    gap_bridge_enabled: bool,
    gap_bridge_amount: float | None,
    precision_fix_enabled: bool = True,
    precision_fix_amount: float | None = None,  # NEW PARAMETER
) -> tuple[float, float]:
```

Update precision tolerance calculation:

```python
if precision_fix_enabled:
    if precision_fix_amount is not None and precision_fix_amount > 0:
        # Use user-specified amount
        precision_tolerance = precision_fix_amount
    else:
        # Use default for the effective unit
        precision_tolerance = DEFAULT_PRECISION_FIX_TOLERANCE.get(
            effective_units,
            DEFAULT_PRECISION_FIX_TOLERANCE.get(0, 0.01),  # Fallback
        )
else:
    precision_tolerance = 0.0
```

### Step 3: Update main.py GUI

#### 3.1 Add new instance variables

```python
# Add in __init__
self.precision_fix_amount_var = ctk.StringVar(value="0.01")
```

#### 3.2 Restructure _create_widgets()

Replace the single `options_frame` with three separate frames:

```python
# Units row (with explanatory label)
units_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
units_frame.pack(pady=(0, 10))

unit_label = ctk.CTkLabel(units_frame, text="Units:", font=ctk.CTkFont(size=12))
unit_label.pack(side="left", padx=(0, 5))

self.unit_dropdown = ctk.CTkOptionMenu(...)
self.unit_dropdown.pack(side="left", padx=(0, 10))

units_hint = ctk.CTkLabel(
    units_frame,
    text="(applies to precision fix and gap bridge)",
    font=ctk.CTkFont(size=10),
    text_color="gray"
)
units_hint.pack(side="left")

# Separator
separator1 = ctk.CTkFrame(self.main_frame, height=1, fg_color="gray50")
separator1.pack(fill="x", pady=5)

# Precision Fix row
precision_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
precision_frame.pack(pady=(5, 10))

self.precision_fix_checkbox = ctk.CTkCheckBox(
    precision_frame,
    text="Precision Fix",
    variable=self.precision_fix_var,
    command=self._on_precision_fix_toggle,
)
self.precision_fix_checkbox.pack(side="left", padx=(0, 15))

precision_amount_label = ctk.CTkLabel(precision_frame, text="Amount:")
precision_amount_label.pack(side="left", padx=(0, 5))

self.precision_fix_entry = ctk.CTkEntry(
    precision_frame,
    width=80,
    textvariable=self.precision_fix_amount_var,
)
self.precision_fix_entry.pack(side="left")

# Separator
separator2 = ctk.CTkFrame(self.main_frame, height=1, fg_color="gray50")
separator2.pack(fill="x", pady=5)

# Gap Bridge row
gap_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
gap_frame.pack(pady=(5, 10))

self.gap_bridge_checkbox = ctk.CTkCheckBox(
    gap_frame,
    text="Gap Bridge",
    variable=self.gap_bridge_var,
    command=self._on_gap_bridge_toggle,
)
self.gap_bridge_checkbox.pack(side="left", padx=(0, 15))

gap_amount_label = ctk.CTkLabel(gap_frame, text="Amount:")
gap_amount_label.pack(side="left", padx=(0, 5))

self.gap_bridge_entry = ctk.CTkEntry(
    gap_frame,
    width=80,
    textvariable=self.gap_bridge_amount_var,
    state="disabled",
)
self.gap_bridge_entry.pack(side="left")
```

#### 3.3 Add precision fix toggle handler

```python
def _on_precision_fix_toggle(self) -> None:
    """Handle precision fix checkbox toggle."""
    enabled = self.precision_fix_var.get()
    self.logger.debug(f"Precision fix toggled: {enabled}")

    if enabled:
        self.precision_fix_entry.configure(state="normal")
        self._update_precision_fix_default()
    else:
        self.precision_fix_entry.configure(state="disabled")
```

#### 3.4 Add precision fix default updater

```python
def _update_precision_fix_default(self) -> None:
    """Update precision fix amount to default for selected unit."""
    selection = self.unit_selection_var.get()
    insunits = UNIT_SELECTION_OPTIONS.get(selection, -1)
    effective_units = insunits if insunits != -1 else 4  # Default to mm
    default_amount = DEFAULT_PRECISION_FIX_TOLERANCE.get(effective_units, 0.01)
    self.precision_fix_amount_var.set(str(default_amount))
    self.logger.debug(f"Precision fix default updated to {default_amount}")
```

#### 3.5 Update unit change handler

```python
def _on_unit_change(self, value: str) -> None:
    """Handle unit dropdown selection change."""
    self.logger.debug(f"Unit selection changed to: {value}")
    # Update precision fix default if enabled
    if self.precision_fix_var.get():
        self._update_precision_fix_default()
    # Update gap bridge default if enabled
    if self.gap_bridge_var.get():
        self._update_gap_bridge_default()
```

#### 3.6 Add precision amount getter

```python
def _get_precision_fix_amount(self) -> float | None:
    """Get validated precision fix amount, or None if invalid/disabled."""
    if not self.precision_fix_var.get():
        return None
    try:
        amount = float(self.precision_fix_amount_var.get())
        if PRECISION_FIX_MIN <= amount <= PRECISION_FIX_MAX:
            return amount
        else:
            self.logger.warning(f"Precision fix amount {amount} out of range")
            return None
    except ValueError:
        self.logger.warning("Invalid precision fix amount")
        return None
```

#### 3.7 Update extraction worker call

```python
extraction_result = extract_blocks(
    self.selected_file_path,
    self.abort_event,
    unit_override=unit_override,
    gap_bridge_enabled=gap_bridge_enabled,
    gap_bridge_amount=gap_bridge_amount,
    precision_fix_enabled=precision_fix_enabled,
    precision_fix_amount=self._get_precision_fix_amount(),  # NEW
)
```

### Step 4: Update extract_blocks() signature

```python
def extract_blocks(
    file_path: str,
    abort_event: threading.Event | None = None,
    unit_override: int | None = None,
    gap_bridge_enabled: bool = False,
    gap_bridge_amount: float | None = None,
    precision_fix_enabled: bool = True,
    precision_fix_amount: float | None = None,  # NEW PARAMETER
) -> ExtractionResult:
```

Pass through to `get_snap_tolerances()`:

```python
precision_tolerance, gap_bridge_tolerance = get_snap_tolerances(
    detected_units,
    unit_override,
    gap_bridge_enabled,
    gap_bridge_amount,
    precision_fix_enabled,
    precision_fix_amount,  # NEW
)
```

### Step 5: Update Tests

Add tests for:
1. New tolerance defaults in constants
2. `get_snap_tolerances()` with custom precision amount
3. GUI precision fix entry behavior

## Recommendations

1. **Keep backward compatibility**: The `PRECISION_SNAP_TOLERANCE` dict can be retained as a reference but renamed to `LEGACY_PRECISION_SNAP_TOLERANCE` for clarity.

2. **Add tooltips**: Consider adding CTkToolTip (if using external package) or simple hover labels to explain what precision fix and gap bridge do.

3. **Validate on focus-out**: Add validation when the entry field loses focus to clamp values to valid range.

4. **Consider presets**: For future enhancement, add preset buttons like "Conservative", "Standard", "Aggressive" that set both tolerances.

## Next Steps

1. Implement constants.py changes
2. Update extractor.py with new parameter
3. Restructure main.py GUI layout
4. Update extract_blocks() signature
5. Add/update unit tests
6. Test with the Frysetorg block that exposed the issue (should now report 21 polygons with 0.01mm tolerance)
