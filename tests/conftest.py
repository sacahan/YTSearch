"""pytest configuration and shared fixtures."""

import sys
from pathlib import Path

import pytest


# Add project root and src directory to Python path at module level
# This is necessary for import resolution in tests
project_root = Path(__file__).parent.parent
src_path = project_root / "src"

# Only add if not already present to avoid duplicates
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))


@pytest.fixture(scope="session", autouse=True)
def setup_python_path():
    """
    Ensure src directory is in Python path for all tests with proper cleanup.
    
    This fixture is auto-used for all tests to ensure consistent import behavior.
    Although sys.path is modified at module level above, this fixture provides
    explicit cleanup for test isolation.
    """
    original_path = sys.path.copy()
    
    # Ensure paths are at the front
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    
    yield
    
    # Restore original path after all tests
    sys.path[:] = original_path
