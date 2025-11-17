# Excel Field Naming Strategy for Scalable CAD Analysis

## Executive Summary
This report defines a future-proof, scalable naming convention for all current and planned Excel output fields in the DWG Block Extractor. The naming strategy follows Python/PostgreSQL conventions (snake_case for data, Title Case for headers) and supports expansion into block-layer relationships, rotation analysis, multi-layer placement tracking, and dimensional analysis while maintaining consistency with existing codebase standards.

## Table Summary

| Category | Field Purpose | Data Name (Python) | Excel Header | Sheet Location | Status |
|----------|---------------|-------------------|--------------|----------------|--------|
| Block Basics | Block identifier | `block_name` | Block Name | Block Counts | Implemented |
| Block Basics | Times block inserted | `block_insertion_count` | Insertion Count | Block Counts | Implemented |
| Block Basics | Entities in block def | `block_entity_count` | Entities in Definition | Block Counts | Implemented |
| Block Advanced | Block rotation values | `block_rotation_angles` | Rotation Angles | Block Details | Planned |
| Block Advanced | Unique rotation count | `block_unique_rotation_count` | Unique Rotations | Block Details | Planned |
| Block Advanced | Block scale factors | `block_scale_factors` | Scale Factors | Block Details | Planned |
| Block Advanced | X/Y insertion points | `block_insertion_positions` | Insertion Positions | Block Details | Planned |
| Block-Layer | Block on specific layer | `block_layer_names` | Layers Used | Block Details | Planned |
| Block-Layer | Block insertions per layer | `block_layer_insertion_counts` | Insertions by Layer | Block-Layer Matrix | Planned |
| Block-Layer | Dominant layer for block | `block_primary_layer` | Primary Layer | Block Counts | Planned |
| Layer Basics | Layer identifier | `layer_name` | Layer Name | Layer Analysis | Implemented |
| Layer Basics | Insertions on layer | `layer_insertion_count` | Insertions on Layer | Layer Analysis | Implemented |
| Layer Basics | All entities on layer | `layer_entity_count` | Entities on Layer | Layer Analysis | Implemented |
| Layer Advanced | Layer color code | `layer_color_index` | Color Index | Layer Properties | Planned |
| Layer Advanced | Layer line weight | `layer_lineweight` | Lineweight | Layer Properties | Planned |
| Layer Advanced | Layer visibility | `layer_is_frozen` | Is Frozen | Layer Properties | Planned |
| Layer Advanced | Layer lock status | `layer_is_locked` | Is Locked | Layer Properties | Planned |
| Entity Basics | Entity type name | `entity_type_name` | Entity Type | Entity Summary | Implemented |
| Entity Basics | Total entity count | `entity_type_count` | Total Count | Entity Summary | Implemented |
| Entity Advanced | Entity color usage | `entity_color_counts` | Color Distribution | Entity Properties | Planned |
| Entity Advanced | Entity linetype usage | `entity_linetype_counts` | Linetype Distribution | Entity Properties | Planned |

## Relevant Files

- **app/core/constants.py** - Contains all Excel column header constants and sheet names. This is the central registry for field naming and should be updated whenever new fields are added. Currently defines 11 constants for 3 sheets.

- **app/core/extractor.py** - Defines the `ExtractionResult` TypedDict which is the canonical data structure. All new data fields must be added here with proper type hints before being used in Excel output.

- **app/core/excel_writer.py** - Consumes data from extractor and maps Python field names to Excel column headers using constants. New sheets or columns require new formatting functions.

- **ai_docs/001-naming-convention-guide.md** - The authoritative naming convention guide that this strategy follows. Specifies snake_case for Python/SQL, Title Case for display names, and descriptive naming principles.

- **specs/014-three-tab-excel-output.md** - Recent feature spec that established the current three-sheet architecture (Block Counts, Layer Analysis, Entity Summary). Future enhancements should align with this pattern.

## Naming Convention Principles

### Python Data Field Names (Internal)
Following Python/PostgreSQL conventions from naming guide:

**Pattern:** `{domain}_{attribute}[_{qualifier}]`

