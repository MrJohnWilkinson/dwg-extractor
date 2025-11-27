# Chore: Replace Tuple-Keyed Dicts with Frozen Dataclass Keys

## Chore Description

Replace tuple-keyed dictionaries with frozen dataclass keys for improved LLM code clarity. The current codebase uses anonymous tuples as dictionary keys (e.g., `dict[tuple[str, str], int]`), which lack semantic meaning. Frozen dataclasses provide:

1. **Named fields** - LLMs and developers can understand `BlockLayerKey(block_name="DOOR", layer_name="WALLS")` vs `("DOOR", "WALLS")`
2. **Docstrings** - Each key class documents its purpose and field meanings
3. **Type safety** - Field names prevent positional errors when constructing keys
4. **Hashability** - `frozen=True` enables use as dict keys

**Scope of changes:**

- Replace tuple-keyed dicts with frozen dataclass keys (highest LLM clarity impact)
- Keep simple counters as `dict[str, int]` (already clear and semantic)
- Keep TypedDicts for records (ColorAnalysisRecord and BlockTrimmingData are already well-documented)
- Add docstrings to all new classes
- Follow naming conventions from `ai_docs/001-naming-convention-guide.md` and `app_docs/005-field-naming-convention.md`

## Relevant Files

Use these files to resolve the chore:

- `app/core/types.py` - Contains existing TypedDict definitions. Add new frozen dataclass key definitions here.
- `app/core/extractor.py` - Contains `ExtractionResult` TypedDict with tuple-keyed dict fields and the `extract_blocks()` function that populates them. Update type annotations and dict key construction.
- `app/core/excel_writer.py` - Consumes `ExtractionResult` and unpacks dict keys. Update iteration over dict items to use dataclass field access.
- `app/tests/core/test_extractor.py` - Contains tests that construct and access tuple-keyed dicts. Update test assertions to use dataclass keys.
- `app/tests/core/test_excel_writer.py` - Contains tests that may construct mock ExtractionResult data. Update to use dataclass keys.

### New Files

None required - all changes are modifications to existing files.

## Step by Step Tasks

IMPORTANT: Execute every step in order, top to bottom.

### Step 1: Define Frozen Dataclass Keys in types.py

Add new frozen dataclass definitions to `app/core/types.py`. Follow the naming conventions:

- **Class names**: PascalCase with descriptive suffix `Key` (per `ai_docs/001-naming-convention-guide.md`)
- **Field names**: snake_case using `{domain}_{attribute}` pattern where domain adds clarity (per `app_docs/005-field-naming-convention.md`)
- **Field naming within key classes**: Since the class name provides domain context, use minimal prefixes only when needed for disambiguation

**BlockLayerKey** - Replaces `tuple[str, str]` for `block_layer_pairs` and `block_xdata_apps`

- Fields: `block_name: str`, `layer_name: str`
- Docstring: "Hashable key identifying a unique block-layer combination for insertion tracking."

**BlockRotationKey** - Replaces `tuple[str, str, str]` for `block_rotation_counts`

- Fields: `block_name: str`, `layer_name: str`, `rotation_category: str`
- Docstring: "Hashable key identifying block insertions by layer and rotation category. rotation_category is one of '0', '90', '180', '270', 'other'."

**AnnotationKey** - Replaces `tuple[str, str, str, int, int, int]` for `annotation_data`

- Fields: `annotation_contents: str`, `annotation_type: str`, `layer_name: str`, `color_r: int`, `color_g: int`, `color_b: int`
- Uses `annotation_contents` and `annotation_type` prefixes to match existing `ColorAnalysisRecord` pattern and `EXCEL_COLUMN_ANNOTATION_*` constants
- Uses `color_r`, `color_g`, `color_b` to match existing color field naming pattern
- Docstring: "Hashable key identifying unique text annotations by content, type (TEXT/MTEXT), layer, and RGB color."

**ColorEntityKey** - Replaces `tuple[int, int, int, int | None, str, str]` for internal `geometric_entities` dict

- Fields: `color_r: int`, `color_g: int`, `color_b: int`, `color_aci: int | None`, `layer_name: str`, `entity_type: str`
- Matches existing `ColorAnalysisRecord` field naming exactly for consistency
- Docstring: "Hashable key for grouping geometric entities by RGB color, ACI index, layer, and entity type."

All dataclasses must use `@dataclass(frozen=True)` for hashability.

### Step 2: Update ExtractionResult in extractor.py

Update the `ExtractionResult` TypedDict in `app/core/extractor.py`:

- Change `block_layer_pairs: dict[tuple[str, str], int]` to `block_layer_pairs: dict[BlockLayerKey, int]`
- Change `block_rotation_counts: dict[tuple[str, str, str], int]` to `block_rotation_counts: dict[BlockRotationKey, int]`
- Change `block_xdata_apps: dict[tuple[str, str], set[str]]` to `block_xdata_apps: dict[BlockLayerKey, set[str]]`
- Change `annotation_data: dict[tuple[str, str, str, int, int, int], int]` to `annotation_data: dict[AnnotationKey, int]`

Add imports for the new dataclass types from `types.py`.

