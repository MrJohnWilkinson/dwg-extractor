# Python Project Testing & Structure Template

A comprehensive, generic template guide for establishing best practices in Python project structure, testing setup, mypy configuration, and typing conventions.

## Quick Start Checklist

- [ ] Python 3.11+ installed
- [ ] uv package manager installed (`pip install uv` or `curl -LsSf https://astral.sh/uv/install.sh | sh`)
- [ ] Create project directory and initialize with `uv init`
- [ ] Copy `pyproject.toml` template (see below)
- [ ] Create directory structure (see Project Structure)
- [ ] Add `__init__.py` files to all package directories
- [ ] Run `uv sync` to install dependencies

## Goals

- **Consistency**: Standardized project structure across all Python projects
- **Type Safety**: Strict mypy configuration with comprehensive type annotations
- **Testability**: Well-organized test suite with clear patterns
- **Maintainability**: Clear separation of concerns and modular design

## Prerequisites

- **Python**: 3.11+ (for modern type annotation syntax)
- **Package Manager**: uv (all dependency management)
- **IDE Support**: Configure your IDE for mypy and ruff integration

---

## 1. Project Structure Template

```
project-root/
├── app/                          # Application code
│   ├── core/                     # Business logic modules
│   │   ├── __init__.py
│   │   ├── constants.py          # Application constants
│   │   ├── logger.py             # Centralized logging
│   │   └── {module}.py           # Feature modules
│   ├── tests/                    # Test suite
│   │   ├── __init__.py
│   │   ├── core/                 # Tests for core modules
│   │   │   ├── __init__.py
│   │   │   └── test_{module}.py  # Unit tests
│   │   └── assets/               # Test fixtures/data
│   └── main.py                   # Application entry point
│
├── scripts/                      # Utility scripts
│   ├── start.sh                  # Launch application
│   └── build.sh                  # Build executable
│
├── .venv/                        # Virtual environment (managed by uv)
├── pyproject.toml                # Project configuration
└── README.md                     # Documentation
```

### Rationale for Nested Tests

Placing `tests/` inside `app/` provides:

- **Co-location**: Tests live near the code they test
- **Easier Imports**: Test files can import from `core` directly without path manipulation
- **Consistent Python Path**: Single `pythonpath` configuration in pytest

### `__init__.py` Requirements

Every Python package directory needs an `__init__.py` file (can be empty):

```python
# app/__init__.py
# app/core/__init__.py
# app/tests/__init__.py
# app/tests/core/__init__.py
```

---

## 2. pyproject.toml Configuration Template

### Complete Template

```toml
[project]
name = "your-project-name"
version = "0.1.0"
description = "A brief description of your project"
requires-python = ">=3.11"
dependencies = [
    # Core dependencies with version constraints
    # "requests>=2.28.0",
    # "pydantic>=2.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "pytest-cov>=4.0.0",
    "mypy>=1.0.0",
]

[dependency-groups]
dev = [
    "mypy>=1.18.2",
    "pytest>=9.0.1",
    "pytest-cov>=7.0.0",
    "ruff>=0.14.5",
]
build = [
    "pyinstaller>=6.0.0",
]

# =============================================================================
# pytest Configuration
# =============================================================================
[tool.pytest.ini_options]
# Configure pytest to run from app/ directory
testpaths = ["app/tests"]
# Set Python path for module resolution
pythonpath = ["app"]

# =============================================================================
# Coverage Configuration
# =============================================================================
[tool.coverage.run]
source = ["app"]
omit = [".venv/*", "build/*", "dist/*"]

# =============================================================================
# mypy Configuration
# =============================================================================
[tool.mypy]
python_version = "3.11"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
check_untyped_defs = true
exclude = ['.venv', 'build', 'dist']

# Override for third-party libraries without type stubs
[[tool.mypy.overrides]]
module = ["some_library", "another_library.*"]
ignore_missing_imports = true

# =============================================================================
# Ruff Configuration
# =============================================================================
[tool.ruff]
line-length = 88
target-version = "py311"
exclude = [".venv", "build", "dist", ".history"]

[tool.ruff.lint]
# E: pycodestyle errors, F: Pyflakes, I: isort
select = ["E", "F", "I"]
# E501: Line too long (handled by formatter)
ignore = ["E501"]

[tool.ruff.lint.isort]
known-first-party = ["app", "core"]
force-single-line = false
lines-after-imports = 2

[tool.ruff.format]
quote-style = "double"
indent-style = "space"

# =============================================================================
# Build System
# =============================================================================
[tool.hatch.build.targets.wheel]
packages = ["app/core"]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

---

## 3. Type Annotation Patterns

### Basic Type Annotations

```python
def process_data(name: str, count: int, enabled: bool = True) -> str:
    """Process data with type-annotated parameters and return type."""
    return f"{name}: {count}" if enabled else ""


