# Chore: Add filtered_polygon_count Field for Polygon Count Tracking

## Chore Description
Add a `filtered_polygon_count` field to support tracking polygon counts before and after filtering. This field will be added to the `ContentZoneData` TypedDict to distinguish between the original polygon count (before any filtering) and the filtered count (after side + area filtering has been applied). Additionally, a corresponding Excel column constant will be added to support exporting this data.

The semantic distinction is:
- `polygon_count` = Original count BEFORE any filtering
- `filtered_polygon_count` = Count AFTER all filtering (side + area)

## Relevant Files
Use these files to resolve the chore:

- `app/core/types.py` - Contains the `ContentZoneData` TypedDict where the new `filtered_polygon_count` field needs to be added (lines 195-228)
- `app/core/constants.py` - Contains Excel column constants where `EXCEL_COLUMN_BLOCK_FILTERED_POLYGON_COUNT` needs to be added
- `app_docs/005-field-naming-convention.md` - Reference for field naming conventions (already read, no changes needed)

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### Step 1: Update ContentZoneData TypedDict in types.py
- Open `app/core/types.py`
- Locate the `ContentZoneData` TypedDict (lines 195-228)
- Update the docstring to clarify the semantic difference between `polygon_count` and `filtered_polygon_count`:
  - `polygon_count` = Total number of closed polygons found BEFORE any filtering (LWPOLYLINE + LINE cycles)
  - `filtered_polygon_count` = Count of polygons AFTER all filtering (side + area filters applied)
- Add the new field `filtered_polygon_count: int` after `polygon_count`

The updated TypedDict should look like:
```python
class ContentZoneData(TypedDict):
    """
    Results from content zone detection analysis.

    Contains suggested trim values derived from the detected content zone shape
    relative to the block's bounding box. The content zone is the closed polygon
    with the largest net area (own area minus areas of contained polygons).

    Attributes:
        suggested_trim_left: Distance from block left edge to content zone left edge,
                            or None if no content zone detected
        suggested_trim_right: Distance from content zone right edge to block right edge,
                             or None if no content zone detected
        suggested_trim_top: Distance from content zone top edge to block top edge,
                           or None if no content zone detected
        suggested_trim_bottom: Distance from block bottom edge to content zone bottom edge,
                              or None if no content zone detected
        content_zone_detected: True if a valid content zone was found, False otherwise
        content_zone_width: Width of content zone bounding box (cz_max_x - cz_min_x),
                           or None if no content zone detected
        content_zone_height: Height of content zone bounding box (cz_max_y - cz_min_y),
                            or None if no content zone detected
        polygon_count: Total number of closed polygons found BEFORE any filtering
                      (LWPOLYLINE + LINE cycles)
        filtered_polygon_count: Count of polygons AFTER all filtering (side + area
                               filters applied)
    """

    suggested_trim_left: float | None
    suggested_trim_right: float | None
    suggested_trim_top: float | None
    suggested_trim_bottom: float | None
    content_zone_detected: bool
    content_zone_width: float | None
    content_zone_height: float | None
    polygon_count: int
    filtered_polygon_count: int
```

### Step 2: Add Excel Column Constant in constants.py
- Open `app/core/constants.py`
- Locate the Content Zone columns section (around line 115 where `EXCEL_COLUMN_BLOCK_POLYGON_COUNT` is defined)
- Add the new constant immediately after `EXCEL_COLUMN_BLOCK_POLYGON_COUNT`:
```python
EXCEL_COLUMN_BLOCK_FILTERED_POLYGON_COUNT: str = "block_filtered_polygon_count"
```
- The naming follows the convention in `app_docs/005-field-naming-convention.md`:
  - Domain: `block`
  - Attribute: `filtered_polygon`
  - Qualifier: `count`

### Step 3: Run Validation Commands
Execute all validation commands to ensure the changes are complete with zero regressions.

## Validation Commands
Execute every command to validate the chore is complete with zero regressions.

- `uv run pytest app/tests/core/test_constants.py -v` - Run constants tests to validate no regressions
- `uv run mypy app/core/types.py app/core/constants.py` - Type check the modified files
- `uv run ruff check app/core/types.py app/core/constants.py` - Lint the modified files
- `uv run pytest app/tests/ -v --tb=short` - Run full test suite to ensure no regressions

## Notes
- This is a foundational change (Unit 1) that adds the type and constant definitions. Subsequent units will:
  - Populate the `filtered_polygon_count` field during extraction
  - Add the column to Excel output
  - Add tests for the new field
- The `filtered_polygon_count` field is initialized separately from `polygon_count` to maintain clear separation between raw detection and filtered results
- The field naming follows the established convention: `block_filtered_polygon_count` uses the block domain prefix since this is a per-block metric from content zone analysis
