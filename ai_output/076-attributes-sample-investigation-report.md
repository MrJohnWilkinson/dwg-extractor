# attributes-sample.dxf Investigation Report

## Executive Summary

The investigation confirms that `attributes-sample.dxf` does **not contain 10-digit DBKEY values**. Instead, it uses a different data structure with 7-digit fixture IDs in HOME_DEPOT XDATA and 8-digit GUIDE values in block attributes. The 10-digit DBKEY format the user referenced likely comes from a different drawing version or external database linkage.

## Investigation Results

### Step 1: Search for DBKEY in Alternative Locations

**Result:** No 10-digit integer values found

- Searched XDATA codes 1071 and 1070 for values > 1,000,000,000
- No large integer values exist anywhere in XDATA
- HOME_DEPOT XDATA uses only Code 1000 (strings), not Code 1071 (integers)

### Step 2: Entity Handles Analysis

**Result:** Handles are 7-digit decimal values (3 million range)

| Block | Handle (Hex) | Handle (Decimal) |
|-------|--------------|------------------|
| EHE42 | 2E7FD4 | 3,047,380 |
| RACKE | 2E7FDD | 3,047,389 |
| EHE24 | 2E80C8 | 3,047,624 |

Entity handles are sequential allocation counters, not meaningful DBKEYs.

### Step 3: Pattern Differences with User Data

**Comparison:**

| Feature | User's Data | Sample DXF |
|---------|-------------|------------|
| DBKEY format | 10-digit integer (3387136948) | **Not present** |
| XDATA storage | Code 1071 (integer) suspected | Code 1000 (string) only |
| Value size | 10 digits | 4-8 digits |
| Data source | External database link | Embedded fixture metadata |

### Step 4: XDATA Application IDs

**56 registered XDATA app IDs found**, including:

| App ID | Purpose |
|--------|---------|
| HOME_DEPOT | Fixture metadata (primary data source) |
| STPL_* (14 apps) | StorePlanner software metadata |
| DCO15 | Unknown (possibly design software) |
| AcDbDynamicBlock* | AutoCAD dynamic block data |
| ACAD | Standard AutoCAD data |

STPL_Fixtures app is registered but **contains no data** (0 INSERTs).

### Step 5: HOME_DEPOT XDATA Structure

**Two distinct patterns found:**

| Pattern | Count | Structure |
|---------|-------|-----------|
| Minimal | 1,107 | Single Code 1000: `'0101'` (category code only) |
| Full | 295 | Six Code 1000 values (fixture metadata) |

**Full XDATA structure (6 values):**

| Position | Sample Value | Purpose |
|----------|--------------|---------|
| 1 | `'0101'` | Category/type code |
| 2 | `'0120258'` | **7-digit Fixture ID** |
| 3 | `'U0000   '` | Placeholder/padding |
| 4 | `''` | Empty |
| 5 | `'Unassigned'` | Status field |
| 6 | `'21'` | Numeric code |

**168 unique fixture IDs** found, ranging from 0120258 to 0120495 (mostly sequential).

### Block Attributes (ATTRIB) Analysis

**93 unique attribute tags** found across 1,118 blocks with attributes:

| Tag | Count | Sample Value | Purpose |
|-----|-------|--------------|---------|
| BAY# | 1,118 | `'13-EC2'`, `'14-019'` | Bay location identifier |
| PROD1 | 1,044 | `'Sawhorses'`, `'Metal'` | Product description |
| PROD2 | 1,044 | `'Steel'`, `'Fastening'` | Secondary product info |
| DEPT | 1,033 | `'25'`, `'6'` | Department number |
| ROW# | 1,031 | (often empty) | Row number |
| GUIDE | 1,031 | `'06979943'`, `'25119435'` | **8-digit guide number** |
| LIGHTING_TRAIT | 218 | (icon character) | Lighting indicator |

**GUIDE values:** 496 unique 8-digit values found. These could be product guide numbers from Home Depot's catalog system.

## Conclusions

### Finding 1: No DBKEY in This Sample

The 10-digit DBKEY format (like 3387136948) does **not exist** in this DXF file. The sample uses:
- 7-digit Fixture IDs in XDATA (0120258)
- 8-digit GUIDE values in attributes (06979943)

### Finding 2: Two Data Systems

The DXF contains two separate identification systems:

1. **HOME_DEPOT XDATA** → Fixture catalog IDs (7-digit)
2. **Block Attributes** → GUIDE product numbers (8-digit)

These systems appear independent (blocks with fixture IDs don't have GUIDE attributes).

### Finding 3: DBKEY Source Hypothesis

The user's 10-digit DBKEY likely comes from:

1. **Different drawing version** - Newer DXF exports may include database linkage
2. **External database** - DBKEY may be stored in linked database, not DXF
3. **Different XDATA format** - User's source may use Code 1071 integers

## Recommendations

### To locate DBKEY values:

1. **Obtain user's source DXF** - The sample may be older or different from user's actual data
2. **Check for database links** - DXF may reference external .mdb or SQL database
3. **Examine Code 1071** - If available, user's source may use integer codes instead of strings

### For current extractor functionality:

1. **Extract GUIDE attribute** - 8-digit product guide numbers are valuable
2. **Extract Fixture ID** - XDATA position 2 contains 7-digit fixture catalog IDs
3. **Consider both systems** - Some blocks have XDATA, others have attributes

## Data Statistics

| Metric | Value |
|--------|-------|
| Total INSERT entities | 3,664 |
| INSERTs with HOME_DEPOT XDATA | 1,402 |
| INSERTs with full XDATA (6 values) | 295 |
| INSERTs with minimal XDATA (1 value) | 1,107 |
| INSERTs with attributes | 1,118+ |
| Unique Fixture IDs | 168 |
| Unique GUIDE values | 496 |
| Registered XDATA app IDs | 56 |
| 10-digit DBKEY values found | **0** |
