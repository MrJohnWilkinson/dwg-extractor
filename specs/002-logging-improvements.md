# Chore: Logging Improvements

## Chore Description
Enhance the existing logging system in `app/core/logger.py` with four improvements:
1. **Log Level Configuration** - Allow runtime configuration of log levels via environment variable
2. **Timing Decorator/Context Manager** - Add utilities to measure and log execution time of functions and code blocks
3. **DEBUG Statements at Key Points** - Add DEBUG-level logging throughout the extraction pipeline for troubleshooting
4. **Structured Logging Option (JSON)** - Add optional JSON output format for machine-parseable logs

## Relevant Files
Use these files to resolve the chore:

- `app/core/logger.py` - Main logging module to be enhanced; currently provides basic `setup_logger()` function with stdout-only output at INFO level
- `app/core/extractor.py` - Primary extraction logic; uses logger extensively for INFO-level messages; needs DEBUG statements added at key points
- `app/core/excel_writer.py` - Excel generation; uses logger for sheet creation progress; needs DEBUG statements for data processing
- `app/core/geometry.py` - Geometric calculations; currently has no logging; needs DEBUG statements for computation details
- `app/core/constants.py` - App constants; may need new constants for log-related configuration
- `app/main.py` - GUI entry point; uses logger for application lifecycle events
- `app/tests/core/test_extractor.py` - Extractor tests; verify no regressions
- `app/tests/core/test_excel_writer.py` - Excel writer tests; verify no regressions
- `app/tests/core/test_geometry.py` - Geometry tests; verify no regressions

