# Chore: Create Python Project Testing & Structure Template

## Chore Description
Create a comprehensive, generic template guide that establishes best practices for Python project structure, testing setup, mypy configuration, and typing conventions. This template should be reusable across any Python project (not domain-specific) and provide clear, actionable guidance for setting up a well-organized, type-safe, and thoroughly tested Python codebase.

## Relevant Files
Use these files as reference patterns for the template:

- `pyproject.toml` - Reference for dependency management, tool configuration (pytest, mypy, ruff, coverage)
- `app/core/extractor.py` - Reference for typing patterns including TypedDict, complex type hints, docstrings
- `app/core/geometry.py` - Reference for modular function design with proper type annotations
- `app/core/constants.py` - Reference for constants organization pattern
- `app/core/logger.py` - Reference for utility module design
- `app/tests/core/test_extractor.py` - Reference for comprehensive test patterns including parametrized tests, fixtures, error handling tests
- `app/tests/core/test_geometry.py` - Reference for focused unit test organization with test classes
- `README.md` - Reference for project documentation structure

### New Files
- `ai_docs/011-python-testing-template.md` - The comprehensive template guide (main deliverable)

## Step by Step Tasks

### 1. Create Template Header and Overview Section
- Add title and purpose statement
- Explain the template's goals: consistency, type safety, testability, maintainability
- List prerequisites (Python 3.11+, uv package manager)

### 2. Document Project Structure Template
- Define standard directory layout:
  ```
  project-root/
  ├── app/                    # Application code
  │   ├── core/               # Business logic modules
  │   │   ├── __init__.py
  │   │   ├── constants.py    # Application constants
  │   │   ├── logger.py       # Centralized logging
  │   │   └── {module}.py     # Feature modules
  │   ├── tests/              # Test suite
  │   │   ├── __init__.py
  │   │   ├── core/           # Tests for core modules
  │   │   │   ├── __init__.py
  │   │   │   └── test_{module}.py
  │   │   └── assets/         # Test fixtures/data
  │   └── main.py             # Application entry point
  ├── scripts/                # Utility scripts
  ├── pyproject.toml          # Project configuration
  └── README.md               # Documentation
  ```
- Explain rationale for nested `tests/` inside `app/` (co-location, easier imports)
- Document `__init__.py` requirements for Python packages

### 3. Document pyproject.toml Configuration Template
- Project metadata section
- Dependencies section with version constraints
- Optional dev dependencies section
- Dependency groups (dev, build)
- pytest configuration:
  - `testpaths`
  - `pythonpath` for module resolution
- coverage configuration:
  - `source`
  - `omit` patterns
- mypy configuration:
  - `python_version`
  - `warn_return_any`
  - `warn_unused_configs`
  - `disallow_untyped_defs`
  - `check_untyped_defs`
  - `exclude` patterns
  - Module overrides for third-party libraries without stubs
- ruff configuration:
  - `line-length`
  - `target-version`
  - `exclude` patterns
  - lint rules selection (`select`, `ignore`)
  - isort configuration
  - format configuration

### 4. Document Type Annotation Patterns
- Basic type annotations for function parameters and return types
- Using `typing` module types:
  - `TypedDict` for structured dictionaries
  - `Any` (when to use, when to avoid)
  - Generic types: `list`, `dict`, `tuple`, `set`
  - Union types and `|` syntax
  - `None` type and optional returns
- Complex nested type annotations:
  - `dict[str, int]`
  - `dict[tuple[str, str], int]`
  - `dict[str, set[tuple[float, float]]]`
  - `list[dict[str, Any]]`
- Return type patterns:
  - `-> None` for void functions
  - `-> Type | None` for functions that may return None
  - Using TypedDict for complex return structures
- Variable annotations for complex types

### 5. Document TypedDict Best Practices
- When to use TypedDict vs regular dict
- Defining TypedDict classes with docstrings
- Attribute documentation pattern
- Example with complex nested types
- Type safety benefits

### 6. Document Docstring Conventions
- Module-level docstrings with usage examples
- Function docstrings following Google style:
  - Summary line
  - Extended description (when needed)
  - Args section with type descriptions
  - Returns section with type and description
  - Raises section for exceptions
  - Examples section with doctests
