# Planogram-to-CAD Mapper: Design Analysis Report (v2)

## Executive Summary

This report analyzes the mapping challenge between Excel planogram data and CAD fixtures. Three different width measurements exist (stated, cell-implied, CAD-measured) and **none of them match**. Understanding these discrepancies is essential before designing any mapping solution.

## Table Summary: The Three Width Values

| Source | Calculation | Value |
|--------|-------------|-------|
| **Stated** | Row 6 values: 30+30+5+25+15 | **105 ft** |
| **Cell Implied** | 22 cells × 5 ft/cell | **110 ft** |
| **CAD** | 43 fixtures × 2.5 ft/fixture | **107.5 ft** |

**None match. Discrepancies:**
- Cell Implied vs Stated: +5 ft (4.8%)
- CAD vs Stated: +2.5 ft (2.4%)
- Cell Implied vs CAD: +2.5 ft (2.3%)

## Verified Data: Excel Row 5-6 (K5 to AF5)

| Planogram | Cells | Cell Implied | Stated Width | Discrepancy |
|-----------|-------|--------------|--------------|-------------|
| Paper Towels | 6 | 30 ft | 30 ft | - |
| Bath Tissue | 7 | 35 ft | 30 ft | **+5 ft** |
| Napkins | 1 | 5 ft | 5 ft | - |
| Plates & Cups | 5 | 25 ft | 25 ft | - |
| Multi Pack Water | 3 | 15 ft | 15 ft | - |
| **TOTAL** | **22** | **110 ft** | **105 ft** | **+5 ft** |

Bath Tissue occupies 7 cells (implying 35 ft) but states only 30 ft.

## Verified Data: CAD Fixtures (ENGO-W30-84)

- **Block name:** ENGO-W30-84 (exact match, excluding ENGO-W30-E-84)
- **Fixture count:** 43
- **Fixture width:** 2.5 ft each
- **Total:** 43 × 2.5 = **107.5 ft**

## Relevant Files

- **app/tests/assets/samples/floorplan-excel.xlsx** - Source Excel with planogram grid
- **app/tests/assets/samples/floorplan-cad.dxf** - Source CAD with fixture blocks
- **app/core/extractor.py** - Existing DXF extraction patterns (reusable)
- **app/core/geometry.py** - Spatial analysis utilities (reusable)

## Problem Statement

**Goal:** Map planogram names from Excel cells to CAD fixture positions, outputting text annotations on a new DXF layer.

**Core Challenges:**
1. Three different width measurements that don't agree
2. Excel grid is approximate, not exact match to CAD layout
3. Orientation difference (Excel: West-up, CAD: North-up)
4. Fixture counts may differ between Excel implied and CAD actual

## Excel Data Structure

**Horizontal planogram rows (two-row pattern):**
```
Row N:   | Planogram Name | (empty cells)      | Next Planogram |
Row N+1: | Width in feet  | (empty cells)      | Width          |
```

**Vertical planogram columns:**
- Name spans multiple cells vertically
- Width value in last cell of the span

## Open Questions for Solution Design

1. **Which width value should drive mapping?**
   - Stated width (105 ft) - closest to CAD but still 2.5 ft off
   - Cell implied (110 ft) - matches cell count but 2.5 ft over CAD
   - CAD actual (107.5 ft) - ground truth for fixture positions

2. **How to handle the 2.5-5 ft discrepancies?**
   - Proportional scaling?
   - Per-planogram adjustment?
   - User correction step?

3. **How to identify fixture rows/columns in CAD?**
   - User specifies layer + block pattern
   - Group fixtures by spatial alignment (tolerance for slight offsets)

## Simple List Summary

- **Stated width:** 105 ft (from row 6 values)
- **Cell implied width:** 110 ft (22 cells × 5 ft)
- **CAD width:** 107.5 ft (43 fixtures × 2.5 ft)
- **None of these values match**
- **Bath Tissue discrepancy:** 7 cells (35 ft implied) but states 30 ft
- **Mapping requires reconciling these three different measurements**