- **domain**: Primary entity (block, layer, entity)
- **attribute**: What is being measured (name, count, rotation, position)
- **qualifier**: Optional specificity (insertion, definition, primary, unique)

**Examples:**
- `block_insertion_count` - How many times a block is inserted
- `block_entity_count` - Entities within block definition
- `block_layer_names` - Which layers a block appears on (plural = list/array)
- `block_rotation_angles` - All rotation values for block insertions (plural = list)
- `block_unique_rotation_count` - Count of distinct rotation values
- `layer_insertion_count` - Block insertions on a specific layer
- `entity_type_count` - Count of entities of a specific type

**Key Rules:**
- Use full words, no abbreviations (except universal: `id`, `count`, `max`, `min`)
- Boolean fields: `is_`, `has_`, `can_` prefix
- Counts: `_count` suffix (singular) or `_total` for aggregations
- Collections: plural suffix (`_names`, `_values`, `_angles`, `_positions`)
- Per-item basis: `_per_layer`, `_per_block` suffix

### Excel Column Headers (User-Facing)
Following Title Case convention for readability:

**Pattern:** `{Entity} {Attribute} [Qualifier]`

**Examples:**
- "Block Name" (identifier)
- "Insertion Count" (how many)
- "Entities in Definition" (qualifier specifies scope)
- "Rotation Angles" (collection of values)
- "Unique Rotations" (distinct count)
- "Insertions on Layer" (qualifier: on layer)
- "Insertions by Layer" (breakdown dimension)
- "Primary Layer" (dominant/most common)

**Key Rules:**
- Use prepositions for clarity: "on Layer", "in Definition", "by Layer"
- Avoid abbreviations in headers (spell out everything)
- Keep headers scannable (2-4 words ideal, 5 max)
- Use "Count" when ambiguous, omit when obvious from context

### Sheet Naming Strategy
Current pattern: `{Analysis Type}` (e.g., "Block Counts", "Layer Analysis")

**Future Sheets:**
- "Block Details" - Extended block analysis (rotations, scales, positions)
- "Block-Layer Matrix" - Cross-tabulation of blocks vs layers
- "Layer Properties" - Layer metadata (colors, linetypes, states)
- "Entity Properties" - Entity metadata beyond counts
- "Drawing Metadata" - File-level properties (units, limits, date)

## Field Taxonomy by Domain

### Block Domain Fields

#### Basic Block Fields (Implemented)
```python
# In ExtractionResult TypedDict
block_counts: dict[str, int]           # Excel: "Block Name" -> "Insertion Count"
block_entities: dict[str, int]         # Excel: "Block Name" -> "Entities in Definition"
```

#### Extended Block Fields (Planned)
```python
# Rotation analysis
block_rotation_angles: dict[str, list[float]]           # All rotation values per block
block_unique_rotation_count: dict[str, int]             # Count of distinct rotations
block_has_uniform_rotation: dict[str, bool]             # True if all same rotation
block_rotation_min: dict[str, float]                    # Minimum rotation angle
block_rotation_max: dict[str, float]                    # Maximum rotation angle
block_rotation_mean: dict[str, float]                   # Average rotation angle

# Scale analysis
block_scale_factors: dict[str, list[tuple[float, float, float]]]  # (x, y, z) scales
block_unique_scale_count: dict[str, int]                # Count of distinct scales
block_has_uniform_scale: dict[str, bool]                # True if all same scale
block_is_mirrored: dict[str, bool]                      # True if any negative scales

# Position analysis
block_insertion_positions: dict[str, list[tuple[float, float, float]]]  # (x, y, z)
block_bounding_box_min: dict[str, tuple[float, float]]  # Min (x, y) extent
block_bounding_box_max: dict[str, tuple[float, float]]  # Max (x, y) extent
block_spatial_distribution: dict[str, str]              # "clustered" | "distributed" | "linear"

# Layer relationships
block_layer_names: dict[str, list[str]]                 # All layers block appears on
block_unique_layer_count: dict[str, int]                # Count of distinct layers
block_primary_layer: dict[str, str]                     # Layer with most insertions
block_layer_insertion_counts: dict[str, dict[str, int]] # Nested: block -> layer -> count

# Complexity metrics
block_total_entity_count: dict[str, int]                # insertion_count × entity_count
block_complexity_score: dict[str, float]                # Weighted complexity metric
block_has_attributes: dict[str, bool]                   # True if contains ATTDEFs
block_attribute_count: dict[str, int]                   # Number of ATTDEF entities
```

