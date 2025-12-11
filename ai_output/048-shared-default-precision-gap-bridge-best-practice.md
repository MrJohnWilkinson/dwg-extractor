# Shared Default Settings for Precision Fix and Gap Bridge: Best Practice Analysis

## Executive Summary
This report analyzes the best practice approach for sharing default tolerance values between Precision Fix and Gap Bridge features. The recommended solution is **Option 1: Shared Constant Dictionary** with values of 3mm for metric units and 0.125" (1/8 inch) for imperial units. Additionally, the Min Area Filter should default to 100,000 sq mm and the Min Side Filter should default to 10mm, with unit changes updating ALL filter values regardless of checkbox state.

## Table Summary

### Gap Closure Tolerance Defaults (Precision Fix / Gap Bridge)

| Unit | Code | Current Precision Fix | Current Gap Bridge | Proposed Shared Default | Notes |
|------|------|----------------------|-------------------|------------------------|-------|
| MM | 4 | 0.01 mm | 0.5 mm | **3.0 mm** | Base reference value |
| CM | 5 | 0.001 cm | 0.05 cm | **0.3 cm** | 3mm equivalent |
| M | 6 | 0.00001 m | 0.001 m | **0.003 m** | 3mm equivalent |
| IN | 1 | 0.0005 in | 0.01 in | **0.125 in** | 1/8 inch (≈3.175mm) |
| FT | 2 | 0.00005 ft | 0.1 ft | **0.0104 ft** | 1/8 inch in feet |
| Unitless | 0 | 0.01 | 0.1 | **3.0** | MM-equivalent default |

### Min Area Filter Defaults (NEW - 100,000 sq mm base)

| Unit | Code | Current Default | Proposed Default | Notes |
|------|------|-----------------|------------------|-------|
| MM | 4 | 100.0 sq mm | **100000.0 sq mm** | Base reference value |
| CM | 5 | 1.0 sq cm | **1000.0 sq cm** | 100000 sq mm = 1000 sq cm |
| M | 6 | 0.0001 sq m | **0.1 sq m** | 100000 sq mm = 0.1 sq m |
| IN | 1 | 0.01 sq in | **155.0 sq in** | ≈100000 sq mm |
| FT | 2 | 0.001 sq ft | **1.076 sq ft** | ≈100000 sq mm |
| Unitless | 0 | 100.0 | **100000.0** | MM-equivalent default |

### Min Side Filter Defaults (NEW - 10mm base)

| Unit | Code | Current Default | Proposed Default | Notes |
|------|------|-----------------|------------------|-------|
| MM | 4 | 10.0 mm | **10.0 mm** | Base reference value (unchanged) |
| CM | 5 | 1.0 cm | **1.0 cm** | 10mm = 1cm (unchanged) |
| M | 6 | 0.01 m | **0.01 m** | 10mm = 0.01m (unchanged) |
| IN | 1 | 0.5 in | **0.394 in** | ≈10mm (was 0.5in = 12.7mm) |
| FT | 2 | 0.05 ft | **0.0328 ft** | ≈10mm (was 0.05ft = 15.24mm) |
| Unitless | 0 | 10.0 | **10.0** | MM-equivalent default (unchanged) |

## Relevant Files

- **`app/core/constants.py`** (lines 198-309) - Contains separate default dictionaries that need consolidation and value updates
- **`app/main.py`** (lines 660-725) - Contains `_on_unit_change()` method that needs modification to update ALL values regardless of checkbox state
- **`app/tests/core/test_constants.py`** (lines 148-245) - Contains unit tests for tolerance constants that will need updates for new shared values
- **`app/core/geometry.py`** (lines 645-720) - Uses tolerances in `_extract_paint_bucket_regions()` - no changes needed, receives tolerance as parameter

## Recommended Solution: Option 1 - Shared Constant Dictionary

Create one dictionary used by both Precision Fix and Gap Bridge features:

```python
# Shared gap closure tolerance defaults for Precision Fix and Gap Bridge.
# Both features solve the same problem (closing small gaps for accurate polygon counts)
# using different algorithmic approaches, so they share the same default tolerance.
# Values: 3mm for metric systems, 0.125" (1/8 inch) for imperial systems.
DEFAULT_GAP_CLOSURE_TOLERANCE: dict[int, float] = {
    0: 3.0,      # Unitless: assume mm-equivalent
    1: 0.125,    # Inches: 1/8 inch (standard imperial fraction)
    2: 0.0104,   # Feet: 1/8 inch expressed in feet
    4: 3.0,      # Millimeters: 3mm (typical visible CAD gap)
    5: 0.3,      # Centimeters: 0.3cm = 3mm
    6: 0.003,    # Meters: 0.003m = 3mm
}
```

