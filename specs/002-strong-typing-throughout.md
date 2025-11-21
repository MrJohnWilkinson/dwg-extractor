# Chore: Ensure Strong Typing Throughout Codebase

## Chore Description
Audit and enhance the codebase to use strong typing consistently throughout all Python files. The codebase currently passes mypy with `disallow_untyped_defs = true`, but there are opportunities to strengthen typing further by:
1. Enabling additional mypy strict mode flags
2. Replacing `Any` types with more specific types where possible
3. Adding TypedDict definitions for internal data structures
4. Improving type annotations in test files for better IDE support and documentation

## Relevant Files
Use these files to resolve the chore:

### Core Application Files
- `app/core/extractor.py` - Uses `Any` type for ezdxf entities and some dict values; needs more specific typing where feasible
- `app/core/excel_writer.py` - Uses `pd.ExcelWriter` without type parameters; has internal helper functions that could use more precise types
- `app/core/excel_formatting.py` - Well-typed but uses `object` in `_is_negative_number`; could be more specific
- `app/core/geometry.py` - Uses `BlockLayout` from ezdxf; well-typed overall
- `app/core/constants.py` - All string constants; well-typed
- `app/core/logger.py` - Returns `logging.Logger`; well-typed
- `app/main.py` - GUI code with customtkinter (no stubs available); reasonably typed

### Configuration Files
- `pyproject.toml` - Contains mypy configuration; needs additional strict flags enabled

### Test Files
- `app/tests/core/test_extractor.py` - Test functions are typed but could benefit from more explicit fixture typing
- `app/tests/core/test_excel_writer.py` - Has good typing with `ExtractionResult` fixture
- `app/tests/core/test_excel_formatting.py` - Well-typed test module
- `app/tests/core/test_geometry.py` - Needs review for typing consistency

### New Files
- `app/core/types.py` - New file to define shared TypedDict definitions for internal data structures like `BlockTrimmingData`, `ColorAnalysisRecord`

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### 1. Create shared types module
- Create `app/core/types.py` to define TypedDict classes for commonly used data structures:
  - `BlockTrimmingData` for the geometry analysis dict structure (native_width, native_height, vertical_segments, horizontal_segments)
  - `ColorAnalysisRecord` for the color analysis list items
- Export these types in `app/core/__init__.py`

### 2. Update pyproject.toml with stricter mypy flags
- Add additional strict mode flags that are feasible:
  - `strict_equality = true` - Check equality comparisons
  - `warn_redundant_casts = true` - Warn on unnecessary casts
  - `warn_unused_ignores = true` - Warn on unused type: ignore comments
  - `no_implicit_reexport = true` - Require explicit re-exports
- Keep `ignore_missing_imports = true` for ezdxf and customtkinter overrides (these libraries lack complete type stubs)

### 3. Update extractor.py to use precise types
- Import new TypedDict definitions from `types.py`
- Replace `dict[str, Any]` with `BlockTrimmingData` in the `ExtractionResult` TypedDict
- Replace `list[dict[str, Any]]` with `list[ColorAnalysisRecord]` in `ExtractionResult`
- Update return type of `extract_color_analysis` to `list[ColorAnalysisRecord]`
- Keep `Any` for ezdxf entity types (no stubs available) but document why in comments

### 4. Update excel_writer.py to use precise types
- Import TypedDict definitions from `types.py`
- Add explicit type annotation for the `format_number` nested function parameter
- Ensure all helper function parameters have explicit types

### 5. Update excel_formatting.py parameter type
- Change `_is_negative_number(value: object)` to use a more specific union type: `int | float | str | None`

### 6. Fix unused type: ignore comment in test file
- In `app/tests/core/test_excel_writer.py:799`, remove or update the unused `type: ignore` comment
- Add proper type parameters for generic dict if needed

### 7. Run validation and fix any remaining issues
- Run mypy with updated config
- Fix any new errors introduced by stricter settings
- Ensure all tests still pass

## Validation Commands
Execute every command to validate the chore is complete with zero regressions.

- `uv run mypy app/` - Run mypy type checker with updated strict config - must pass with 0 errors
- `uv run pytest app/tests/ -v` - Run full test suite to verify no regressions
- `uv run ruff check app/` - Run linter to ensure code style compliance
- `uv run ruff format app/ --check` - Verify code formatting

## Notes
- The ezdxf and customtkinter libraries lack complete type stubs, so we must use `ignore_missing_imports = true` for their module overrides. This is a known limitation.
- The `Any` type is acceptable for ezdxf entity parameters (`entity: Any`) since ezdxf doesn't export typed entity classes.
- Full mypy `--strict` mode produces ~42 errors, mostly from ezdxf missing exports. The goal is to enable as many strict flags as possible while excluding those that conflict with untyped library dependencies.
- The GUI code in `main.py` uses customtkinter which has no type stubs; the `Class cannot subclass "CTk"` error from strict mode is expected and acceptable.