**Excel Headers for Block Domain:**
- "Rotation Angles" (list display or summary)
- "Unique Rotations" (count)
- "Has Uniform Rotation" (Yes/No)
- "Rotation Range" (min-max display)
- "Average Rotation" (degrees)
- "Scale Factors" (list or summary)
- "Is Mirrored" (Yes/No)
- "Insertion Positions" (coordinate list or summary)
- "Bounding Box" (extent display)
- "Spatial Distribution" (categorical)
- "Layers Used" (comma-separated list)
- "Layer Count" (distinct count)
- "Primary Layer" (most common)
- "Total Entities" (insertion × definition)
- "Complexity Score" (calculated metric)
- "Has Attributes" (Yes/No)
- "Attribute Count" (number)

### Layer Domain Fields

#### Basic Layer Fields (Implemented)
```python
# In ExtractionResult TypedDict
layer_insertions: dict[str, int]       # Excel: "Layer Name" -> "Insertions on Layer"
layer_entities: dict[str, int]         # Excel: "Layer Name" -> "Entities on Layer"
```

#### Extended Layer Fields (Planned)
```python
# Block distribution on layers
layer_block_types: dict[str, list[str]]                 # All unique blocks on layer
layer_unique_block_count: dict[str, int]                # Count of distinct blocks
layer_dominant_block: dict[str, str]                    # Most inserted block on layer
layer_block_insertion_counts: dict[str, dict[str, int]] # Nested: layer -> block -> count

# Layer properties
layer_color_index: dict[str, int]                       # AutoCAD color index (0-256)
layer_color_name: dict[str, str]                        # Color name if standard
layer_lineweight: dict[str, float]                      # Line weight in mm
layer_linetype: dict[str, str]                          # Linetype name (CONTINUOUS, etc.)
layer_is_frozen: dict[str, bool]                        # Frozen state
layer_is_locked: dict[str, bool]                        # Locked state
layer_is_off: dict[str, bool]                           # Visibility off
layer_plot_style: dict[str, str]                        # Plot style name

# Entity type distribution on layers
layer_entity_type_counts: dict[str, dict[str, int]]     # Nested: layer -> entity_type -> count
layer_dominant_entity_type: dict[str, str]              # Most common entity type on layer
layer_has_insertions: dict[str, bool]                   # True if any INSERT entities
layer_insertion_percentage: dict[str, float]            # insertions / total_entities

# Complexity metrics
layer_density_score: dict[str, float]                   # Entities per unit area estimate
layer_complexity_category: dict[str, str]               # "simple" | "moderate" | "complex"
```

**Excel Headers for Layer Domain:**
- "Block Types" (comma-separated)
- "Unique Blocks" (count)
- "Dominant Block" (most common)
- "Block Distribution" (breakdown or chart)
- "Color Index" (ACI number)
- "Color Name" (text)
- "Lineweight" (mm)
- "Linetype" (name)
- "Is Frozen" (Yes/No)
- "Is Locked" (Yes/No)
- "Is Off" (Yes/No)
- "Plot Style" (name)
- "Entity Type Distribution" (breakdown)
- "Dominant Entity Type" (most common)
- "Has Blocks" (Yes/No)
- "Insertion Percentage" (%)
- "Density Score" (metric)
- "Complexity Category" (categorical)

### Entity Domain Fields

#### Basic Entity Fields (Implemented)
```python
# In ExtractionResult TypedDict
entity_types: dict[str, int]           # Excel: "Entity Type" -> "Total Count"
```

