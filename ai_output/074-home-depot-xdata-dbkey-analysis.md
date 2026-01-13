# HOME_DEPOT XDATA Application and DBKEY Relationship

## Executive Summary

The DBKEY field is highly likely stored as XDATA under a `HOME_DEPOT` (or similar vendor-specific) application ID attached to each INSERT entity. The `Live_fixtureplan` FileType in the data confirms this is Home Depot's fixtures management system. The current extractor collects XDATA app IDs but does not extract the actual DBKEY values stored within.

## Table Summary

| XDATA Component | Purpose | Example Value |
|-----------------|---------|---------------|
| Application ID | Vendor identifier | `HOME_DEPOT` or `HD_FIXTURES` |
| Tag 1000 (string) | DBKEY as text | `"3387136948"` |
| Tag 1070 (16-bit int) | Small integers | N/A (DBKEY too large) |
| Tag 1071 (32-bit int) | DBKEY as integer | `3387136948` |

## Relevant Files

- `app/core/extractor.py:1539-1562` - Current XDATA app ID extraction (collects IDs only, not values)
- `app/core/extractor.py:783-801` - XDATA value extraction example (for dynamic block resolution)
- `app/tests/assets/create_xdata_test.py` - Test fixture showing XDATA structure with ezdxf
- `app/core/constants.py:44` - `EXCEL_COLUMN_BLOCK_XDATA_APPS` column definition

## XDATA Structure in DXF

Home Depot's fixture system likely attaches XDATA to INSERT entities:

```dxf
INSERT
  ...entity data...
1001
HOME_DEPOT
1071
3387136948
```

Or as string:
```dxf
1001
HOME_DEPOT
1000
3387136948
```

## XDATA Tag Codes Reference

| Code | Type | Range | Suitable for DBKEY |
|------|------|-------|-------------------|
| 1000 | String | Unlimited | Yes (as text) |
| 1070 | 16-bit integer | -32768 to 32767 | No (too small) |
| 1071 | 32-bit integer | -2B to 2B | Yes (DBKEYs ~3.4B fit) |

The DBKEY values (e.g., `3387136948`) require either:
- Tag 1000 as string `"3387136948"`
- Tag 1071 as 32-bit integer `3387136948`

## Current Extractor Behavior

| Feature | Current Status | Code Location |
|---------|----------------|---------------|
| Collect XDATA app IDs | Implemented | extractor.py:1548-1559 |
| Extract XDATA string values (1000) | For dynamic blocks only | extractor.py:783-798 |
| Extract XDATA integer values (1071) | Not implemented | - |
| HOME_DEPOT-specific extraction | Not implemented | - |

## Evidence Linking DBKEY to XDATA

| Data Point | Evidence |
|------------|----------|
| FileType = `Live_fixtureplan` | Home Depot's fixture planning system |
| DBKEY prefix `338713` | Drawing/session identifier (constant) |
| Sequential DBKEYs | Database record IDs assigned on insert |
| Unique per insertion | One-to-one mapping to INSERT entities |
| Not in standard DXF fields | Must be stored as XDATA extension |

## Implementation to Extract HOME_DEPOT DBKEY

To extract DBKEY values, extend the XDATA extraction:

```python
# After line 1559 in extractor.py
# Extract HOME_DEPOT DBKEY from XDATA
try:
    hd_xdata = entity.xdata.get("HOME_DEPOT")
    if hd_xdata:
        for tag in hd_xdata:
            if tag.code == 1071:  # 32-bit integer
                dbkey = tag.value
            elif tag.code == 1000:  # String
                dbkey = tag.value
except (DXFError, KeyError):
    pass
```

## Simple List Summary

- DBKEY is stored as XDATA under `HOME_DEPOT` (or similar) application ID
- XDATA attaches to each INSERT entity in the DXF
- Tag 1000 (string) or 1071 (32-bit int) likely contains the DBKEY value
- Current extractor collects app IDs but not values
- `Live_fixtureplan` FileType confirms Home Depot fixtures system
- Extending extractor.py:1539-1562 would enable DBKEY extraction
- No `HOME_DEPOT` reference in codebase yet - requires sample DXF to confirm app ID name
