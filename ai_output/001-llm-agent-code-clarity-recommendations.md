# LLM Agent Code Clarity Recommendations

## Executive Summary

Given that LLM agents handle maintenance tasks, the primary goal shifts from minimizing developer cognitive load to maximizing machine parseability. This report recommends adopting classes over dicts to provide explicit type contracts that LLMs can reliably interpret without inferring tuple index meanings.

## Table Summary

| Approach | LLM Benefit | Recommendation |
|----------|-------------|----------------|
| TypedDict (current) | Good - named fields, IDE hints | Keep for simple records |
| Dataclasses | Excellent - explicit fields, methods, defaults | Use for entities with behavior |
| Complex tuple keys | Poor - positional semantics hidden | Replace with frozen dataclasses |
| dict[str, int] counters | Good - clear intent | Keep as-is |
| Nested tuples in dict keys | Very Poor - requires comments to understand | Replace with hashable classes |

## Relevant Files

- **app/core/types.py**: Contains `BlockTrimmingData` and `ColorAnalysisRecord` TypedDicts - well-documented, LLM-friendly
- **app/core/extractor.py**: Contains `ExtractionResult` TypedDict and complex internal dict annotations - main refactoring target
- **app/core/excel_writer.py**: Consumes extraction results - benefits from typed inputs
- **app/core/geometry.py**: Pure utility functions - no dict/class changes needed

## Key Problem Areas for LLM Agents

The following tuple-keyed dicts require positional inference:

```python
# LLM must infer: (R, G, B, ACI, layer_name, entity_type)
geometric_entities: dict[tuple[int, int, int, int | None, str, str], int]

# LLM must infer: (contents, type, layer, r, g, b)
annotation_data: dict[tuple[str, str, str, int, int, int], int]

# LLM must infer: (block_name, layer_name, rotation_category)
block_rotation_counts: dict[tuple[str, str, str], int]
```

## Recommended Class Structure

```python
@dataclass(frozen=True)
class ColorKey:
    """Hashable color grouping key."""
    r: int
    g: int
    b: int
    aci: int | None
    layer_name: str
    entity_type: str

@dataclass(frozen=True)
class AnnotationKey:
    """Hashable annotation grouping key."""
    contents: str
    annotation_type: str  # 'TEXT' or 'MTEXT'
    layer_name: str
    r: int
    g: int
    b: int

@dataclass(frozen=True)
class BlockLayerKey:
    """Hashable block-layer pair."""
    block_name: str
    layer_name: str

@dataclass(frozen=True)
class BlockRotationKey:
    """Hashable block-layer-rotation combination."""
    block_name: str
    layer_name: str
    rotation_category: str  # '0', '90', '180', '270', 'other'
```

## Recommendations

1. **Replace tuple-keyed dicts with frozen dataclass keys** - Highest LLM clarity impact
2. **Keep simple counters as dict[str, int]** - Already clear and semantic
3. **Keep TypedDicts for records** - `ColorAnalysisRecord` and `BlockTrimmingData` are already well-documented
4. **Add docstrings to all new classes** - LLMs parse docstrings for semantic understanding
5. **Use descriptive field names** - `annotation_type` instead of `type` avoids Python keyword confusion

## Implementation Priority

| Priority | Change | Impact |
|----------|--------|--------|
| High | Replace `geometric_entities` tuple key with `ColorKey` class | Eliminates 6-tuple position inference |
| High | Replace `annotation_data` tuple key with `AnnotationKey` class | Eliminates 6-tuple position inference |
| Medium | Replace `block_rotation_counts` tuple key with `BlockRotationKey` | Eliminates 3-tuple inference |
| Medium | Replace `block_layer_pairs` tuple key with `BlockLayerKey` | Consistency improvement |
| Low | Keep TypedDicts as-is | Already LLM-friendly |

## Next Steps

1. Create new dataclass definitions in `app/core/types.py`
2. Update `extract_color_analysis()` to use `ColorKey` as dict key
3. Update `extract_blocks()` to use new key classes
4. Update `ExtractionResult` TypedDict to reference new key types
5. Run tests to verify no regressions