def calculate_total(items: list[float]) -> float:
    """Function with generic type annotation."""
    return sum(items)
```

### Using `typing` Module Types

```python
from typing import Any, TypedDict


# TypedDict for structured dictionaries
class UserData(TypedDict):
    """User data structure with typed fields."""
    name: str
    age: int
    email: str


# Generic types (Python 3.9+ built-in syntax)
def process_records(records: list[dict[str, Any]]) -> dict[str, int]:
    """Process records and return counts."""
    return {}


# Union types with | syntax (Python 3.10+)
def find_item(items: list[str], key: str) -> str | None:
    """Find an item, returning None if not found."""
    return key if key in items else None
```

### Complex Nested Type Annotations

```python
from typing import Any


# Simple nested types
counts_by_name: dict[str, int] = {}

# Tuple keys in dictionaries
counts_by_pair: dict[tuple[str, str], int] = {}

# Complex nested structures
geometry_data: dict[str, set[tuple[float, float]]] = {}

# List of dictionaries
records: list[dict[str, Any]] = []

# Three-element tuple keys
rotation_counts: dict[tuple[str, str, str], int] = {}
```

### Return Type Patterns

```python
def void_function() -> None:
    """Function that returns nothing."""
    print("No return value")


def nullable_return(items: list[str], index: int) -> str | None:
    """Function that may return None."""
    if 0 <= index < len(items):
        return items[index]
    return None


def complex_return(data: dict[str, Any]) -> tuple[bool, str]:
    """Function returning multiple values."""
    return True, "success"
```

### Variable Annotations

```python
# Annotate complex variables for clarity
result_counts: dict[str, int] = {}
unique_values: set[tuple[float, float]] = set()
layer_colors: dict[str, set[tuple[int, int, int]]] = {}
```

---

## 4. TypedDict Best Practices

### When to Use TypedDict

Use `TypedDict` when:

- You need a dictionary with a fixed set of string keys
- Different keys have different value types
- You want IDE autocompletion and type checking for dictionary access
- The structure represents a data transfer object or API response

### Defining TypedDict with Documentation

```python
from typing import Any, TypedDict


class ProcessingResult(TypedDict):
    """
    Result structure from data processing operations.

    Attributes:
        item_counts: Dictionary mapping item names to their occurrence counts
        entity_data: Dictionary mapping entity names to their entity counts
        pair_data: Dictionary mapping (name, category) tuples to counts
        metadata: Additional processing metadata as nested dictionary
    """

    item_counts: dict[str, int]
    entity_data: dict[str, int]
    pair_data: dict[tuple[str, str], int]
    metadata: dict[str, Any]


class GeometryData(TypedDict):
    """
    Geometric analysis data for a single object.

    Attributes:
        native_width: Object width at 0-degree rotation
        native_height: Object height at 0-degree rotation
        vertical_segments: List of vertical segment sizes (left-to-right)
        horizontal_segments: List of horizontal segment sizes (bottom-to-top)
    """

    native_width: float
    native_height: float
    vertical_segments: list[float]
    horizontal_segments: list[float]
```

### Using TypedDict as Return Type

```python
def analyze_data(file_path: str) -> ProcessingResult:
    """
    Analyze data from a file.

    Args:
        file_path: Path to the data file

    Returns:
        ProcessingResult with counts, entities, pairs, and metadata
    """
    result: ProcessingResult = {
        "item_counts": {},
        "entity_data": {},
        "pair_data": {},
        "metadata": {},
    }
    # ... processing logic ...
    return result
