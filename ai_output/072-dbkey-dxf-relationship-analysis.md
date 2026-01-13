# DBKEY to DXF Block/Layer Relationship Analysis

## Executive Summary

DBKEY is an external database identifier (not native DXF data) that uniquely identifies each block insertion instance in the drawing. It does not derive from block names or layers - instead it's a sequential integer assigned by an external fixtures/planogram management system and stored as XDATA attached to INSERT entities.

## Table Summary

| Field | Relationship to DBKEY | Pattern |
|-------|----------------------|---------|
| BlockName | None - same name has many DBKEYs | `36X48 Pallet` has 11 different DBKEYs |
| Layer | None - same layer has many DBKEYs | `h-bulk` blocks have DBKEYs 3387136978-3387137001 |
| InsertionPoint | Indirect - unique position = unique DBKEY | Each X,Y coordinate pair has unique DBKEY |
| FileType | Source system | `Live_fixtureplan` = fixtures management system |
| Sequence | Direct - DBKEYs are near-sequential | Assigned in creation/insertion order |

## Relevant Files

- `app/core/extractor.py` - Contains XDATA extraction logic (lines 714-882) that could extract DBKEY if stored as XDATA
- `app/core/constants.py` - Column definitions for Excel output; no DBKEY column exists currently
- `app/tests/assets/xdata_test.dxf` - Test file for XDATA functionality

## DBKEY Characteristics

Based on the provided data:

| Observation | Evidence |
|-------------|----------|
| Unique per insertion | 18 rows, 18 unique DBKEYs |
| Sequential assignment | Values range 3387136537-3387137001 (464 range) |
| Not block-derived | Same `36X48 Pallet` has DBKEYs: 3387136978, 3387136979, 3387136980... |
| Not layer-derived | `h-bulk` layer has DBKEYs across full range |
| Position-correlated | Each unique X,Y insertion point has unique DBKEY |

## Layer-to-Block Grouping

| Layer | Block Count | DBKEY Range | Purpose |
|-------|-------------|-------------|---------|
| h-equip | 5 | 3387136537-3387136949 | Equipment fixtures |
| h-fixt | 1 | 3387136609 | Fixture displays |
| h-millwork | 1 | 3387136548 | Millwork counters |
| h-bulk | 11 | 3387136978-3387137001 | Bulk storage pallets |

## Storage Mechanism

The DBKEY is likely stored as XDATA (Extended Data) attached to each INSERT entity:

```
XDATA Application ID: "Live_fixtureplan" or vendor-specific
Tag 1000 (string) or 1070 (integer): DBKEY value
```

The current extractor (extractor.py:1539-1559) collects XDATA application IDs but does not extract specific values like DBKEY.

## Current Codebase Support

| Feature | Status |
|---------|--------|
| XDATA app ID collection | Supported |
| XDATA value extraction | Not implemented |
| DBKEY column in Excel | Not implemented |
| Planogram system integration | Not implemented |

## Simple List Summary

- DBKEY is an external database ID, not derived from block names or layers
- Each block insertion gets a unique, sequential DBKEY
- DBKEY is likely stored as XDATA from the `Live_fixtureplan` system
- Same block name on same layer can have multiple DBKEYs (one per insertion)
- Current extractor reads XDATA app IDs but not DBKEY values
- To support DBKEY: extend XDATA extraction to capture specific tag values