### Why Option 1 (Shared Dictionary) Over Option 2 (Base Value with Conversion)

| Criteria | Option 1: Shared Dictionary | Option 2: Conversion Function |
|----------|----------------------------|------------------------------|
| **Simplicity** | ✅ Direct lookup, no computation | ❌ Requires conversion logic |
| **Testability** | ✅ Values are explicit, easy to assert | ❌ Must test conversion accuracy |
| **Consistency** | ✅ Matches existing pattern in codebase | ❌ Introduces new pattern |
| **Precision** | ✅ No floating-point conversion errors | ❌ May accumulate rounding errors |
| **Maintainability** | ✅ Single place to update values | ❌ Two places (base + conversion) |

## Implementation Changes

### 1. Update `app/core/constants.py`

#### Remove/Replace Existing Dictionaries
```python
# Remove or deprecate:
# - DEFAULT_PRECISION_FIX_TOLERANCE
# - DEFAULT_GAP_BRIDGE_TOLERANCE

# Add new shared constant:
DEFAULT_GAP_CLOSURE_TOLERANCE: dict[int, float] = {
    0: 3.0,      # Unitless: assume mm-equivalent
    1: 0.125,    # Inches: 1/8 inch (standard imperial fraction ≈ 3.175mm)
    2: 0.0104,   # Feet: 1/8 inch expressed in feet (0.125/12)
    4: 3.0,      # Millimeters: 3mm (typical visible CAD gap)
    5: 0.3,      # Centimeters: 0.3cm = 3mm
    6: 0.003,    # Meters: 0.003m = 3mm
}
"""Shared default tolerance for gap closure features (Precision Fix and Gap Bridge).
Both features close small gaps for accurate polygon detection using different algorithms.
Values represent typical visible CAD gaps: 3mm for metric, 1/8 inch for imperial."""
```

#### Update Min Area Filter Defaults (100,000 sq mm base)
```python
DEFAULT_MIN_AREA_FILTER: dict[int, float] = {
    0: 100000.0,  # Unitless: assume mm-equivalent
    1: 155.0,     # Inches: ~155 sq in ≈ 100000 sq mm
    2: 1.076,     # Feet: ~1.076 sq ft ≈ 100000 sq mm
    4: 100000.0,  # Millimeters: 100000 sq mm (base reference)
    5: 1000.0,    # Centimeters: 1000 sq cm = 100000 sq mm
    6: 0.1,       # Meters: 0.1 sq m = 100000 sq mm
}
"""Default minimum area filter by unit code.
Base value: 100,000 sq mm. Polygons with area less than this are filtered out.
Unit equivalents: 100000 sq mm = 1000 sq cm = 0.1 sq m = ~155 sq in = ~1.076 sq ft"""
```

#### Update Min Side Filter Defaults (10mm base)
```python
DEFAULT_MIN_SIDE_FILTER: dict[int, float] = {
    0: 10.0,     # Unitless: assume mm-equivalent
    1: 0.394,    # Inches: ~0.394 in ≈ 10mm
    2: 0.0328,   # Feet: ~0.0328 ft ≈ 10mm
    4: 10.0,     # Millimeters: 10mm (base reference)
    5: 1.0,      # Centimeters: 1cm = 10mm
    6: 0.01,     # Meters: 0.01m = 10mm
}
"""Default minimum side filter by unit code.
Base value: 10mm. Polygons with shortest side less than this are filtered out.
Unit equivalents: 10mm = 1cm = 0.01m = ~0.394 in = ~0.0328 ft"""
```

### 2. Update `app/main.py`

#### Update Import Statement
```python
from core.constants import DEFAULT_GAP_CLOSURE_TOLERANCE  # was DEFAULT_PRECISION_FIX_TOLERANCE, DEFAULT_GAP_BRIDGE_TOLERANCE
```

#### Update `_update_precision_fix_default()` Method
```python
def _update_precision_fix_default(self) -> None:
    """Update precision fix amount to default for selected unit."""
    selection = self.unit_selection_var.get()
    insunits = UNIT_SELECTION_OPTIONS.get(selection, -1)
    effective_units = insunits if insunits != -1 else 4  # Default to mm
    default_amount = DEFAULT_GAP_CLOSURE_TOLERANCE.get(effective_units, 3.0)
    self.precision_fix_amount_var.set(str(default_amount))
```

#### Update `_update_gap_bridge_default()` Method
```python
def _update_gap_bridge_default(self) -> None:
    """Update gap bridge amount to default for selected unit."""
    selection = self.unit_selection_var.get()
    insunits = UNIT_SELECTION_OPTIONS.get(selection, -1)
    effective_units = insunits if insunits != -1 else 4  # Default to mm
    default_amount = DEFAULT_GAP_CLOSURE_TOLERANCE.get(effective_units, 3.0)
    self.gap_bridge_amount_var.set(str(default_amount))
```