#### Extended Entity Fields (Planned)
```python
# Entity distribution analysis
entity_layer_counts: dict[str, dict[str, int]]          # Nested: entity_type -> layer -> count
entity_dominant_layer: dict[str, str]                   # Layer with most of this entity type
entity_layer_percentage: dict[str, dict[str, float]]    # Distribution as percentages

# Entity properties (aggregated)
entity_color_counts: dict[str, dict[int, int]]          # entity_type -> color_index -> count
entity_linetype_counts: dict[str, dict[str, int]]       # entity_type -> linetype -> count
entity_lineweight_counts: dict[str, dict[float, int]]   # entity_type -> lineweight -> count

# Geometric entity specifics
line_total_length: float                                # Sum of all LINE lengths
arc_total_length: float                                 # Sum of all ARC lengths
circle_radius_distribution: dict[float, int]            # radius -> count
polyline_vertex_counts: dict[int, int]                  # vertex_count -> polyline_count
text_height_distribution: dict[float, int]              # height -> count
```

**Excel Headers for Entity Domain:**
- "Layer Distribution" (breakdown by layer)
- "Dominant Layer" (most common)
- "Layer Percentage" (distribution %)
- "Color Distribution" (by color index)
- "Linetype Distribution" (by linetype)
- "Lineweight Distribution" (by weight)
- "Total Line Length" (units)
- "Total Arc Length" (units)
- "Circle Radius Distribution" (histogram data)
- "Polyline Vertex Counts" (distribution)
- "Text Height Distribution" (histogram data)

### Cross-Domain Fields (Block-Layer Relationships)

These fields represent many-to-many relationships and would appear in dedicated "Block-Layer Matrix" sheet:

```python
# Pivot table data structure
block_layer_matrix: dict[str, dict[str, int]]           # block -> layer -> insertion_count

# Summary metrics derived from matrix
total_block_layer_combinations: int                     # Count of unique combinations
blocks_on_multiple_layers: list[str]                    # Blocks appearing on 2+ layers
layers_with_multiple_blocks: list[str]                  # Layers containing 2+ block types
most_diverse_block: str                                 # Block on most layers
most_diverse_layer: str                                 # Layer with most block types
```

**Excel Headers for Block-Layer Matrix:**
- Rows: Block names
- Columns: Layer names (dynamic)
- Cells: Insertion count for that block-layer combination
- Summary row: "Total Insertions per Layer"
- Summary column: "Total Insertions per Block"

## Implementation Roadmap

### Phase 1: Current State (Implemented)
- 3 sheets: Block Counts, Layer Analysis, Entity Summary
- 11 data fields total
- Basic counting only

### Phase 2: Block Details Enhancement (Next Priority)
**New Fields to Add:**
- `block_layer_names` - List of layers block appears on
- `block_unique_layer_count` - Count of distinct layers
- `block_primary_layer` - Most common layer for block
- `block_rotation_angles` - All rotation values (for future detailed analysis)

**New Sheet:** "Block Details"
**Excel Columns:** Block Name | Insertion Count | Layers Used | Layer Count | Primary Layer

**Rationale:** Solves immediate user request for "which layer(s) a block is inserted on"

### Phase 3: Rotation & Transform Analysis
**New Fields to Add:**
- `block_unique_rotation_count` - Count distinct rotations
- `block_rotation_min`, `block_rotation_max`, `block_rotation_mean`
- `block_has_uniform_rotation` - Boolean flag
- `block_scale_factors` - Scale analysis

**Enhancement:** Expand "Block Details" sheet
**Excel Columns:** Add: Unique Rotations | Rotation Range | Avg Rotation | Has Uniform Rotation

**Rationale:** Addresses "I will need block rotations at some point"

### Phase 4: Block-Layer Matrix
**New Fields to Add:**
- `block_layer_matrix` - Nested dictionary for pivot table
- `block_layer_insertion_counts` - Per-block layer breakdown

**New Sheet:** "Block-Layer Matrix"
**Format:** Pivot table with blocks as rows, layers as columns, insertion counts as values

**Rationale:** Solves "how many times a block is used in a layer"

### Phase 5: Layer Properties & Advanced Analysis
**New Fields to Add:**
- `layer_color_index`, `layer_lineweight`, `layer_linetype`
- `layer_is_frozen`, `layer_is_locked`, `layer_is_off`
- `layer_block_types`, `layer_unique_block_count`

**New Sheet:** "Layer Properties"
**Excel Columns:** Layer Name | Color | Lineweight | Linetype | Block Types | Unique Blocks | Is Frozen | Is Locked

### Phase 6: Geometric Analysis
**New Fields to Add:**
- `block_insertion_positions` - XYZ coordinates
- `block_bounding_box_min`, `block_bounding_box_max`
- `line_total_length`, `arc_total_length`
- `circle_radius_distribution`, `polyline_vertex_counts`

**Enhancement:** Add geometric metrics to existing sheets or create "Geometric Analysis" sheet

## Constant Naming Convention

### In app/core/constants.py

**Sheet Names:**
```python
# Current (implemented)
EXCEL_SHEET_BLOCK_COUNTS: str = 'Block Counts'
EXCEL_SHEET_LAYER_ANALYSIS: str = 'Layer Analysis'
EXCEL_SHEET_ENTITY_SUMMARY: str = 'Entity Summary'

# Planned
EXCEL_SHEET_BLOCK_DETAILS: str = 'Block Details'
EXCEL_SHEET_BLOCK_LAYER_MATRIX: str = 'Block-Layer Matrix'
EXCEL_SHEET_LAYER_PROPERTIES: str = 'Layer Properties'
EXCEL_SHEET_ENTITY_PROPERTIES: str = 'Entity Properties'
EXCEL_SHEET_DRAWING_METADATA: str = 'Drawing Metadata'
```

**Column Headers - Naming Pattern:**
`EXCEL_COLUMN_{FIELD_PURPOSE}` where FIELD_PURPOSE uses UPPER_SNAKE_CASE

```python
# Block domain columns
EXCEL_COLUMN_BLOCK_NAME: str = 'Block Name'
EXCEL_COLUMN_BLOCK_INSERTION_COUNT: str = 'Insertion Count'
EXCEL_COLUMN_BLOCK_ENTITY_COUNT: str = 'Entities in Definition'
EXCEL_COLUMN_BLOCK_LAYERS_USED: str = 'Layers Used'
EXCEL_COLUMN_BLOCK_LAYER_COUNT: str = 'Layer Count'
EXCEL_COLUMN_BLOCK_PRIMARY_LAYER: str = 'Primary Layer'
EXCEL_COLUMN_BLOCK_ROTATION_ANGLES: str = 'Rotation Angles'
EXCEL_COLUMN_BLOCK_UNIQUE_ROTATIONS: str = 'Unique Rotations'
EXCEL_COLUMN_BLOCK_ROTATION_RANGE: str = 'Rotation Range'
EXCEL_COLUMN_BLOCK_AVG_ROTATION: str = 'Average Rotation'
EXCEL_COLUMN_BLOCK_UNIFORM_ROTATION: str = 'Has Uniform Rotation'
EXCEL_COLUMN_BLOCK_SCALE_FACTORS: str = 'Scale Factors'
EXCEL_COLUMN_BLOCK_IS_MIRRORED: str = 'Is Mirrored'
EXCEL_COLUMN_BLOCK_POSITIONS: str = 'Insertion Positions'
EXCEL_COLUMN_BLOCK_BOUNDING_BOX: str = 'Bounding Box'

# Layer domain columns
EXCEL_COLUMN_LAYER_NAME: str = 'Layer Name'
EXCEL_COLUMN_LAYER_INSERTION_COUNT: str = 'Insertions on Layer'
EXCEL_COLUMN_LAYER_ENTITY_COUNT: str = 'Entities on Layer'
EXCEL_COLUMN_LAYER_BLOCK_TYPES: str = 'Block Types'
EXCEL_COLUMN_LAYER_UNIQUE_BLOCKS: str = 'Unique Blocks'
EXCEL_COLUMN_LAYER_DOMINANT_BLOCK: str = 'Dominant Block'
EXCEL_COLUMN_LAYER_COLOR_INDEX: str = 'Color Index'
EXCEL_COLUMN_LAYER_COLOR_NAME: str = 'Color Name'
EXCEL_COLUMN_LAYER_LINEWEIGHT: str = 'Lineweight'
EXCEL_COLUMN_LAYER_LINETYPE: str = 'Linetype'
EXCEL_COLUMN_LAYER_IS_FROZEN: str = 'Is Frozen'
EXCEL_COLUMN_LAYER_IS_LOCKED: str = 'Is Locked'

# Entity domain columns
EXCEL_COLUMN_ENTITY_TYPE: str = 'Entity Type'
EXCEL_COLUMN_ENTITY_TOTAL_COUNT: str = 'Total Count'
EXCEL_COLUMN_ENTITY_DOMINANT_LAYER: str = 'Dominant Layer'
EXCEL_COLUMN_ENTITY_COLOR_DISTRIBUTION: str = 'Color Distribution'
EXCEL_COLUMN_ENTITY_LINETYPE_DISTRIBUTION: str = 'Linetype Distribution'
```

**Deprecation Strategy:**
When renaming existing constants, maintain backward compatibility:
```python
# New preferred name
EXCEL_COLUMN_BLOCK_INSERTION_COUNT: str = 'Insertion Count'

# Deprecated alias (remove in v2.0)
EXCEL_COLUMN_COUNT: str = EXCEL_COLUMN_BLOCK_INSERTION_COUNT  # Deprecated: use EXCEL_COLUMN_BLOCK_INSERTION_COUNT
```

## Data Type Conventions

### Simple Values
```python
block_name: str                        # Single identifier
block_insertion_count: int             # Simple count
layer_is_frozen: bool                  # Binary flag
block_complexity_score: float          # Calculated metric
```

### Collections
```python
block_layer_names: list[str]           # Ordered collection
block_rotation_angles: list[float]     # Value collection
layer_color_index: dict[str, int]      # Key-value mapping
block_layer_matrix: dict[str, dict[str, int]]  # Nested structure
```

### Type Hints in ExtractionResult
Always use complete type hints:
```python
class ExtractionResult(TypedDict):
    # Current fields
    block_counts: dict[str, int]
    block_entities: dict[str, int]
    layer_insertions: dict[str, int]
    layer_entities: dict[str, int]
    entity_types: dict[str, int]

    # Phase 2 additions
    block_layer_names: dict[str, list[str]]
    block_unique_layer_count: dict[str, int]
    block_primary_layer: dict[str, str]

    # Phase 3 additions
    block_rotation_angles: dict[str, list[float]]
    block_unique_rotation_count: dict[str, int]
    block_has_uniform_rotation: dict[str, bool]
```

## Excel Display Strategies

### List Fields in Excel
For fields containing lists (e.g., `block_layer_names: list[str]`):

**Option 1: Comma-separated string** (Recommended for short lists)
```python
df['Layers Used'] = block_layer_names.get(block_name, [])
# Convert list to comma-separated: ['Layer1', 'Layer2'] -> 'Layer1, Layer2'
df['Layers Used'] = df['Layers Used'].apply(lambda x: ', '.join(x) if x else '')
```

**Option 2: Count + Detail sheets** (Recommended for long lists)
- Main sheet shows count only: "Layer Count" = 5
- Detail sheet shows full breakdown with one row per block-layer combination

**Option 3: JSON or formatted text** (For complex nested data)
```python
# For block_rotation_angles with many values
'0°, 45°, 90°, 135° (4 unique)'
```

### Nested Dictionary Fields in Excel
For fields like `block_layer_matrix: dict[str, dict[str, int]]`:

**Option 1: Pivot table sheet** (Recommended)
- Rows = outer key (blocks)
- Columns = inner key (layers)
- Cells = values (insertion counts)

**Option 2: Flattened rows** (Alternative)
- Each combination gets own row: Block Name | Layer Name | Insertion Count

### Boolean Fields in Excel
Always use human-readable values:
```python
# NOT: True/False
# YES: 'Yes'/'No' or '✓'/'' (checkmark/empty)
df['Has Uniform Rotation'] = df['has_uniform_rotation'].apply(lambda x: 'Yes' if x else 'No')
```

## Recommendations

### Immediate Actions
1. **Standardize existing constants** - Rename current generic constants to domain-specific names:
   - `EXCEL_COLUMN_COUNT` → `EXCEL_COLUMN_BLOCK_INSERTION_COUNT`
   - `EXCEL_COLUMN_ENTITIES_IN_DEFINITION` → `EXCEL_COLUMN_BLOCK_ENTITY_COUNT`
   - `EXCEL_COLUMN_INSERTIONS_ON_LAYER` → `EXCEL_COLUMN_LAYER_INSERTION_COUNT`
   - `EXCEL_COLUMN_ENTITIES_ON_LAYER` → `EXCEL_COLUMN_LAYER_ENTITY_COUNT`
   - `EXCEL_COLUMN_TOTAL_COUNT` → `EXCEL_COLUMN_ENTITY_TOTAL_COUNT`

2. **Document field registry** - Maintain a central registry in constants.py with comments:
   ```python
   # ============================================================================
   # FIELD NAMING REGISTRY
   # ============================================================================
   # Pattern: EXCEL_COLUMN_{DOMAIN}_{ATTRIBUTE}[_{QUALIFIER}]
   # Domain: BLOCK | LAYER | ENTITY
   # Attribute: NAME | COUNT | ROTATION | SCALE | etc.
   # Qualifier: UNIQUE | PRIMARY | TOTAL | etc.
   # ============================================================================
   ```

3. **Create field expansion guide** - Document in ai_docs/ how to add new fields:
   - Step 1: Define Python field name in extractor.py TypedDict
   - Step 2: Add constant in constants.py following naming pattern
   - Step 3: Implement extraction logic in extractor.py
   - Step 4: Implement Excel mapping in excel_writer.py
   - Step 5: Add unit tests for new field

### Future-Proofing Strategies
1. **Use domain prefixes consistently** - Every field should start with domain (block_, layer_, entity_, drawing_)
2. **Avoid abbreviations** - Spell out full words except universal terms (id, count, max, min, avg)
3. **Plural for collections** - Use plural suffix when field contains list or array (_names, _angles, _values)
4. **Qualifier suffixes** - Add context with suffixes (_per_layer, _per_block, _in_definition, _on_layer)
5. **Boolean naming** - Prefix with is_, has_, can_ for boolean fields
6. **Aggregation suffix** - Use _count for single aggregation, _total for sum aggregation
7. **Reserve generic names** - Avoid "data", "value", "info" without domain prefix

### Testing Strategy for New Fields
When adding new fields, always test:
1. **Empty data** - Field with no values should gracefully show empty column
2. **Single value** - Field with one item should display correctly
3. **Multiple values** - Field with many items should format properly (truncate/paginate if needed)
4. **Null handling** - Missing data should show as empty string or "N/A", not error
5. **Type validation** - mypy should catch type mismatches

## Next Steps

1. **Implement Phase 2 fields** (Block-Layer relationship):
   - Add `block_layer_names`, `block_unique_layer_count`, `block_primary_layer` to ExtractionResult
   - Create extraction logic in `extract_blocks()` to track layers per block
   - Add constants for new columns
   - Create "Block Details" sheet or expand "Block Counts" sheet
   - Write unit tests for layer tracking per block

2. **Standardize existing constant names** (breaking change - coordinate with version bump):
   - Rename all 11 existing constants to use domain prefixes
   - Update all references in excel_writer.py
   - Add deprecated aliases for backward compatibility
   - Update tests to use new constant names

3. **Document ezdxf INSERT attributes**:
   - Research available properties: rotation, scale_x, scale_y, scale_z, insert position
   - Document how to access these in extraction logic
   - Plan implementation for Phase 3 rotation analysis

4. **Create field expansion template**:
   - Document the 5-step process for adding new fields
   - Create example showing end-to-end implementation
   - Add to ai_docs/ for future AI agent reference