```

---

## 5. Docstring Conventions (Google Style)

### Module-Level Docstring

```python
"""
Data processing utilities for the application.

This module provides functionality to parse data files, extract metrics,
and generate analysis reports.

Usage:
    from core.processor import process_file

    result = process_file('/path/to/data.json')
    # Returns: ProcessingResult with item_counts, entity_data, etc.
"""
```

### Function Docstring

```python
def process_data(
    file_path: str,
    options: dict[str, Any] | None = None,
) -> ProcessingResult:
    """
    Process data from a file and extract analysis metrics.

    This function loads a data file and extracts:
    - Item counts and categories
    - Entity relationships
    - Pair-based metrics

    Args:
        file_path: Path to the data file to process
        options: Optional configuration dictionary with processing options

    Returns:
        ProcessingResult TypedDict containing all analysis data.
        All dictionaries will be empty if the file contains no relevant data.

    Raises:
        FileNotFoundError: If the specified file does not exist
        ValueError: If the file format is not supported or file is corrupted

    Examples:
        >>> result = process_data('data.json')
        >>> result['item_counts']
        {'widget': 142, 'gadget': 89}
        >>> result['entity_data']
        {'widget': 8, 'gadget': 12}
    """
```

### Class Docstring

```python
class DataProcessor:
    """
    Process and analyze data files.

    This class provides methods for loading, validating, and extracting
    metrics from various data file formats.

    Attributes:
        file_path: Path to the currently loaded file
        options: Processing options dictionary
        _cache: Internal cache for processed results
    """

    def __init__(self, file_path: str, options: dict[str, Any] | None = None) -> None:
        """
        Initialize the DataProcessor.

        Args:
            file_path: Path to the data file
            options: Optional processing configuration
        """
        self.file_path = file_path
        self.options = options or {}
        self._cache: dict[str, Any] = {}
```

---

## 6. Testing Patterns

### Test File Naming

- Test files: `test_{module}.py`
- Test classes: `TestClassName` or `TestFunctionName`
- Test methods: `test_{method}_{scenario}`

### Test Class Organization

```python
"""
Unit tests for the processor module.

This test suite validates the data processing functionality including:
- Valid file processing with known data
- Empty file handling
- Invalid/corrupted file error handling
- Missing file error handling
- Count accuracy verification
- Return type validation
"""

import pytest

from core.processor import process_data


class TestProcessData:
    """Test suite for the process_data function."""

    def test_process_valid_file(self) -> None:
        """Test processing from valid data file with known counts."""
        result = process_data("app/tests/assets/sample_data.json")

        # Verify result is a ProcessingResult dict
        assert isinstance(result, dict)
        assert "item_counts" in result
        assert "entity_data" in result

    def test_process_empty_file(self) -> None:
        """Test processing from valid file with no data."""
        result = process_data("app/tests/assets/empty_data.json")

        # Verify result has all required keys with empty dicts
        assert isinstance(result, dict)
        assert result["item_counts"] == {}

    def test_process_invalid_file(self) -> None:
        """Test that invalid/corrupted files raise ValueError."""
        with pytest.raises(ValueError, match="Invalid or corrupted"):
            process_data("app/tests/assets/invalid.json")

    def test_process_missing_file(self) -> None:
        """Test that missing files raise FileNotFoundError."""
        with pytest.raises(FileNotFoundError, match="File not found"):
            process_data("app/tests/assets/nonexistent.json")
```

### Testing Categories

#### Happy Path Tests

```python
def test_process_valid_file(self) -> None:
    """Test extraction from valid file with known counts."""
    result = process_data("app/tests/assets/sample_data.json")
    assert result["item_counts"]["widget"] == 10
```

#### Edge Case Tests

```python
def test_process_empty_file(self) -> None:
    """Test extraction from valid file with no data."""
    result = process_data("app/tests/assets/empty_data.json")
    assert result["item_counts"] == {}

def test_process_single_item(self) -> None:
    """Test extraction with single item boundary case."""
    result = process_data("app/tests/assets/single_item.json")
    assert len(result["item_counts"]) == 1
```

#### Error Handling Tests

```python
def test_process_invalid_file(self) -> None:
    """Test that invalid files raise ValueError."""
    with pytest.raises(ValueError, match="Invalid or corrupted"):
        process_data("app/tests/assets/invalid.json")

def test_process_missing_file(self) -> None:
    """Test that missing files raise FileNotFoundError."""
    with pytest.raises(FileNotFoundError, match="File not found"):
        process_data("app/tests/assets/nonexistent.json")
```

#### Type Validation Tests

```python
def test_returns_correct_types(self) -> None:
    """Test that return value has correct types."""
    result = process_data("app/tests/assets/sample_data.json")

    assert isinstance(result, dict)
    for key, value in result["item_counts"].items():
        assert isinstance(key, str)
        assert isinstance(value, int)