- Class docstrings with attribute documentation

### 7. Document Testing Patterns
- Test file naming: `test_{module}.py`
- Test class organization:
  - Group related tests in classes
  - `TestClassName` naming convention
- Test method patterns:
  - `test_{method}_{scenario}` naming
  - Type annotations on test methods: `def test_foo(self) -> None:`
  - Arrange-Act-Assert pattern
- Testing categories:
  - Happy path tests
  - Edge case tests (empty inputs, boundary values)
  - Error handling tests (expected exceptions)
  - Type validation tests
  - Conservation/invariant tests
- pytest fixtures for test data
- pytest.raises for exception testing
- pytest.mark.parametrize for data-driven tests
- pytest.mark.skip for conditional skipping
- pytest.approx for floating-point comparisons
- Mocking with unittest.mock

### 8. Document Test Organization Best Practices
- One test class per module or feature
- Test file structure:
  ```python
  """
  Module docstring explaining test coverage.
  """

  import pytest
  from module import function_to_test


  class TestFeatureA:
      """Test suite for feature A."""

      def test_happy_path(self) -> None:
          """Test description."""
          ...

      def test_edge_case(self) -> None:
          """Test description."""
          ...


  class TestFeatureB:
      """Test suite for feature B."""
      ...
  ```
- Test assets/fixtures organization in `tests/assets/`

### 9. Document Constants Module Pattern
- Organizing constants by category
- Type annotations for constants
- Naming conventions (SCREAMING_SNAKE_CASE)
- Module docstring with usage examples
- Constants categories:
  - File/path constants
  - Configuration constants
  - UI/message constants
  - Magic numbers/values

### 10. Document Logger Module Pattern
- Centralized logging configuration
- stdout-only logging for development visibility
- Logger factory function pattern
- Format configuration
- When to add file handlers (production)

### 11. Document Code Quality Commands
- Testing: `uv run pytest app/tests/`
- Coverage: `uv run pytest --cov=app app/tests/`
- Type checking: `uv run mypy app/`
- Linting: `uv run ruff check app/`
- Formatting: `uv run ruff format app/`
- Auto-fix: `uv run ruff check app/ --fix`

### 12. Document README Template
- Project title and description
- Purpose/Features summary
- Tech Stack list
- Project Structure tree
- Usage section with commands
- Reference files section
- Working directory conventions
- Development environment notes

### 13. Add Complete pyproject.toml Template
- Include full working example with all sections
- Add comments explaining each section

### 14. Validate Template Completeness
Run validation to ensure the template covers all patterns from the reference codebase:
- All type annotation patterns are documented
- All test patterns are documented
- All configuration options are covered
- Template is generic (no domain-specific references)

## Validation Commands
Execute every command to validate the chore is complete with zero regressions.

- `test -f ai_docs/011-python-testing-template.md && echo "Template file exists"` - Verify template file was created
- `grep -q "pyproject.toml" ai_docs/011-python-testing-template.md && echo "Contains pyproject.toml section"` - Verify pyproject.toml documentation exists
- `grep -q "TypedDict" ai_docs/011-python-testing-template.md && echo "Contains TypedDict section"` - Verify TypedDict patterns documented
- `grep -q "pytest" ai_docs/011-python-testing-template.md && echo "Contains pytest section"` - Verify testing patterns documented
- `grep -q "mypy" ai_docs/011-python-testing-template.md && echo "Contains mypy section"` - Verify mypy configuration documented
- `uv run pytest app/tests/ -v` - Run existing tests to ensure no regressions from any incidental changes
- `uv run mypy app/` - Verify type checking still passes

## Notes
- The template should be **generic** - avoid domain-specific examples (use generic names like `process_data()`, `User`, `Order` instead of CAD/DXF terminology)
- Focus on patterns that work for **any Python project**, not just this specific codebase
- Include both minimal examples and more complex patterns for each concept
- The template should serve as a **quick-start reference** that developers can copy and adapt
- Consider adding a "Quick Start Checklist" at the beginning for easy setup
- Reference official documentation links where appropriate (mypy, pytest, ruff docs)
