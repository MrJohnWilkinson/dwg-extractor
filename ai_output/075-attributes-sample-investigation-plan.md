# attributes-sample.dxf Investigation Plan

## Executive Summary

The DXF sample contains 3,664 INSERT entities with 1,402 having `HOME_DEPOT` XDATA attached. The XDATA structure uses multiple Code 1000 string values for fixture metadata, but does not contain 10-digit DBKEY values like those in the user's data. The DBKEY may be stored differently or this sample predates DBKEY implementation.

## Table Summary

| Component | Finding | Count |
|-----------|---------|-------|
| INSERT entities | Total blocks in drawing | 3,664 |
| INSERTs with HOME_DEPOT XDATA | Blocks with vendor data | 1,402 |
| Unique XDATA values | Distinct string values | 219 |
| Block attributes (ATTRIB) | Tags like BAY#, GUIDE, PROD1 | Present |
| 10-digit DBKEY values | Not found | 0 |

## Relevant Files

- `app/tests/assets/samples/attributes-sample.dxf` - 18MB DXF with HOME_DEPOT XDATA (target file)
- `app/core/extractor.py:1539-1562` - Current XDATA extraction (app IDs only)
- `ai_output/074-home-depot-xdata-dbkey-analysis.md` - Previous DBKEY analysis

## HOME_DEPOT XDATA Structure Discovered

Each INSERT with XDATA contains multiple Code 1000 string values:

| Position | Sample Value | Possible Purpose |
|----------|--------------|------------------|
| 1 | `'0101'` | Category/Type code |
| 2 | `'0120258'` | 7-digit fixture ID |
| 3 | `'U0000   '` | Placeholder/padding |
| 4 | `''` | Empty |
| 5 | `'Unassigned'` | Status field |
| 6 | `'21'` | Numeric code |

## Block Attributes (ATTRIB) Discovered

INSERTs also have standard DXF attributes:

| Tag | Sample Value | Purpose |
|-----|--------------|---------|
| ROW# | (empty) | Row number |
| BAY# | `'13-EC2'` | Bay identifier |
| GUIDE | `'06979943'` | 8-digit guide number |
| PROD1 | `'Sawhorses'` | Product description |
| PROD2 | (empty) | Secondary product info |

## Investigation Steps

### Step 1: Search for DBKEY in Alternative Locations
```bash
# Check for 10-digit numeric values anywhere in XDATA
uv run python -c "
import ezdxf
doc = ezdxf.readfile('app/tests/assets/samples/attributes-sample.dxf')
for insert in doc.modelspace().query('INSERT'):
    if insert.xdata:
        for appid in insert.xdata.data.keys():
            for tag in insert.xdata.get(appid):
                if tag.code in (1071, 1070) and tag.value > 1000000000:
                    print(f'{appid}: {tag.value}')
"
```

### Step 2: Check Entity Handles
```bash
# Entity handles could map to DBKEY
uv run python -c "
import ezdxf
doc = ezdxf.readfile('app/tests/assets/samples/attributes-sample.dxf')
for insert in list(doc.modelspace().query('INSERT'))[:5]:
    print(f'{insert.dxf.name}: handle={insert.dxf.handle}')"
```

### Step 3: Compare with User's Original Data
- User's DBKEY: 10-digit (3387136948)
- Sample XDATA: 4-7 digit strings (0101, 0120258)
- Possible: Different drawing versions or DBKEY stored in external database

### Step 4: Check Other XDATA Applications
```bash
# List all registered XDATA app IDs
uv run python -c "
import ezdxf
doc = ezdxf.readfile('app/tests/assets/samples/attributes-sample.dxf')
for appid in doc.appids:
    print(appid.dxf.name)"
```

### Step 5: Analyze 7-digit Fixture IDs
The `0120258` style values could be related to DBKEY:
- Check if they're sequential per block type
- Compare pattern to user's DBKEY suffix analysis

## Key Findings vs User's Data

| Feature | User's Data | Sample DXF |
|---------|-------------|------------|
| DBKEY format | 10-digit integer | Not present |
| XDATA app ID | (assumed HOME_DEPOT) | HOME_DEPOT confirmed |
| Value storage | Code 1071 (integer) suspected | Code 1000 (string) found |
| Fixture ID | 7-digit in XDATA Value 2 | 7-digit (0120258) |

## Hypothesis

The 7-digit fixture ID in XDATA position 2 (`0120258`) may be the **internal fixture ID** that corresponds to a record in Home Depot's database, while the 10-digit DBKEY in the user's data is a **database primary key** that includes a drawing/session prefix. The relationship:

```
DBKEY: 3387136948
       └── 338713 (drawing prefix) + 6948 (fixture sequence)

Sample Fixture ID: 0120258
       └── Different numbering scheme, possibly older format
```

## Simple List Summary

- File contains 3,664 INSERTs, 1,402 with HOME_DEPOT XDATA
- HOME_DEPOT XDATA uses Code 1000 strings (not Code 1071 integers)
- XDATA values are 4-7 digits, not 10-digit DBKEYs
- Block attributes include BAY#, GUIDE, PROD1, PROD2 tags
- 10-digit DBKEY not found - may be in different drawing version
- 7-digit fixture IDs (0120258) could be related to DBKEY
- Need user's actual source DXF to confirm DBKEY storage format
