# Chore: Add mypy Type Checking

## Chore Description
Integrate mypy static type checking into the DWG Block Extractor project to improve code quality, catch type-related bugs during development, and provide better IDE support. This includes:
- Installing mypy as a dev dependency
- Creating a mypy configuration file with appropriate settings
- Adding comprehensive type hints to all Python modules
- Configuring mypy to work with third-party libraries (ezdxf, pandas, openpyxl, customtkinter)
- Setting up validation commands to ensure type safety

The codebase already uses modern Python 3.11+ type hints (e.g., `dict[str, int]`, function annotations), but lacks static type checking enforcement and needs additional type hints for complete coverage.

## Relevant Files
Use these files to resolve the chore:

- **app/core/extractor.py** - Already has good type hints (`extract_blocks(file_path: str) -> dict[str, int]`), needs return types for internal logic and exception handling verification
- **app/core/excel_writer.py** - Already has good type hints (`write_excel(block_data: dict[str, int], output_path: str) -> str`), may need additional hints for pandas/openpyxl interactions
- **app/core/logger.py** - Has function signature type hints (`setup_logger(name: str) -> logging.Logger`), complete
- **app/core/constants.py** - Likely contains module-level constants that need type annotations
- **app/main.py** - GUI application with class methods that need comprehensive type hints for customtkinter widgets, callbacks, and threading
- **app/tests/core/test_extractor.py** - Test file that needs type hints for test functions and fixtures
- **app/tests/core/test_excel_writer.py** - Test file that needs type hints for test functions and fixtures
- **pyproject.toml** - Project configuration where mypy dependency and configuration will be added

### New Files
- **mypy.ini** or **pyproject.toml `[tool.mypy]` section** - mypy configuration file with settings for strict type checking, third-party library stubs, and path configurations

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### Step 1: Install mypy and type stubs
- Add `mypy` to the `[project.optional-dependencies]` dev section in `pyproject.toml`
- Add type stub packages for third-party libraries:
  - `pandas-stubs` - Type stubs for pandas
  - `types-openpyxl` - Type stubs for openpyxl
- Install dependencies with `uv sync --all-extras` to ensure mypy and stubs are available

### Step 2: Create mypy configuration
- Add `[tool.mypy]` section to `pyproject.toml` with the following settings:
  - `python_version = "3.11"` - Match project's minimum Python version
  - `warn_return_any = true` - Warn about returning Any from typed functions
  - `warn_unused_configs = true` - Warn about unused config options
  - `disallow_untyped_defs = true` - Require all functions to have type annotations
  - `check_untyped_defs = true` - Type check the interior of functions without annotations
  - `exclude = ['.venv', 'build', 'dist']` - Exclude virtual environment and build directories
  - Configure third-party library handling for libraries without stubs (ezdxf, customtkinter)

### Step 3: Add type hints to app/core/constants.py
- Read the file to identify all module-level constants
- Add explicit type annotations to all constants (e.g., `SUPPORTED_EXTENSIONS: set[str] = {'.dwg', '.dxf'}`)
- Ensure all string constants have type annotations

### Step 4: Add type hints to app/main.py
- Add type hints to all class methods in `DWGExtractorApp`
- Add type hints for instance variables in `__init__` method (e.g., `self.selected_file_path: str | None = None`)
- Add return type hints to all methods (most will be `-> None` for GUI callbacks)
- Add type hints for threading and tkinter widget parameters
- Add type hint to `main()` function (`-> None`)

### Step 5: Add type hints to test files
- Add type hints to `app/tests/core/test_extractor.py` test functions (return type `-> None`)
- Add type hints to `app/tests/core/test_excel_writer.py` test functions (return type `-> None`)
- Add type hints to any test fixtures or helper functions
- Review `conftest.py` for any shared fixtures that need type hints

### Step 6: Run mypy and fix any type errors
- Run `uv run mypy app/` to check all application code
- Address any type errors found by mypy:
  - Missing return type annotations
  - Incompatible types in assignments
  - Missing type annotations on function parameters
  - Issues with third-party library types
- If ezdxf or customtkinter cause issues due to missing stubs, configure mypy to ignore those imports

### Step 7: Update README.md with mypy usage
- Add mypy to the "Testing" section of README.md
- Document the command to run type checking: `uv run mypy app/`
- Note that mypy is part of the dev dependencies

## Validation Commands
Execute every command to validate the chore is complete with zero regressions.

- `uv run mypy app/` - Run mypy type checker on all application code, must pass with no errors
- `uv run pytest app/tests/` - Run all tests to ensure type hints don't break existing functionality
- `uv run pytest --cov=app/core app/tests/` - Run tests with coverage to ensure no regression in test coverage
- `uv run python app/main.py` - Launch GUI application to verify it still runs correctly (will open GUI window, manually close it)

## Notes
- The codebase already uses modern Python 3.11+ type hint syntax (`dict[str, int]` instead of `Dict[str, int]`), so continue using this style
- Some third-party libraries (ezdxf, customtkinter) may not have type stubs available - configure mypy to handle these gracefully with `ignore_missing_imports = true` for specific modules if needed
- Focus on adding value with type hints - don't add `-> None` everywhere if it's obvious, but do add it for public API functions
- The project uses `uv` for dependency management, not pip - all commands should use `uv run` prefix
- Type checking should be part of the development workflow but doesn't need to be enforced in CI/CD yet (this can be a future enhancement)
