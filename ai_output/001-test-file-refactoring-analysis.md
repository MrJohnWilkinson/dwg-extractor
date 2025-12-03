# Test File Refactoring Analysis

## Executive Summary
Three test files exceed 1000 lines: `test_extractor.py` (2460), `test_excel_writer.py` (2435), and `test_excel_formatting.py` (1657). Each file contains multiple test classes organized by feature area. The recommended refactoring approach splits each file by test class into separate modules within feature-specific subdirectories, following pytest conventions and existing naming patterns.

## Table Summary

| File | Lines | Test Classes | Tests | Recommended Split |
|------|-------|--------------|-------|-------------------|
| `test_extractor.py` | 2460 | 7 | 126 | 7 modules by feature |
| `test_excel_writer.py` | 2435 | 8 | 81 | 4 modules by feature |
| `test_excel_formatting.py` | 1657 | 7 | 49 | 4 modules by feature |

## Relevant Files

- `app/tests/core/test_extractor.py` - Main extractor tests with 7 test classes covering extraction, color, mtext, true color, hatch, ACI, and dynamic blocks
- `app/tests/core/test_excel_writer.py` - Excel writer tests with 8 test classes covering writer, negative scale, annotations, ACI, color analysis, and extraction issues
- `app/tests/core/test_excel_formatting.py` - Excel formatting tests with 7 test classes covering header formatting, sheet-specific formatting, and negative scale highlighting
- `ai_docs/001-naming-convention-guide.md` - Project naming conventions to follow during refactoring

## Current Test Class Distribution

### test_extractor.py (2460 lines, 126 tests)
| Class | Line Start | Tests | Recommended Module |
|-------|-----------|-------|-------------------|
| `TestExtractor` | 33 | ~30 | `test_extractor_core.py` |
| `TestColorAnalysis` | 1183 | ~20 | `test_extractor_color.py` |
| `TestMtextFormatting` | 1438 | ~15 | `test_extractor_mtext.py` |
| `TestTrueColorExtraction` | 1728 | ~15 | `test_extractor_color.py` |
| `TestHatchExtraction` | 1954 | ~10 | `test_extractor_hatch.py` |
| `TestAciExtraction` | 2113 | ~10 | `test_extractor_color.py` |
| `TestDynamicBlockExtraction` | 2273 | ~10 | `test_extractor_dynamic.py` |

### test_excel_writer.py (2435 lines, 81 tests)
| Class | Line Start | Tests | Recommended Module |
|-------|-----------|-------|-------------------|
| `TestExcelWriter` | 62 | ~50 | `test_excel_writer_core.py` |
| `TestNegativeScaleDetection` | 1332 | ~5 | `test_excel_writer_scale.py` |
| `TestNegativeScaleTextGeneration` | 1387 | ~10 | `test_excel_writer_scale.py` |
| `TestNegativeScaleIntegration` | 1617 | ~5 | `test_excel_writer_scale.py` |
| `TestAnnotationsAnalysisSheet` | 1734 | ~10 | `test_excel_writer_annotations.py` |
| `TestAciDisplayNameMapping` | 1993 | ~3 | `test_excel_writer_color.py` |
| `TestColorAnalysisExcelOutput` | 2046 | ~8 | `test_excel_writer_color.py` |
| `TestExtractionIssuesSheet` | 2195 | ~8 | `test_excel_writer_issues.py` |

### test_excel_formatting.py (1657 lines, 49 tests)
| Class | Line Start | Tests | Recommended Module |
|-------|-----------|-------|-------------------|
| `TestFormatHeader` | 35 | ~12 | `test_formatting_header.py` |
| `TestBlockAnalysisFormatting` | 92 | ~4 | `test_formatting_sheets.py` |
| `TestLayerAnalysisFormatting` | 165 | ~4 | `test_formatting_sheets.py` |
| `TestEntitySummaryFormatting` | 249 | ~4 | `test_formatting_sheets.py` |
| `TestBlockGeometryAnalysisFormatting` | 305 | ~10 | `test_formatting_sheets.py` |
| `TestNegativeScaleHighlighting` | 930 | ~12 | `test_formatting_scale.py` |
| `TestAnnotationsAnalysisFormatting` | 1353 | ~10 | `test_formatting_annotations.py` |

