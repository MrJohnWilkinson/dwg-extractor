# DBKEY Last Digits to Block Correlation Analysis

## Executive Summary

DBKEY last digits do not directly encode block type, but blocks of the same type are inserted in consecutive batches, resulting in clustered sequential DBKEY suffixes. The prefix `338713` appears constant (likely a drawing/session ID), while the last 4 digits form a sequential counter. Same block types share consecutive DBKEY ranges because they were inserted together.

## Table Summary

| BlockName | DBKEY Range | Last 4 Digits | Cluster Size | Pattern |
|-----------|-------------|---------------|--------------|---------|
| 30in-Roller_PD | 3387136537-539 | 6537-6539 | 3 | Consecutive |
| 24in_PD_Counter | 3387136548 | 6548 | 1 | Single |
| 20ft Fishbone Grill | 3387136609 | 6609 | 1 | Single |
| 5Gal Bottle Water | 3387136948-949 | 6948-6949 | 2 | Consecutive |
| 36X48 Pallet | 3387136978-7001 | 6978-7001 | 11 | 4 sub-clusters |

## Relevant Files

- `app/core/extractor.py` - XDATA extraction logic that could parse DBKEY values
- `app/core/constants.py` - Column definitions; could add DBKEY column
- `ai_output/072-dbkey-dxf-relationship-analysis.md` - Previous DBKEY analysis

## DBKEY Structure Breakdown

```
DBKEY: 3387136948
       ├── 338713 (Drawing/Session Prefix - constant)
       └── 6948   (Sequential Counter - varies)
```

| Component | Digits | Purpose | Example |
|-----------|--------|---------|---------|
| Drawing Prefix | 1-6 | Session/Drawing ID | `338713` (constant in dataset) |
| Sequential Counter | 7-10 | Insertion order | `6537` to `7001` |

## Last 4 Digits Cluster Analysis

Blocks of the same type form consecutive clusters:

| Block Type | Last 4 Digits | Gap from Previous |
|------------|---------------|-------------------|
| 30in-Roller_PD | 6537, 6538, 6539 | - |
| 24in_PD_Counter | 6548 | +9 |
| 20ft Fishbone | 6609 | +61 |
| 5Gal Bottle Water | 6948, 6949 | +339 |
| 36X48 Pallet (batch 1) | 6978, 6979, 6980 | +29 |
| 36X48 Pallet (batch 2) | 6984, 6985 | +4 |
| 36X48 Pallet (batch 3) | 6990, 6991, 6992 | +5 |
| 36X48 Pallet (batch 4) | 6999, 7000, 7001 | +7 |

## 36X48 Pallet Sub-Cluster Analysis

The 11 pallets form 4 sub-clusters with small internal gaps:

| Sub-Cluster | Last 3 Digits | X-Coordinates (approx) | Spatial Grouping |
|-------------|---------------|------------------------|------------------|
| Cluster A | 978, 979, 980 | 552, 516, 588 | Right side |
| Cluster B | 984, 985 | 663, 627 | Far right |
| Cluster C | 990, 991, 992 | 441, 405, 477 | Middle |
| Cluster D | 999, 000, 001 | 316, 280, 352 | Left side |

This suggests pallets were selected/inserted in 4 spatial groups from right-to-left.

## Correlation Findings

| Hypothesis | Result | Evidence |
|------------|--------|----------|
| Last digits encode block type | FALSE | Different blocks share similar suffixes (e.g., 48) |
| Same blocks have consecutive DBKEYs | TRUE | 30in-Roller_PD: 537,538,539 |
| DBKEY predicts block type | PARTIAL | Consecutive DBKEYs = same type (within cluster) |
| Spatial order = DBKEY order | FALSE | X-coords don't follow DBKEY sequence |

## Practical Applications

| Use Case | Feasibility | Method |
|----------|-------------|--------|
| Group blocks by DBKEY range | High | Blocks with consecutive DBKEYs are same type |
| Reverse-lookup block type from DBKEY | Low | No direct encoding; requires range mapping |
| Detect insertion batches | High | Gaps in DBKEY sequence indicate new batch |
| Track insertion order | High | Lower DBKEY = inserted earlier |

## Simple List Summary

- DBKEY prefix `338713` is constant (drawing/session ID)
- Last 4 digits are sequential insertion counter (6537-7001 range)
- Same block types get consecutive DBKEYs because inserted together
- 36X48 Pallets show 4 sub-clusters = 4 separate insertion operations
- Last digits don't encode block type but do indicate batch membership
- Gaps between DBKEY clusters suggest different insertion sessions
- Spatial position does not correlate with DBKEY order within clusters