### New Files
- `app/tests/core/test_logger.py` - New test file for logger functionality (timing decorator, JSON formatting, log level configuration)

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### Step 1: Add Log Level Configuration to `app/core/logger.py`
- Add import for `os` module
- Add constant `LOG_LEVEL_ENV_VAR = "DXF_EXTRACTOR_LOG_LEVEL"` for environment variable name
- Add constant `DEFAULT_LOG_LEVEL = "INFO"` for default level
- Add helper function `_get_log_level_from_env() -> int` that:
  - Reads `DXF_EXTRACTOR_LOG_LEVEL` environment variable
  - Validates against allowed values: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`
  - Returns corresponding `logging` constant (e.g., `logging.DEBUG`)
  - Falls back to `logging.INFO` if invalid or not set
- Update `setup_logger()` to use `_get_log_level_from_env()` instead of hardcoded `logging.INFO`

### Step 2: Add Timing Decorator to `app/core/logger.py`
- Add import for `time`, `functools`, and `contextlib`
- Add `from typing import Callable, ParamSpec, TypeVar, Generator` for proper typing
- Create `@timed` decorator that:
  - Accepts optional `logger` and `level` parameters (defaults to module logger and DEBUG)
  - Measures function execution time using `time.perf_counter()`
  - Logs entry with function name and arguments at specified level
  - Logs exit with function name and elapsed time (formatted to 3 decimal places)
  - Preserves function signature using `functools.wraps`
  - Example output: `"[TIMING] extract_blocks completed in 1.234s"`

### Step 3: Add Timing Context Manager to `app/core/logger.py`
- Create `timed_block` context manager using `@contextlib.contextmanager` that:
  - Accepts `name: str`, optional `logger`, and optional `level` parameter
  - Logs entry with block name at specified level
  - Yields control to the block
  - Logs exit with block name and elapsed time on successful completion
  - Example usage: `with timed_block("color analysis"): ...`
  - Example output: `"[TIMING] color analysis completed in 0.456s"`

### Step 4: Add JSON Formatter to `app/core/logger.py`
- Add import for `json` module
- Add constant `LOG_FORMAT_ENV_VAR = "DXF_EXTRACTOR_LOG_FORMAT"` for format environment variable
- Create `JsonFormatter(logging.Formatter)` class that:
  - Overrides `format(record)` method
  - Outputs JSON with keys: `timestamp`, `name`, `level`, `message`
  - Optionally includes `exc_info` if exception present
  - Uses ISO 8601 format for timestamp
- Add helper function `_get_log_format_from_env() -> str` that:
  - Reads `DXF_EXTRACTOR_LOG_FORMAT` environment variable
  - Returns `"json"` or `"text"` (default `"text"`)
- Update `setup_logger()` to:
  - Check format preference via `_get_log_format_from_env()`
  - Use `JsonFormatter` when format is `"json"`
  - Use existing text formatter when format is `"text"`

### Step 5: Add DEBUG Statements to `app/core/extractor.py`
- Add DEBUG logging at these key points:
  - Before and after loading DXF file with `ezdxf.readfile()`
  - When iterating block definitions (log block name being analyzed)
  - When processing each INSERT entity (log block name and layer)
  - When extracting rotation/scale data (log the values extracted)
  - When processing TEXT/MTEXT annotations (log annotation content preview, truncated to 50 chars)
  - When resolving entity colors (log RGB result)
  - At start and end of `extract_color_analysis()` with entity counts
- Use `logger.debug()` for all new statements to avoid noise at INFO level

### Step 6: Add DEBUG Statements to `app/core/excel_writer.py`
- Add DEBUG logging at these key points:
  - When creating each sheet (log sheet name and row count)
  - When processing block-layer pairs (log pair being processed)
  - When formatting scale data (log variance detection results)
  - When applying Excel formatting (log formatting stage)
- Use `logger.debug()` for all new statements

### Step 7: Add DEBUG Statements to `app/core/geometry.py`
- Add import for `setup_logger` from `.logger`
- Initialize module logger: `logger = setup_logger(__name__)`
- Add DEBUG logging at these key points:
  - In `_get_block_bounding_box()`: log entity type being processed, final bbox result
  - In `_get_intersection_points()`: log coordinate counts before/after deduplication
  - In `_calculate_segments()`: log input points and output segments
  - In `_categorize_rotation()`: log input angle and normalized result
- Use `logger.debug()` for all new statements

### Step 8: Create Tests for Logger Enhancements in `app/tests/core/test_logger.py`
- Create new test file with the following test cases:
  - `test_setup_logger_default_level()` - Verify default INFO level
  - `test_setup_logger_env_debug_level()` - Verify DEBUG level from env var
  - `test_setup_logger_env_invalid_level()` - Verify fallback to INFO for invalid env var
  - `test_setup_logger_json_format()` - Verify JSON output format when env var set
  - `test_setup_logger_text_format_default()` - Verify text format is default
  - `test_timed_decorator_logs_duration()` - Verify timing decorator logs function duration
  - `test_timed_block_logs_duration()` - Verify context manager logs block duration
  - `test_json_formatter_output_structure()` - Verify JSON has expected keys
- Use `monkeypatch` fixture to set/unset environment variables
- Use `caplog` or `capfd` fixtures to capture log output

### Step 9: Run Validation Commands
- Execute all validation commands listed below to ensure zero regressions

## Validation Commands
Execute every command to validate the chore is complete with zero regressions.

- `uv run pytest app/tests/core/test_logger.py -v` - Run new logger tests to validate logging enhancements work correctly
- `uv run pytest app/tests/core/test_extractor.py -v` - Run extractor tests to ensure DEBUG statements don't break extraction
- `uv run pytest app/tests/core/test_excel_writer.py -v` - Run excel writer tests to ensure DEBUG statements don't break Excel generation
- `uv run pytest app/tests/core/test_geometry.py -v` - Run geometry tests to ensure DEBUG statements don't break calculations
- `uv run pytest app/tests/ -v` - Run full test suite to validate no regressions anywhere
- `uv run mypy app/` - Run type checker to ensure new code is properly typed
- `uv run ruff check app/` - Run linter to ensure code style compliance

## Notes
- Environment variables for configuration:
  - `DXF_EXTRACTOR_LOG_LEVEL` - Set to `DEBUG`, `INFO`, `WARNING`, `ERROR`, or `CRITICAL`
  - `DXF_EXTRACTOR_LOG_FORMAT` - Set to `json` for JSON output, defaults to `text`
- The timing utilities should use `time.perf_counter()` for accurate measurement
- DEBUG statements should be informative but not verbose enough to significantly slow down processing
- JSON format is useful for log aggregation systems and automated analysis
- All existing functionality must remain backward compatible - INFO level and text format remain defaults
