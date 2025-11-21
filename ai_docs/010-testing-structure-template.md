# Testing Structure and Organisation Template

A comprehensive guide for establishing consistent, maintainable test suites in Python projects. This template captures best practices for test organisation, fixture management, and assertion patterns.

## Table of Contents

1. [Testing Philosophy](#testing-philosophy)
2. [Directory Structure](#directory-structure)
3. [Configuration (pyproject.toml)](#configuration-pyprojecttoml)
4. [Test File Patterns](#test-file-patterns)
5. [Fixture Patterns](#fixture-patterns)
6. [Assertion Patterns](#assertion-patterns)
7. [Test Asset Management](#test-asset-management)
8. [Integration Test Patterns](#integration-test-patterns)
9. [Commands Reference](#commands-reference)
10. [Anti-Patterns to Avoid](#anti-patterns-to-avoid)

---

## Testing Philosophy

### Core Principles

- **Tests validate behaviour, not implementation**: Focus on what the code does, not how it does it
- **One assertion concept per test**: Each test should verify a single logical concept (multiple `assert` statements are fine if they validate the same concept)
- **Tests should be independent**: Each test must be able to run in isolation without depending on other tests
- **Use descriptive naming**: Test names should describe the scenario and expected outcome
- **Maintain test code quality**: Apply the same standards (type hints, docstrings) to test code as production code

### Test Categories

| Category | Purpose | Location | Characteristics |
|----------|---------|----------|-----------------|
| Unit Tests | Test individual functions/classes in isolation | `app/tests/core/` | Fast, no I/O, mocked dependencies |
| Integration Tests | Test module interactions | `app/tests/core/` | May use real files, temp directories |
| Fixture Generation | Create reproducible test data | `app/tests/assets/` | Standalone scripts, version-controlled output |

---

## Directory Structure

### Recommended Layout

```
project/
├── app/                          # Application code
│   ├── core/                     # Business logic modules
│   │   ├── __init__.py
│   │   ├── module_a.py
│   │   └── module_b.py
│   ├── tests/                    # Test suite (mirrors app/core structure)
│   │   ├── __init__.py           # Required for package discovery
│   │   ├── core/                 # Unit tests for app/core/
│   │   │   ├── __init__.py       # Required for package discovery
│   │   │   ├── test_module_a.py  # Tests for module_a.py
│   │   │   └── test_module_b.py  # Tests for module_b.py
│   │   └── assets/               # Test fixtures and generators
│   │       ├── sample_data.json
│   │       └── create_sample_data.py
│   └── main.py                   # Application entry point
│
├── pyproject.toml                # Project and tool configuration
└── .venv/                        # Virtual environment
```

### Key Conventions

- **Mirror structure**: `app/tests/core/` mirrors `app/core/`
- **File naming**: `test_<module_name>.py` maps to `<module_name>.py`
- **Package markers**: Include `__init__.py` in all test directories
- **Assets folder**: Store test fixtures and generator scripts together

---

## Configuration (pyproject.toml)

### Pytest Configuration

```toml
[tool.pytest.ini_options]
# Configure pytest to discover tests from app/tests/
testpaths = ["app/tests"]

# Add app/ to Python path for importing production code
pythonpath = ["app"]

# Optional: Default options (uncomment as needed)
# addopts = "-v --strict-markers"
# markers = ["slow: marks tests as slow"]
```

### Coverage Configuration

```toml
[tool.coverage.run]
# Measure coverage for application code only
source = ["app"]

# Exclude non-relevant directories
omit = [".venv/*", "build/*", "dist/*"]

[tool.coverage.report]
# Optional: Fail if coverage drops below threshold
# fail_under = 80
exclude_lines = [
    "pragma: no cover",
    "if TYPE_CHECKING:",
    "raise NotImplementedError",
]
```

### Mypy Configuration (for type-checked tests)

```toml
[tool.mypy]
python_version = "3.11"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true      # Enforce type hints everywhere
check_untyped_defs = true
exclude = ['.venv', 'build', 'dist']

# Ignore missing stubs for external libraries
[[tool.mypy.overrides]]
module = ["external_library", "external_library.*"]
ignore_missing_imports = true
```

### Ruff Configuration (linting)

```toml
[tool.ruff]
line-length = 88
target-version = "py311"
exclude = [".venv", "build", "dist"]

[tool.ruff.lint]
select = ["E", "F", "I"]  # Pyflakes, pycodestyle, isort
ignore = ["E501"]          # Line length (handled by formatter)

[tool.ruff.lint.isort]
known-first-party = ["app", "core"]
```

---

## Test File Patterns

### Module Docstring

Every test file should begin with a docstring describing its scope:

```python
"""
Unit tests for the <module_name> module.

This test suite validates <high-level description> including:
- Feature A validation
- Feature B error handling
- Edge case coverage
- Return type validation
"""
```

### Class-Based Organisation

Group related tests in classes. Each class focuses on a specific function or component:

```python
from pathlib import Path
from typing import Iterator

import pytest

from core.module_a import function_a, ClassA


class TestFunctionA:
    """Test suite for the function_a function."""

    def test_function_a_basic_case(self) -> None:
        """Test function_a with typical input."""
        result = function_a("input")

        assert result == "expected_output"

    def test_function_a_empty_input(self) -> None:
        """Test function_a handles empty input correctly."""
        result = function_a("")

        assert result == ""

    def test_function_a_raises_on_invalid(self) -> None:
        """Test that invalid input raises ValueError."""
        with pytest.raises(ValueError, match="Invalid input"):
            function_a(None)


class TestClassA:
    """Test suite for ClassA."""

    def test_class_a_initialization(self) -> None:
        """Test ClassA initializes with correct defaults."""
        instance = ClassA()

        assert instance.property_a == "default"
        assert instance.property_b == 0
```

### Method Naming Convention

Use the pattern: `test_<functionality>_<scenario>()`

Examples:
- `test_extract_valid_file()` - Tests extraction with valid input
- `test_extract_empty_file()` - Tests extraction with empty file
- `test_extract_invalid_file_raises()` - Tests error handling
- `test_categorize_rotation_standard_angles()` - Tests specific angle handling
- `test_categorize_rotation_boundary_cases()` - Tests edge cases

### Type Hints on Test Methods

Always include return type annotations:

```python
def test_example(self) -> None:
    """Test description."""
    pass
```

---

## Fixture Patterns

### Temporary Directory Fixture

Use for tests that need file system access:

```python
import tempfile
from typing import Iterator

import pytest


class TestFileOperations:
    """Tests requiring file system access."""

    @pytest.fixture
    def temp_dir(self) -> Iterator[str]:
        """Create a temporary directory for test outputs."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir

    def test_write_file(self, temp_dir: str) -> None:
        """Test file writing to temp directory."""
        output_path = Path(temp_dir) / "output.txt"

        write_file(output_path, "content")

        assert output_path.exists()
        assert output_path.read_text() == "content"
```

### Sample Data Fixture

Return typed dictionaries for structured test data:

```python
from typing import TypedDict


class ExtractionResult(TypedDict):
    """Type definition for extraction results."""
    counts: dict[str, int]
    entities: dict[str, int]


class TestExtraction:
    """Tests for extraction functionality."""

    @pytest.fixture
    def sample_extraction_data(self) -> ExtractionResult:
        """Provide sample extraction data for testing."""
        return {
            "counts": {"VALVE": 10, "PIPE": 5, "TAG": 3},
            "entities": {"VALVE": 8, "PIPE": 12, "TAG": 4},
        }

    def test_process_extraction(
        self, sample_extraction_data: ExtractionResult
    ) -> None:
        """Test processing with sample data."""
        result = process(sample_extraction_data)

        assert result["total"] == 18
```

### Fixture Scope

Use appropriate scope for expensive fixtures:

```python
@pytest.fixture(scope="module")  # Created once per test module
def expensive_resource() -> Iterator[Resource]:
    """Create expensive resource once per module."""
    resource = create_expensive_resource()
    yield resource
    resource.cleanup()


@pytest.fixture  # Default: function scope, created per test
def simple_fixture() -> dict:
    """Create fresh data for each test."""
    return {"key": "value"}
```

---

## Assertion Patterns

### Basic Assertions

```python
def test_basic_assertions(self) -> None:
    """Demonstrate basic assertion patterns."""
    result = function_under_test()

    # Direct equality
    assert result == expected_value

    # Type checking
    assert isinstance(result, dict)

    # Collection membership
    assert "key" in result
    assert len(result) == 3

    # Boolean conditions
    assert result["enabled"] is True
    assert not result["disabled"]

    # Numeric comparisons
    assert result["count"] > 0
    assert result["count"] >= 1
```

### Exception Testing

```python
def test_raises_value_error(self) -> None:
    """Test that invalid input raises ValueError with message."""
    with pytest.raises(ValueError, match="Invalid or corrupted"):
        function_under_test("invalid_input")


def test_raises_file_not_found(self) -> None:
    """Test that missing file raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError, match="File not found"):
        function_under_test("nonexistent.txt")
```

### Approximate Comparisons

For floating-point comparisons:

```python
def test_floating_point_calculation(self) -> None:
    """Test calculation with floating point tolerance."""
    result = calculate_ratio(10, 3)

    # Default tolerance: 1e-6
    assert result == pytest.approx(3.33, abs=0.01)

    # Alternative: relative tolerance
    assert result == pytest.approx(3.333, rel=0.01)
```

### Parametrized Tests

Test multiple scenarios with the same logic:

```python
@pytest.mark.parametrize(
    "input_angle,expected_category",
    [
        (0.0, "0"),
        (0.5, "0"),       # Within tolerance
        (45.0, "other"),
        (89.5, "90"),     # Within tolerance
        (90.0, "90"),
        (90.5, "90"),     # Within tolerance
        (135.0, "other"),
        (180.0, "180"),
        (270.0, "270"),
        (359.5, "0"),     # Wraps around
        (-90.0, "270"),   # Negative normalisation
        (450.0, "90"),    # > 360 normalisation
    ],
)
def test_categorize_rotation_parametrized(
    self, input_angle: float, expected_category: str
) -> None:
    """Test rotation categorization with parametrized angles."""
    result = categorize_rotation(input_angle)

    assert result == expected_category
```

### Skip Markers

Skip tests that cannot run in certain environments:

```python
@pytest.mark.skip(
    reason="Feature requires external service not available in CI"
)
def test_external_integration(self) -> None:
    """Test integration with external service."""
    pass


@pytest.mark.skipif(
    sys.platform != "linux",
    reason="Linux-specific functionality"
)
def test_linux_specific_feature(self) -> None:
    """Test Linux-specific feature."""
    pass
```

---

## Test Asset Management

### Asset Organisation

```
app/tests/assets/
├── sample_data.json              # Static fixture file
├── create_sample_data.py         # Generator script
├── complex_fixture.dxf           # Generated test file
├── create_complex_fixture.py     # Generator for complex_fixture.dxf
└── samples/                      # Real-world sample files (may be gitignored)
    └── production_sample.dwg
```

### Fixture Generator Scripts

Create self-documenting scripts that generate test fixtures:

```python
"""
Script to create test fixture with specific test scenarios.

This creates test fixtures for validating <feature name>.
The file includes:
- Scenario A: Basic case with expected values
- Scenario B: Edge case with boundary values
- Scenario C: Error case with invalid data
"""

import json
from pathlib import Path


def create_test_fixture() -> None:
    """Generate test fixture file with documented scenarios."""
    fixture_data = {
        # Scenario A: Basic case
        "basic_case": {
            "input": "normal_value",
            "expected_output": 42,
        },
        # Scenario B: Edge case - boundary values
        "boundary_case": {
            "input": 0,
            "expected_output": 0,
        },
        # Scenario C: Multiple items
        "multi_item_case": {
            "items": ["a", "b", "c"],
            "expected_count": 3,
        },
    }

    output_path = Path(__file__).parent / "test_fixture.json"
    output_path.write_text(json.dumps(fixture_data, indent=2))

    print(f"Created {output_path}")
    print("\nExpected test scenarios:")
    print("- basic_case: Standard input -> 42")
    print("- boundary_case: Zero input -> 0")
    print("- multi_item_case: 3 items -> count=3")


if __name__ == "__main__":
    create_test_fixture()
```

### Regenerating Fixtures

Run generator scripts from the project root:

```bash
# Regenerate a specific fixture
uv run python app/tests/assets/create_sample_data.py

# Verify fixture exists
test -f app/tests/assets/sample_data.json && echo "Fixture created"
```

---

## Integration Test Patterns

### File I/O with Temp Directories

```python
import os
import tempfile
from pathlib import Path
from typing import Iterator

import pytest


class TestFileIntegration:
    """Integration tests for file operations."""

    @pytest.fixture
    def temp_dir(self) -> Iterator[str]:
        """Create temporary directory, cleaned up after test."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir

    def test_full_pipeline(self, temp_dir: str) -> None:
        """Test complete file processing pipeline."""
        # Arrange
        input_path = "app/tests/assets/sample_input.txt"
        output_path = os.path.join(temp_dir, "output.txt")

        # Act
        result = process_file(input_path, output_path)

        # Assert
        assert Path(output_path).exists()
        assert result["status"] == "success"

        # Verify output content
        content = Path(output_path).read_text()
        assert "expected_content" in content
```

### Cleanup Patterns

Use context managers and try/finally for cleanup:

```python
def test_temporary_file_creation(self) -> None:
    """Test with manual cleanup for generated files."""
    temp_file = Path("app/tests/assets/temp_test.txt")

    try:
        # Create temporary file
        temp_file.write_text("test content")

        # Perform test
        result = process_file(temp_file)
        assert result == "expected"

    finally:
        # Always clean up
        if temp_file.exists():
            temp_file.unlink()
```

### Mocking External Dependencies

```python
from unittest.mock import patch, MagicMock


class TestExternalIntegration:
    """Tests with mocked external dependencies."""

    def test_with_mocked_api(self) -> None:
        """Test processing with mocked API call."""
        with patch("core.module.external_api") as mock_api:
            mock_api.fetch.return_value = {"data": "mocked_value"}

            result = process_with_api("input")

            assert result == "processed_mocked_value"
            mock_api.fetch.assert_called_once_with("input")

    def test_exception_handling_with_mock(self) -> None:
        """Test error handling when external call fails."""
        with patch("core.module.external_api") as mock_api:
            mock_api.fetch.side_effect = RuntimeError("Connection failed")

            with pytest.raises(RuntimeError, match="Connection failed"):
                process_with_api("input")
```

---

## Commands Reference

### Running Tests

```bash
# Run all tests
uv run pytest app/tests/

# Run tests with verbose output
uv run pytest app/tests/ -v

# Run specific test file
uv run pytest app/tests/core/test_module_a.py

# Run specific test class
uv run pytest app/tests/core/test_module_a.py::TestFunctionA

# Run specific test method
uv run pytest app/tests/core/test_module_a.py::TestFunctionA::test_basic_case

# Run tests matching pattern
uv run pytest app/tests/ -k "test_basic"
```

### Coverage

```bash
# Run tests with coverage report
uv run pytest --cov=app/core app/tests/

# Generate HTML coverage report
uv run pytest --cov=app/core --cov-report=html app/tests/

# Check coverage threshold
uv run pytest --cov=app/core --cov-fail-under=80 app/tests/
```

### Type Checking

```bash
# Type check application and test code
uv run mypy app/

# Type check specific file
uv run mypy app/tests/core/test_module_a.py
```

### Linting

```bash
# Check code style
uv run ruff check app/

# Fix auto-fixable issues
uv run ruff check app/ --fix

# Format code
uv run ruff format app/
```

---

## Anti-Patterns to Avoid

### 1. Test Interdependence

**Bad**: Tests depend on execution order or shared state

```python
# BAD - shared state between tests
class TestBad:
    data = []  # Shared mutable state

    def test_first(self) -> None:
        self.data.append("value")

    def test_second(self) -> None:
        # Fails if test_first doesn't run first
        assert "value" in self.data
```

**Good**: Each test is independent

```python
# GOOD - independent tests
class TestGood:
    def test_first(self) -> None:
        data = []
        data.append("value")
        assert "value" in data

    def test_second(self) -> None:
        data = ["value"]
        assert "value" in data
```

### 2. Vague Test Names

**Bad**: Names don't describe the scenario

```python
def test_function(self) -> None: ...
def test_function2(self) -> None: ...
def test_it_works(self) -> None: ...
```

**Good**: Names describe scenario and expectation

```python
def test_extract_valid_file_returns_expected_counts(self) -> None: ...
def test_extract_empty_file_returns_empty_dict(self) -> None: ...
def test_extract_invalid_file_raises_value_error(self) -> None: ...
```

### 3. Missing Docstrings

**Bad**: No explanation of test purpose

```python
def test_complex_scenario(self) -> None:
    result = complex_function(a=1, b=2, c=3)
    assert result == 42
```

**Good**: Docstring explains the "why"

```python
def test_complex_scenario_with_default_weights(self) -> None:
    """Test calculation uses default weights when not specified."""
    result = complex_function(a=1, b=2, c=3)
    assert result == 42  # 1*1 + 2*2 + 3*3 = 14 with default multiplier 3
```

### 4. Testing Implementation Details

**Bad**: Testing internal implementation

```python
def test_uses_correct_algorithm(self) -> None:
    # Testing HOW it works
    with patch("module._internal_helper") as mock:
        function_under_test()
        assert mock.call_count == 3
```

**Good**: Testing observable behaviour

```python
def test_returns_correct_result(self) -> None:
    # Testing WHAT it does
    result = function_under_test(input_data)
    assert result == expected_output
```

### 5. Incomplete Assertions

**Bad**: Not verifying all aspects

```python
def test_extraction_result(self) -> None:
    result = extract_data(file_path)
    assert isinstance(result, dict)  # Only checks type, not content
```

**Good**: Comprehensive verification

```python
def test_extraction_result_structure_and_content(self) -> None:
    result = extract_data(file_path)

    # Verify structure
    assert isinstance(result, dict)
    assert "counts" in result
    assert "entities" in result

    # Verify content
    assert result["counts"]["VALVE"] == 10
    assert len(result["entities"]) == 3
```

### 6. Not Cleaning Up Resources

**Bad**: Leaving test artifacts

```python
def test_file_creation(self) -> None:
    path = Path("test_output.txt")
    path.write_text("test")
    result = process_file(path)
    assert result == "success"
    # File left behind!
```

**Good**: Always clean up

```python
def test_file_creation(self) -> None:
    path = Path("test_output.txt")
    try:
        path.write_text("test")
        result = process_file(path)
        assert result == "success"
    finally:
        if path.exists():
            path.unlink()
```

---

## Further Reading

- [pytest Documentation](https://docs.pytest.org/)
- [pytest-cov Documentation](https://pytest-cov.readthedocs.io/)
- [mypy Documentation](https://mypy.readthedocs.io/)
- [ruff Documentation](https://docs.astral.sh/ruff/)