```

#### Conservation/Invariant Tests

```python
def test_pair_counts_conservation(self) -> None:
    """Test that sum of pair counts equals sum of item counts."""
    result = process_data("app/tests/assets/sample_data.json")

    total_pair_count = sum(result["pair_data"].values())
    total_item_count = sum(result["item_counts"].values())

    assert total_pair_count == total_item_count
```

### pytest Features

#### Fixtures

```python
import pytest


@pytest.fixture
def sample_data_path() -> str:
    """Provide path to sample data file."""
    return "app/tests/assets/sample_data.json"


@pytest.fixture
def processor_instance(sample_data_path: str) -> DataProcessor:
    """Create a DataProcessor instance for testing."""
    return DataProcessor(sample_data_path)


def test_with_fixture(processor_instance: DataProcessor) -> None:
    """Test using fixture-provided instance."""
    result = processor_instance.process()
    assert "item_counts" in result
```

#### Parametrized Tests

```python
@pytest.mark.parametrize(
    "angle,expected_category",
    [
        (0.0, "0"),
        (90.0, "90"),
        (180.0, "180"),
        (270.0, "270"),
        (45.0, "other"),
        (-90.0, "270"),
        (450.0, "90"),
    ],
)
def test_categorize_angle_parametrized(
    angle: float, expected_category: str
) -> None:
    """Test angle categorization with parametrized test cases."""
    assert categorize_angle(angle) == expected_category
```

#### pytest.raises for Exception Testing

```python
def test_invalid_input_raises_value_error(self) -> None:
    """Test that invalid input raises ValueError with specific message."""
    with pytest.raises(ValueError, match="Unsupported format"):
        process_data("invalid.txt")
```

#### pytest.mark.skip for Conditional Skipping

```python
@pytest.mark.skip(reason="Feature not yet implemented")
def test_future_feature(self) -> None:
    """Test for a feature that's not yet implemented."""
    pass


@pytest.mark.skipif(
    sys.platform == "win32",
    reason="Test not supported on Windows"
)
def test_unix_only_feature(self) -> None:
    """Test that only runs on Unix systems."""
    pass
```

#### pytest.approx for Floating-Point Comparisons

```python
def test_floating_point_calculation(self) -> None:
    """Test floating-point calculations with tolerance."""
    result = calculate_ratio(10, 3)
    assert result == pytest.approx(3.33, abs=0.01)

def test_segment_rounding(self) -> None:
    """Test specific rounding behavior."""
    segments = calculate_segments([0.0, 10.555, 20.999])
    assert segments[0] == pytest.approx(10.56, abs=0.01)
```

#### Mocking with unittest.mock

```python
from unittest.mock import patch, MagicMock


def test_external_api_call(self) -> None:
    """Test function that calls external API."""
    with patch("core.processor.external_api.fetch") as mock_fetch:
        mock_fetch.return_value = {"status": "success"}

        result = process_with_api("data.json")

        assert mock_fetch.called
        assert result["status"] == "success"


def test_generic_exception_handling(self) -> None:
    """Test that unexpected exceptions are re-raised with logging."""
    with patch("core.processor.load_file") as mock_load:
        mock_load.side_effect = RuntimeError("Unexpected error")

        with pytest.raises(RuntimeError, match="Unexpected error"):
            process_data("app/tests/assets/sample_data.json")
```

---

## 7. Test Organization Best Practices

### Test File Structure

```python
"""
Unit tests for the geometry module.

This test suite validates geometric calculation utilities including:
- Bounding box calculation for various entity types
- Intersection point detection and deduplication
- Segment distance calculation
- Rotation angle categorization
"""

import pytest

from core.geometry import (
    calculate_bounding_box,
    calculate_segments,
    categorize_rotation,
    get_intersection_points,
)


class TestBoundingBox:
    """Test suite for calculate_bounding_box function."""

    def test_bounding_box_simple_rectangle(self) -> None:
        """Test bounding box extraction for simple rectangular shape."""
        # Arrange
        shape = create_rectangle(0, 0, 100, 50)

        # Act
        bbox = calculate_bounding_box(shape)

        # Assert
        assert bbox == (0.0, 0.0, 100.0, 50.0)

    def test_bounding_box_empty_shape(self) -> None:
        """Test that empty shape returns (0, 0, 0, 0)."""
        shape = create_empty_shape()
        bbox = calculate_bounding_box(shape)
        assert bbox == (0.0, 0.0, 0.0, 0.0)