### Step 3: Update extract_blocks() Function in extractor.py

Update the `extract_blocks()` function to use frozen dataclass keys:

- Update local variable type annotations to use new key types
- Replace tuple key construction with dataclass instantiation using keyword arguments for clarity:
  - `pair_key = (block_name, layer_name)` becomes `pair_key = BlockLayerKey(block_name=block_name, layer_name=layer_name)`
  - `rotation_key = (block_name, layer_name, rotation_category)` becomes `rotation_key = BlockRotationKey(block_name=block_name, layer_name=layer_name, rotation_category=rotation_category)`
  - `annotation_key = (contents, entity_type, ...)` becomes `annotation_key = AnnotationKey(annotation_contents=contents, annotation_type=entity_type, layer_name=layer_name, color_r=rgb_color[0], color_g=rgb_color[1], color_b=rgb_color[2])`

### Step 4: Update extract_color_analysis() Function in extractor.py

Update the internal `geometric_entities` dict to use `ColorEntityKey`:

- Change type annotation from `dict[tuple[int, int, int, int | None, str, str], int]` to `dict[ColorEntityKey, int]`
- Replace tuple key construction with dataclass instantiation using keyword arguments
- Update the unpacking loop that converts to `ColorAnalysisRecord` list to use dataclass field access (e.g., `key.color_r`, `key.layer_name`)

### Step 5: Update excel_writer.py Dict Iteration

Update `app/core/excel_writer.py` to use dataclass field access:

- In `_create_block_analysis_sheet()`: Change tuple unpacking to dataclass field access
  - `for (block_name, layer_name), insertion_count in block_layer_pairs.items()` becomes `for key, insertion_count in block_layer_pairs.items()` with `key.block_name`, `key.layer_name`
  - Update `block_xdata_apps.get()` to use `BlockLayerKey` constructor
- In `_create_block_geometry_analysis_sheet()`: Update similar iteration patterns
- In `_create_annotations_analysis_sheet()`: Update unpacking of `annotation_data` keys to use field access (e.g., `key.annotation_contents`, `key.annotation_type`)

Add imports for the new dataclass types from `types.py`.

### Step 6: Update test_extractor.py Test Assertions

Update `app/tests/core/test_extractor.py`:

- Update tests that check tuple key structure to verify dataclass fields instead
- Update tests that construct keys for assertions to use dataclass instantiation
- Update tests that iterate over dict keys to use field access
- Key tests to update:
  - `test_block_layer_pairs_tuple_keys` - rename to `test_block_layer_pairs_dataclass_keys` and verify `BlockLayerKey` structure
  - `test_block_rotation_counts_tuple_keys` - rename to `test_block_rotation_counts_dataclass_keys` and verify `BlockRotationKey` structure
  - `test_block_rotation_counts_with_fixture` - update key construction: `result["block_rotation_counts"][BlockRotationKey(block_name="TEST_BLOCK", layer_name="LAYER_A", rotation_category="0")]`
  - `test_annotation_data_extraction` - update key structure verification for `AnnotationKey`
  - `test_annotation_data_grouping_by_content` - update key access to use `key.annotation_contents`
  - `test_extract_xdata_from_blocks` - update key construction to use `BlockLayerKey`

Add imports for the new dataclass types.

### Step 7: Update test_excel_writer.py Test Data

Update `app/tests/core/test_excel_writer.py`:

- Update any mock `ExtractionResult` data construction to use dataclass keys
- Verify tests still pass with new key types

Add imports for the new dataclass types.

### Step 8: Run Validation Commands

Execute every command to validate the chore is complete with zero regressions.

## Validation Commands

Execute every command to validate the chore is complete with zero regressions.

- `uv run mypy app/` - Run type checker to verify all type annotations are correct with new dataclass keys
- `uv run pytest app/tests/` - Run all tests to verify zero regressions from key type changes
- `uv run ruff check app/` - Run linter to verify code style compliance

## Notes

- **Naming Convention Compliance**: All new code follows `ai_docs/001-naming-convention-guide.md` (PascalCase classes, snake_case fields, descriptive names) and `app_docs/005-field-naming-convention.md` (domain prefixes where needed for clarity)
- **Field Naming Strategy**: Dataclass field names match existing patterns in `ColorAnalysisRecord` for consistency - use `annotation_contents`, `annotation_type`, `color_r/g/b`, `entity_type`, `layer_name`
- **Frozen Dataclass Requirement**: `@dataclass(frozen=True)` is required because mutable dataclasses cannot be used as dictionary keys (not hashable)
- **Backward Compatibility**: The frozen dataclass approach maintains dict operations since frozen dataclasses are hashable
- **Keyword Arguments**: Always use keyword arguments when constructing dataclass instances for clarity (e.g., `BlockLayerKey(block_name="X", layer_name="Y")` not `BlockLayerKey("X", "Y")`)
- **Unchanged Types**: Simple counters (`dict[str, int]` like `block_counts`, `layer_entity_counts`) and TypedDicts (`ColorAnalysisRecord`, `BlockTrimmingData`) remain unchanged as they are already semantic and well-documented