#### **CRITICAL: Update `_on_unit_change()` to Update ALL Values Regardless of Checkbox State**

The current behavior only updates values for enabled checkboxes. The new behavior should update ALL filter values when units change, regardless of whether the checkbox is checked ON or OFF:

```python
def _on_unit_change(self, value: str) -> None:
    """Handle unit dropdown selection change.

    Updates ALL filter defaults when units change, regardless of checkbox state.
    This ensures users see appropriate values for their selected unit system
    whether or not a filter is currently enabled.
    """
    self.logger.debug(f"Unit selection changed to: {value}")
    # Always update all defaults when unit changes (regardless of checkbox state)
    self._update_precision_fix_default()
    self._update_gap_bridge_default()
    self._update_min_area_filter_default()
    self._update_min_side_filter_default()
```

#### Update Initial StringVar Values in `__init__`
```python
# In __init__, update initial values to match new defaults (MM):
self.precision_fix_amount_var = ctk.StringVar(value="3.0")      # was "0.01"
self.gap_bridge_amount_var = ctk.StringVar(value="3.0")          # was "100.0" or similar
self.min_area_filter_amount_var = ctk.StringVar(value="100000.0")  # was "100.0"
self.min_side_filter_amount_var = ctk.StringVar(value="10.0")      # unchanged
```

### 3. Update Tests in `app/tests/core/test_constants.py`

Update test assertions to validate new shared values:

```python
def test_default_gap_closure_tolerance_mm_value(self) -> None:
    """MM tolerance should be 3.0mm (typical visible CAD gap)."""
    assert DEFAULT_GAP_CLOSURE_TOLERANCE[4] == 3.0

def test_default_gap_closure_tolerance_inch_value(self) -> None:
    """Inch tolerance should be 0.125in (1/8 inch)."""
    assert DEFAULT_GAP_CLOSURE_TOLERANCE[1] == 0.125

def test_default_min_area_filter_mm_value(self) -> None:
    """MM area filter should be 100000 sq mm."""
    assert DEFAULT_MIN_AREA_FILTER[4] == 100000.0

def test_default_min_side_filter_mm_value(self) -> None:
    """MM side filter should be 10mm."""
    assert DEFAULT_MIN_SIDE_FILTER[4] == 10.0
```

## UI/UX Behavior Changes

### Current Behavior (INCORRECT)
When user changes units in dropdown:
- Only updates defaults for **enabled** features (checkboxes that are ON)
- Disabled features retain their previous unit's values

### New Behavior (CORRECT)
When user changes units in dropdown:
- Updates defaults for **ALL** features regardless of checkbox state
- Users see appropriate values for their selected unit system whether a filter is enabled or not
- This prevents confusion where a user enables a filter after changing units and sees a stale value from the previous unit system

## Summary of Changes

| Change | File | Description |
|--------|------|-------------|
| Add `DEFAULT_GAP_CLOSURE_TOLERANCE` | constants.py | New shared dictionary (3mm / 0.125") |
| Remove `DEFAULT_PRECISION_FIX_TOLERANCE` | constants.py | Replaced by shared constant |
| Remove `DEFAULT_GAP_BRIDGE_TOLERANCE` | constants.py | Replaced by shared constant |
| Update `DEFAULT_MIN_AREA_FILTER` | constants.py | Change base from 100 to 100,000 sq mm |
| Update `DEFAULT_MIN_SIDE_FILTER` | constants.py | Update imperial values for 10mm base |
| Update `_on_unit_change()` | main.py | Remove checkbox conditionals - update ALL values |
| Update `_update_*_default()` methods | main.py | Use shared constant |
| Update initial StringVar values | main.py | Match new MM defaults |
| Update tolerance tests | test_constants.py | Validate new shared values |

## Notes

- The 3mm value represents a typical visible gap in CAD drawings - large enough to bridge design gaps but small enough to not merge distinct geometry
- 1/8 inch (0.125") is the closest standard imperial fraction to 3mm (actual: 3.175mm)
- 100,000 sq mm (≈ 316mm × 316mm square) filters out small artifact polygons while preserving meaningful geometry
- 10mm min side filter removes thin slivers and small edge artifacts
- Updating all values on unit change prevents user confusion when enabling a filter after changing units
- Consider reducing `GAP_BRIDGE_MAX` from 10000.0 to 10.0 to match `PRECISION_FIX_MAX` since both features now share the same purpose