class TestCalculateSegments:
    """Test suite for calculate_segments function."""

    def test_calculate_segments_normal(self) -> None:
        """Test segment calculation with typical point list."""
        points = [0.0, 50.0, 1150.0, 1200.0]
        segments = calculate_segments(points)

        assert len(segments) == 3
        assert segments == [50.0, 1100.0, 50.0]

    def test_calculate_segments_empty_list(self) -> None:
        """Test segment calculation with empty list."""
        assert calculate_segments([]) == []

    def test_calculate_segments_single_point(self) -> None:
        """Test segment calculation with single point."""
        assert calculate_segments([0.0]) == []


class TestCategorizeRotation:
    """Test suite for categorize_rotation function."""

    def test_categorize_rotation_standard_angles(self) -> None:
        """Test rotation categorization for exact standard angles."""
        assert categorize_rotation(0.0) == "0"
        assert categorize_rotation(90.0) == "90"
        assert categorize_rotation(180.0) == "180"
        assert categorize_rotation(270.0) == "270"

    @pytest.mark.parametrize(
        "rotation,expected_category",
        [
            (0.0, "0"),
            (45.0, "other"),
            (90.0, "90"),
            (-90.0, "270"),
        ],
    )
    def test_categorize_rotation_parametrized(
        self, rotation: float, expected_category: str
    ) -> None:
        """Test rotation categorization with parametrized cases."""
        assert categorize_rotation(rotation) == expected_category
```

### Test Assets Organization

```
app/tests/assets/
├── sample_data.json        # Standard test data
├── empty_data.json         # Empty file for edge cases
├── invalid.json            # Corrupted/invalid file
├── single_item.json        # Single item boundary case
├── large_dataset.json      # Performance testing
└── create_test_data.py     # Script to generate test fixtures
```

---

## 8. Constants Module Pattern

### Organization and Naming

```python
"""
Application-wide constants for the project.

This module defines all constants used throughout the application including:
- Supported file extensions
- Output configuration (column names, sheet names)
- User-facing messages for UI and error handling

Usage:
    from core.constants import SUPPORTED_EXTENSIONS, DEFAULT_TIMEOUT
"""

# =============================================================================
# File Extensions
# =============================================================================
SUPPORTED_EXTENSIONS: tuple[str, str] = (".json", ".xml")

# =============================================================================
# Output Configuration - Sheet Names
# =============================================================================
OUTPUT_SHEET_SUMMARY: str = "Summary"
OUTPUT_SHEET_DETAILS: str = "Details"
OUTPUT_SHEET_METRICS: str = "Metrics"

# =============================================================================
# Output Configuration - Column Names
# =============================================================================
# Naming convention: {DOMAIN}_{ATTRIBUTE}_{QUALIFIER}
COLUMN_ITEM_NAME: str = "item_name"
COLUMN_ITEM_COUNT: str = "item_count"
COLUMN_ENTITY_TYPE: str = "entity_type"
COLUMN_LAYER_NAME: str = "layer_name"

# =============================================================================
# Styling Constants
# =============================================================================
FILL_COLOR_WARNING: str = "FFFFFF00"  # Yellow
FILL_COLOR_ERROR: str = "FFFF0000"    # Red
FILL_COLOR_SUCCESS: str = "FF00FF00"  # Green

# =============================================================================
# Processing Configuration
# =============================================================================
DEFAULT_TIMEOUT: int = 30
MAX_RETRIES: int = 3
BATCH_SIZE: int = 100

# =============================================================================
# UI Messages
# =============================================================================
MSG_SELECT_FILE: str = "Please select a file"
MSG_PROCESSING: str = "Processing..."
MSG_SUCCESS: str = "Operation complete"
MSG_ERROR_INVALID_FILE: str = "Invalid or corrupted file"
MSG_ERROR_NOT_FOUND: str = "File not found"
```

---

## 9. Logger Module Pattern

### Centralized Logging Configuration

```python
"""
Centralized logging configuration for the application.

This module provides stdout-only logging to enable real-time monitoring
during development and workflow execution.
"""

import logging
import sys