## Proposed Directory Structure

```
app/tests/core/
├── __init__.py
├── extractor/                          # NEW subdirectory
│   ├── __init__.py
│   ├── test_extractor_core.py          # TestExtractor class
│   ├── test_extractor_color.py         # TestColorAnalysis, TestTrueColorExtraction, TestAciExtraction
│   ├── test_extractor_mtext.py         # TestMtextFormatting
│   ├── test_extractor_hatch.py         # TestHatchExtraction
│   └── test_extractor_dynamic.py       # TestDynamicBlockExtraction
├── excel_writer/                       # NEW subdirectory
│   ├── __init__.py
│   ├── test_excel_writer_core.py       # TestExcelWriter class
│   ├── test_excel_writer_scale.py      # TestNegativeScale* classes
│   ├── test_excel_writer_annotations.py # TestAnnotationsAnalysisSheet
│   ├── test_excel_writer_color.py      # TestAciDisplayNameMapping, TestColorAnalysisExcelOutput
│   └── test_excel_writer_issues.py     # TestExtractionIssuesSheet
├── excel_formatting/                   # NEW subdirectory
│   ├── __init__.py
│   ├── test_formatting_header.py       # TestFormatHeader
│   ├── test_formatting_sheets.py       # TestBlockAnalysis/Layer/Entity/Geometry Formatting
│   ├── test_formatting_scale.py        # TestNegativeScaleHighlighting
│   └── test_formatting_annotations.py  # TestAnnotationsAnalysisFormatting
├── test_geometry.py                    # Keep as-is (447 lines)
└── test_logger.py                      # Keep as-is (328 lines)
```

## Naming Pattern Analysis

Current naming follows the pattern:
- Test file: `test_{module_name}.py`
- Test class: `Test{FeatureName}` (PascalCase)
- Test method: `test_{specific_behavior}` (snake_case)

Proposed naming extends this pattern:
- Test subdirectory: `{module_name}/` (matches source module)
- Test file: `test_{module_name}_{feature}.py`

## Recommendations

1. **Create subdirectories** for each major test file to group related tests
2. **Group related test classes** - Combine classes testing the same feature area (e.g., all color-related tests)
3. **Maintain shared fixtures** - Move common fixtures to `conftest.py` files in each subdirectory
4. **Update imports** - Each new module will need its own imports from `core.*` modules
5. **Keep backward compatibility** - Run `pytest app/tests/` from project root unchanged

## Estimated Line Counts After Split

| New Module | Estimated Lines | Under 1000? |
|------------|-----------------|-------------|
| `extractor/test_extractor_core.py` | ~600 | Yes |
| `extractor/test_extractor_color.py` | ~700 | Yes |
| `extractor/test_extractor_mtext.py` | ~300 | Yes |
| `extractor/test_extractor_hatch.py` | ~200 | Yes |
| `extractor/test_extractor_dynamic.py` | ~200 | Yes |
| `excel_writer/test_excel_writer_core.py` | ~800 | Yes |
| `excel_writer/test_excel_writer_scale.py` | ~400 | Yes |
| `excel_writer/test_excel_writer_annotations.py` | ~300 | Yes |
| `excel_writer/test_excel_writer_color.py` | ~200 | Yes |
| `excel_writer/test_excel_writer_issues.py` | ~250 | Yes |
| `excel_formatting/test_formatting_header.py` | ~100 | Yes |
| `excel_formatting/test_formatting_sheets.py` | ~650 | Yes |
| `excel_formatting/test_formatting_scale.py` | ~450 | Yes |
| `excel_formatting/test_formatting_annotations.py` | ~350 | Yes |

## Next Steps

1. Create subdirectory structure under `app/tests/core/`
2. Create `conftest.py` files with shared fixtures (e.g., `temp_dir`, `sample_extraction_data`)
3. Split `test_extractor.py` into 5 modules
4. Split `test_excel_writer.py` into 5 modules
5. Split `test_excel_formatting.py` into 4 modules
6. Remove original large test files
7. Run `uv run pytest app/tests/` to verify all tests pass
8. Run `uv run pytest --cov=app/core app/tests/` to verify coverage unchanged
