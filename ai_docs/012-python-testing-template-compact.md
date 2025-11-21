# Python Project Template (Compact)

Concise template for Python project structure, testing, and typing.

## Project Structure

```
project-root/
├── app/
│   ├── core/                 # Business logic
│   │   ├── __init__.py
│   │   ├── constants.py
│   │   └── {module}.py
│   ├── tests/
│   │   ├── __init__.py
│   │   ├── core/test_{module}.py
│   │   └── assets/           # Test fixtures
│   └── main.py
├── pyproject.toml
└── README.md
```

## pyproject.toml

```toml
[project]
name = "my-project"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = []

[dependency-groups]
dev = ["mypy>=1.18.0", "pytest>=9.0.0", "pytest-cov>=7.0.0", "ruff>=0.14.0"]

[tool.pytest.ini_options]
testpaths = ["app/tests"]
pythonpath = ["app"]

[tool.coverage.run]
source = ["app"]
omit = [".venv/*", "build/*"]

[tool.mypy]
python_version = "3.11"
disallow_untyped_defs = true
check_untyped_defs = true
exclude = ['.venv', 'build']

[[tool.mypy.overrides]]
module = ["third_party.*"]
ignore_missing_imports = true

[tool.ruff]
line-length = 88
target-version = "py311"

[tool.ruff.lint]
select = ["E", "F", "I"]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

## Type Annotations

```python
# Basic
def process(name: str, count: int = 0) -> str: ...

# Collections
def get_items() -> list[str]: ...
def get_map() -> dict[str, int]: ...

# Optional
def find(id: str) -> User | None: ...

# Complex nested
def get_data() -> dict[tuple[str, str], int]: ...
def get_scales() -> dict[str, set[tuple[float, float]]]: ...

# TypedDict for structured returns
from typing import TypedDict

class Result(TypedDict):
    items: dict[str, int]
    errors: list[str]
```

## Test Patterns

```python
"""Unit tests for processor module."""
import pytest
from unittest.mock import patch
from core.processor import process_data

class TestProcessData:
    """Tests for process_data function."""

    def test_valid_input(self) -> None:
        result = process_data({"key": "value"})
        assert result["status"] == "success"

    def test_empty_input(self) -> None:
        assert process_data({})["items"] == []

    def test_invalid_raises_error(self) -> None:
        with pytest.raises(ValueError, match="Invalid"):
            process_data(None)

    @pytest.mark.parametrize("val,expected", [(0, "zero"), (1, "one")])
    def test_categorize(self, val: int, expected: str) -> None:
        assert categorize(val) == expected

    def test_mocked_call(self) -> None:
        with patch("core.processor.api") as mock:
            mock.return_value = {"data": [1]}
            result = process_data({"fetch": True})
            assert mock.called

    def test_float_comparison(self) -> None:
        assert calculate(10, 3) == pytest.approx(3.33, abs=0.01)
```

## Constants Pattern

```python
"""Application constants."""
SUPPORTED_EXTENSIONS: tuple[str, ...] = (".csv", ".json")
DEFAULT_TIMEOUT: int = 30
MSG_SUCCESS: str = "Operation completed"
```

## Logger Pattern

```python
"""Logging configuration."""
import logging, sys

def setup_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        h = logging.StreamHandler(sys.stdout)
        h.setFormatter(logging.Formatter("%(asctime)s [%(name)s] %(levelname)s: %(message)s"))
        logger.addHandler(h)
        logger.setLevel(logging.INFO)
    return logger
```

## Commands

```bash
uv run pytest app/tests/              # Run tests
uv run pytest --cov=app app/tests/    # With coverage
uv run mypy app/                      # Type check
uv run ruff check app/                # Lint
uv run ruff format app/               # Format
```

## Docstring Format

```python
def process(items: list[str], limit: int = 10) -> dict[str, int]:
    """
    Process items and return counts.

    Args:
        items: List of items to process
        limit: Max items (default: 10)

    Returns:
        Dict mapping items to counts

    Raises:
        ValueError: If items empty
    """
```

## Key Rules

1. **All functions typed** - params + return
2. **Test methods return `-> None`**
3. **Test naming**: `test_{function}_{scenario}`
4. **Constants**: `SCREAMING_SNAKE_CASE` with types
5. **Run from project root** - paths relative to root
