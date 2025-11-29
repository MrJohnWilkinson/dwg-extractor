"""Shared fixtures for excel_formatting tests."""

import tempfile
from typing import Iterator

import pytest


@pytest.fixture
def temp_dir() -> Iterator[str]:
    """Create a temporary directory for test outputs."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir
