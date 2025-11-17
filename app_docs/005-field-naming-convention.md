# Field Naming Convention

## Pattern
`{domain}_{attribute}[_{qualifier}]`

- **domain**: block, layer, entity
- **attribute**: name, count, rotation, position, color, etc.
- **qualifier**: insertion, definition, primary, unique, min, max, avg

## Rules
1. Full words only (except: id, count, max, min, avg, total)
2. Boolean fields: `is_`, `has_`, `can_` prefix
3. Single count: `_count` | Sum: `_total`
4. Collections: plural suffix (`_names`, `_values`, `_angles`)
5. All snake_case (Python and Excel use identical names)

## Block Domain Examples
```python
block_name                      # identifier
block_insertion_count           # times inserted
block_entity_count              # entities in definition
block_layer_names               # layers block appears on (list)
block_unique_layer_count        # distinct layer count
block_primary_layer             # layer with most insertions
block_rotation_angles           # all rotations (list)
block_unique_rotation_count     # distinct rotation count
block_has_uniform_rotation      # boolean
block_scale_factors             # (x,y,z) scales (list)
block_is_mirrored               # boolean
block_total_entity_count        # insertion_count × entity_count
```

## Layer Domain Examples
```python
layer_name                      # identifier
layer_block_insertion_count     # INSERT entities (block references) on layer
layer_entity_count              # all entities (INSERT, LINE, CIRCLE, etc.)
layer_block_names               # blocks on layer (list)
layer_unique_block_count        # distinct block count
layer_dominant_block            # most common block
layer_color_index               # ACI color (0-256)
layer_is_frozen                 # boolean
layer_is_locked                 # boolean
```

## Entity Domain Examples
```python
entity_type_name                # LINE, CIRCLE, ARC, etc.
entity_type_count               # total count
entity_dominant_layer           # layer with most of this type
```

## Constants Pattern
```python
# In app/core/constants.py
EXCEL_COLUMN_BLOCK_NAME: str = 'block_name'
EXCEL_COLUMN_BLOCK_INSERTION_COUNT: str = 'block_insertion_count'
EXCEL_COLUMN_LAYER_NAME: str = 'layer_name'
EXCEL_COLUMN_ENTITY_TYPE_NAME: str = 'entity_type_name'
```

## Avoid
❌ `count` (no domain)
❌ `blk_ins_cnt` (abbreviations)
❌ `block_layer_name` (singular for list)
✅ `block_insertion_count`
✅ `block_layer_names`

## Adding New Fields Checklist
1. Choose domain prefix (block_, layer_, entity_)
2. Add descriptive attribute (full words)
3. Add qualifier if needed (_count, _unique, _primary)
4. Plural for collections (_names, _angles)
5. Add to ExtractionResult TypedDict
6. Add EXCEL_COLUMN_ constant
7. Implement extraction logic
8. Write unit tests
