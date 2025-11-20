# Token-Aware Refactoring Strategy

## Executive Summary
Refactoring purely for token limits is NOT recommended for this codebase. The largest file (extractor.py at 26.9KB) consumes only ~6,700 tokens - well within Claude Code's 200K context window. However, if token optimization becomes necessary, strategic extraction of color analysis and annotation processing into separate modules would be the most practical approach.

## Table Summary

| Module | Size (KB) | Est. Tokens | % of 200K Budget | Refactor Priority | Split Strategy |
|--------|-----------|-------------|------------------|-------------------|----------------|
| extractor.py | 26.9 | ~6,700 | 3.4% | Low | Extract color/annotation analysis |
| excel_writer.py | 24.3 | ~6,100 | 3.0% | Very Low | Extract sheet creators if needed |
| excel_formatting.py | 15.9 | ~4,000 | 2.0% | None | Already focused |
| geometry.py | 9.2 | ~2,300 | 1.1% | None | Already minimal |
| constants.py | 5.4 | ~1,350 | 0.7% | None | Pure config |
| logger.py | 1.2 | ~300 | 0.2% | None | Trivial size |
| **Total** | **82.8** | **~20,750** | **10.4%** | - | - |

## Relevant Files

- **app/core/extractor.py** (26.9KB, 605 lines) - Largest module. Contains main extraction logic, color resolution, and color analysis. Primary candidate if token reduction needed. Functions: `extract_blocks()`, `extract_color_analysis()`, `_resolve_entity_color_to_rgb()`.

- **app/core/excel_writer.py** (24.3KB, 645 lines) - Second largest module. Contains Excel generation with 6 sheet creation functions plus 4 scale helper functions. Secondary candidate for splitting.

- **app/core/excel_formatting.py** (15.9KB, 419 lines) - Excel formatting utilities. Already well-organized with 6 sheet-specific formatters. Low refactoring priority.

- **app/core/geometry.py** (9.2KB, 266 lines) - Geometric calculations. Small and focused. No refactoring needed.

- **app/core/constants.py** (5.4KB, 108 lines) - Configuration constants. Minimal size, no refactoring needed.

- **app/core/logger.py** (1.2KB, 41 lines) - Logging setup. Trivial size, no refactoring needed.

## Token Budget Analysis

**Current State:**
- **Total core module tokens:** ~20,750 (10.4% of 200K budget)
- **Largest single file:** extractor.py at ~6,700 tokens (3.4% of budget)
- **Remaining budget:** 179,250 tokens (89.6%)

**Reality Check:**
- Claude Code has 200,000 token context window
- Reading ALL core modules simultaneously uses only 10.4% of budget
- Even with test files (4,932 lines ≈ 25KB ≈ 6,250 tokens), total usage is ~27,000 tokens (13.5%)
- **Conclusion:** Token limits are NOT a practical concern for this codebase

**When Token Limits Actually Matter:**
- Individual files > 40KB (~10,000 tokens each)
- Total codebase > 400KB (~100,000 tokens)
- Complex operations requiring multiple full file reads in single conversation
- None of these apply to this project

## Practical Refactoring Options (If Required)

### Option 1: Extract Color Analysis Module (Recommended if needed)

**Create:** `app/core/color_analysis.py`

**Move from extractor.py:**
- `_resolve_entity_color_to_rgb()` (73 lines)
- `extract_color_analysis()` (127 lines)
- Total extraction: ~200 lines (~5KB)

**Benefits:**
- Reduces extractor.py by ~19% (605→405 lines)
- Clean separation: color analysis is distinct concern
- Maintains cohesion: both functions work together
- Token reduction: ~1,250 tokens (not significant but clean)

**Implementation:**
```python
# app/core/color_analysis.py
"""Color resolution and analysis for CAD entities."""

def resolve_entity_color_to_rgb(entity, doc) -> tuple[int, int, int] | None:
    """Resolve entity color to RGB (formerly _resolve_entity_color_to_rgb)."""
    # Move implementation here

def extract_color_analysis(doc: Drawing) -> list[dict[str, Any]]:
    """Extract color analysis from drawing."""
    # Move implementation here
```

**Update imports in extractor.py:**
```python
from .color_analysis import resolve_entity_color_to_rgb, extract_color_analysis
```

### Option 2: Extract Annotation Processing Module

**Create:** `app/core/annotation_extractor.py`

**Move from extractor.py:**
- Annotation extraction logic from `extract_blocks()` (lines 433-466)
- Create dedicated function: `extract_annotations()`

**Benefits:**
- Separates TEXT/MTEXT processing from main extraction
- Reduces complexity of main `extract_blocks()` function
- Token reduction: ~500 tokens

**Less Recommended:** This creates tighter coupling and more complexity for minimal gain.

### Option 3: Split Excel Writer by Sheet Groups

**Create:** `app/core/excel_sheets/`
```
excel_sheets/
├── __init__.py
├── block_sheets.py      # Block Analysis + Block Geometry Analysis
├── layer_sheets.py      # Layer Analysis
├── entity_sheets.py     # Entity Summary
├── annotation_sheets.py # Annotations Analysis + Color Analysis
```

**Benefits:**
- Reduces excel_writer.py from 645→150 lines
- Each sheet module is 100-200 lines
- Token reduction: ~4,000 tokens distributed across 4 files

**Drawbacks:**
- Over-engineering for current size
- Adds directory complexity
- Only justified if adding 5+ more worksheets

### Option 4: Reduce Docstring Verbosity

**Current state:** Comprehensive docstrings with examples
```python
def extract_blocks(file_path: str) -> ExtractionResult:
    """
    Extract comprehensive CAD analysis from a DWG or DXF file.

    This function loads a CAD file and extracts:
    - Block insertion counts
    - Entity counts within each block definition
    ... (20+ more lines of docstring)
    """
```

