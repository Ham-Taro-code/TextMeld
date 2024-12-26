import pytest
from pathlib import Path


def pytest_configure(config):
    """Pytest configuration hook."""
    config.addinivalue_line("markers", "integration: mark test as integration test.")
