"""
Pytest configuration to ensure tests run with app/ as the working directory.
This allows tests to use relative paths like 'tests/assets/sample.dxf'.
"""
import os
from pathlib import Path


def pytest_configure(config):
    """Change working directory to app/ before running tests."""
    app_dir = Path(__file__).parent / "app"
    os.chdir(app_dir)