**Streamlined version:**
```python
def extract_blocks(file_path: str) -> ExtractionResult:
    """Extract comprehensive CAD analysis from DWG/DXF file.

    Returns ExtractionResult with blocks, layers, entities, geometry, and colors.
    Raises FileNotFoundError, ValueError for invalid files.
    """
```

**Token savings:** ~2,000 tokens across all modules
**Cost:** Reduced inline documentation quality
**Recommendation:** Only if desperate - documentation is valuable

## Alternative Strategies (No Refactoring)

### Strategy 1: Use Selective File Reading

**Instead of:** Reading entire files
```
Read app/core/extractor.py  # 6,700 tokens
```

**Do:** Read specific functions with line ranges
```
Read app/core/extractor.py (lines 302-450)  # ~1,000 tokens
Read app/core/extractor.py (lines 110-237)  # ~800 tokens
```

**Benefits:**
- No code changes required
- Reduces token usage by 80% when only specific functions needed
- Maintains full file when needed

### Strategy 2: Use Grep for Function Location

**Instead of:** Reading full file to find function
```
Read app/core/extractor.py
# Scan 605 lines to find _resolve_entity_color_to_rgb
```

**Do:** Grep then targeted read
```
Grep "^def _resolve_entity_color_to_rgb" app/core/extractor.py
Read app/core/extractor.py (lines 35-107)
```

**Benefits:**
- Find functions without reading entire files
- 90% token reduction for function discovery

### Strategy 3: Leverage Test Files for Understanding

**Instead of:** Reading implementation files
```
Read app/core/extractor.py  # 6,700 tokens
```

**Do:** Read tests first
```
Read app/tests/core/test_extractor.py (lines 1-100)  # ~500 tokens
# Tests show what extract_blocks() does without implementation details
```

**Benefits:**
- Tests document behavior clearly
- Often faster to understand from tests
- Reduces need to read full implementations

## Refactoring Limits Analysis

### Size-Based Limits

| Threshold | When to Refactor | Rationale |
|-----------|------------------|-----------|
| **300 lines** | Consider if crossing | Single screen view, easy comprehension |
| **500 lines** | Review for separation | Multiple concerns may have emerged |
| **800 lines** | Strong consideration | Difficult to navigate, likely multiple concerns |
| **1000 lines** | Mandatory split | Too large for effective maintenance |

**Current status:** extractor.py at 605 lines - in "review" zone but not mandatory

### Token-Based Limits

| File Size | Est. Tokens | Action Needed |
|-----------|-------------|---------------|
| < 10KB | < 2,500 | No action |
| 10-20KB | 2,500-5,000 | Monitor |
| 20-40KB | 5,000-10,000 | Consider optimization |
| 40-80KB | 10,000-20,000 | **Refactor recommended** |
| > 80KB | > 20,000 | **Refactor required** |

**Current status:** All files under 27KB - in "monitor" or "no action" zones

### Complexity-Based Limits

| Metric | Current | Healthy Range | Action |
|--------|---------|---------------|--------|
| Functions per file | 3-11 | < 15 | ✓ Healthy |
| Max function length | ~270 lines | < 300 | ✓ Healthy |
| Import depth | 2 levels | < 3 | ✓ Healthy |
| Cyclomatic complexity | Low | < 10 per function | ✓ Healthy |

## Recommendations

### Primary Recommendation: Do NOT Refactor for Tokens

**Reasoning:**
1. Current token usage is only 10.4% of budget
2. No practical token limit issues observed
3. Code is well-structured and maintainable
4. Refactoring adds complexity without benefit
5. Claude Code handles current file sizes easily

### Secondary Recommendation: If Token Issues Arise

**Then consider Option 1 (Extract Color Analysis):**
1. Create `app/core/color_analysis.py`
2. Move `_resolve_entity_color_to_rgb()` and `extract_color_analysis()`
3. Update imports in extractor.py
4. Update tests accordingly
5. Estimated effort: 2-3 hours

**Benefits:**
- Clean separation of concerns
- Reduces largest file by 19%
- Improves maintainability (side benefit)
- Token reduction: ~1,250 tokens

### Tertiary Recommendation: Use Alternative Strategies First

**Before refactoring, try:**
1. Use line-range reading for specific functions
2. Use Grep to locate functions before reading
3. Read test files for behavior understanding
4. Ask Claude Code to summarize rather than read full files

## Next Steps

### Immediate Actions (None Required)

**Monitor token usage:**
- No action needed currently
- Revisit if files exceed 40KB (~10,000 tokens)
- Track if Claude Code reports token warnings

### Future Considerations (If Growing Beyond Current Size)

**If extractor.py exceeds 800 lines:**
1. Extract color analysis module (Option 1)
2. Extract annotation processing (Option 2)
3. Evaluate need for further separation

**If excel_writer.py exceeds 800 lines:**
1. Split into sheet-specific modules (Option 3)
2. Create excel_sheets/ directory structure

**If adding 5+ more worksheets:**
1. Implement Option 3 preemptively
2. Organize by worksheet category

### Documentation Updates (If Refactoring)

**If pursuing Option 1:**
1. Update README.md project structure section
2. Add color_analysis.py to architecture diagram
3. Update import examples in docstrings
4. Document rationale in git commit message

## Conclusion

**Token-aware refactoring is NOT practical or necessary for this codebase.** Current files are well within Claude Code's capabilities, and premature optimization would add complexity without benefit. Focus on functional refactoring (improving cohesion, reducing complexity) rather than token-based refactoring. If token issues emerge in the future, Option 1 (Extract Color Analysis) provides the cleanest separation with minimal disruption.