def setup_logger(name: str) -> logging.Logger:
    """
    Create and configure a logger with stdout output only.

    Args:
        name: The name for the logger (typically __name__ from the calling module)

    Returns:
        A configured logger instance with stdout handler

    Example:
        >>> from core.logger import setup_logger
        >>> logger = setup_logger(__name__)
        >>> logger.info("Starting process")
    """
    logger = logging.getLogger(name)

    # Only add handler if the logger doesn't have one already
    if not logger.handlers:
        # Create stdout handler
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(logging.INFO)

        # Set format
        formatter = logging.Formatter(
            "%(asctime)s [%(name)s] %(levelname)s: %(message)s"
        )
        handler.setFormatter(formatter)

        # Add handler to logger
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)

    return logger
```

### Usage in Modules

```python
from .logger import setup_logger

logger = setup_logger(__name__)


def process_data(file_path: str) -> dict[str, Any]:
    """Process data from file."""
    logger.info(f"Starting data extraction from {file_path}")

    try:
        # ... processing logic ...
        logger.info(f"Found {total_items} items")
        return result

    except ValueError as e:
        logger.error(f"Invalid file: {file_path} - {str(e)}")
        raise
```

---

## 10. Code Quality Commands

### Testing

```bash
# Run all tests
uv run pytest app/tests/

# Run with verbose output
uv run pytest app/tests/ -v

# Run specific test file
uv run pytest app/tests/core/test_processor.py

# Run specific test class
uv run pytest app/tests/core/test_processor.py::TestProcessData

# Run specific test method
uv run pytest app/tests/core/test_processor.py::TestProcessData::test_valid_file
```

### Coverage

```bash
# Run tests with coverage
uv run pytest --cov=app app/tests/

# Run with coverage report
uv run pytest --cov=app --cov-report=html app/tests/

# Run coverage for specific module
uv run pytest --cov=app/core app/tests/
```

### Type Checking

```bash
# Run mypy on entire app
uv run mypy app/

# Run mypy on specific module
uv run mypy app/core/processor.py

# Run mypy with strict mode
uv run mypy app/ --strict
```

### Linting and Formatting

```bash
# Check for linting issues
uv run ruff check app/

# Auto-fix linting issues
uv run ruff check app/ --fix

# Format code
uv run ruff format app/

# Check formatting without changes
uv run ruff format app/ --check
```

---

## 11. README Template

```markdown
# Project Name

A brief description of what this project does.

## Purpose

Describe the main functionality and goals:
- Feature 1
- Feature 2
- Feature 3

**User Flow:** Describe the typical workflow (e.g., "Select file -> Process -> View output")

## Tech Stack

- **Python:** 3.11+ (managed with uv)
- **Data Processing:** pandas (data manipulation)
- **Testing:** pytest with coverage reporting
- **Type Checking:** mypy with strict configuration
- **Package Manager:** uv (all dependency management)

## Project Structure

\`\`\`
project-name/
├── app/                          # Application code
│   ├── core/                     # Business logic
│   │   ├── constants.py          # App constants
│   │   ├── processor.py          # Main processing logic
│   │   └── logger.py             # Stdout logging
│   ├── tests/                    # Test suite
│   │   ├── core/                 # Unit tests
│   │   └── assets/               # Test fixtures
│   └── main.py                   # Entry point
│
├── scripts/                      # Utility scripts
│   ├── start.sh                  # Launch application
│   └── build.sh                  # Build executable
│
├── .venv/                        # Virtual environment
└── pyproject.toml                # Project config
\`\`\`

## Usage

### Running the Application

\`\`\`bash
bash scripts/start.sh
\`\`\`

### Testing

\`\`\`bash
# Run all tests
uv run pytest app/tests/

# Run with coverage
uv run pytest --cov=app app/tests/
\`\`\`

### Code Quality

\`\`\`bash
# Type check
uv run mypy app/

# Lint
uv run ruff check app/

# Format
uv run ruff format app/
\`\`\`

## Reference Files

- `ai_docs/001-naming-convention-guide.md`
- Additional documentation files...

## Working Directory Convention

- **Always execute commands from project root**
- **Use `uv run <command>` with root-relative paths**
- **File operations use root-relative paths**

## Dev Environment

- Platform: [Your platform]
- Project directory: `/path/to/project`
- Special notes: [Any platform-specific notes]
```

---

## Official Documentation Links

- **pytest**: https://docs.pytest.org/
- **mypy**: https://mypy.readthedocs.io/
- **ruff**: https://docs.astral.sh/ruff/
- **uv**: https://docs.astral.sh/uv/
- **Python typing**: https://docs.python.org/3/library/typing.html
- **TypedDict**: https://docs.python.org/3/library/typing.html#typing.TypedDict
