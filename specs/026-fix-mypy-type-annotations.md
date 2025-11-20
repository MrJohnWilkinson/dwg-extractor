# Chore: Fix mypy type annotation errors in test asset generator scripts

## Chore Description
Resolve three mypy type annotation errors in test asset generator scripts:
1. `create_comprehensive_scale_test_compact.py:17` - Missing return type annotation on main function
2. `create_comprehensive_scale_test_compact.py:123` - Missing type annotation for `row_descriptions` dictionary
3. `create_comprehensive_scale_test.py:15` - Missing return type annotation on main function

These are pre-existing issues in test asset generator scripts that need to be fixed to pass strict mypy type checking (`uv run mypy app/`).

## Relevant Files
Use these files to resolve the chore:

- `app/tests/assets/create_comprehensive_scale_test_compact.py` - Contains two type annotation errors:
  - Line 17: Function `create_comprehensive_scale_test_compact()` missing return type `-> None`
  - Line 123: Variable `row_descriptions` needs explicit type `dict[int, dict[str, str]]`

- `app/tests/assets/create_comprehensive_scale_test.py` - Contains one type annotation error:
  - Line 15: Function `create_comprehensive_scale_test()` missing return type `-> None`

- `app/tests/assets/create_negative_scale_test.py` - Reference file showing correct type annotation pattern (has `-> None` on line 19)

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### Fix type annotations in create_comprehensive_scale_test.py
- Add `-> None` return type annotation to the `create_comprehensive_scale_test()` function on line 15
- This function doesn't return a value, so `-> None` is the correct annotation
- Pattern: `def create_comprehensive_scale_test() -> None:`

### Fix type annotations in create_comprehensive_scale_test_compact.py
- Add `-> None` return type annotation to the `create_comprehensive_scale_test_compact()` function on line 17
- Add explicit type annotation to the `row_descriptions` variable on line 123
  - The variable stores row indices as keys and dictionaries of position labels ("left"/"right") to description strings as values
  - Correct type: `dict[int, dict[str, str]]`
  - Pattern: `row_descriptions: dict[int, dict[str, str]] = {}`

### Run validation commands
- Execute all validation commands listed below to confirm zero mypy errors and zero test regressions
- All commands must pass without errors

## Validation Commands
Execute every command to validate the chore is complete with zero regressions.

- `uv run mypy app/` - Run mypy type checking to confirm all type annotation errors are resolved
- `uv run pytest app/tests/core/` - Run unit tests to ensure no regressions in core functionality
- `uv run python app/tests/assets/create_comprehensive_scale_test.py` - Verify the script still executes correctly
- `uv run python app/tests/assets/create_comprehensive_scale_test_compact.py` - Verify the script still executes correctly

## Notes
- These scripts are test asset generators that create DXF files for testing block scale scenarios
- They are standalone scripts run via `uv run python <script>` and are not imported as modules
- The type annotations follow the pattern used in `create_negative_scale_test.py` which already has correct annotations
- The `row_descriptions` dict structure: `{row_index: {"left": "description", "right": "description"}}`
