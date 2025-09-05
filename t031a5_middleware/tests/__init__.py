"""Test package for t031a5_middleware.

This package contains unit tests for all modules of the middleware system.
"""

import sys
import os
from pathlib import Path

# Add the parent directory to the Python path for imports
test_dir = Path(__file__).parent
project_root = test_dir.parent
sys.path.insert(0, str(project_root))

# Test configuration
TEST_CONFIG = {
    "log_level": "DEBUG",
    "test_data_dir": test_dir / "data",
    "mock_hardware": True,
    "timeout": 5.0
}

# Common test utilities
def get_test_config():
    """Get test configuration."""
    return TEST_CONFIG.copy()


def setup_test_environment():
    """Setup test environment."""
    # Create test data directory if it doesn't exist
    test_data_dir = TEST_CONFIG["test_data_dir"]
    test_data_dir.mkdir(exist_ok=True)
    
    # Set environment variables for testing
    os.environ["TESTING"] = "true"
    os.environ["LOG_LEVEL"] = TEST_CONFIG["log_level"]
    os.environ["MOCK_HARDWARE"] = str(TEST_CONFIG["mock_hardware"])


def teardown_test_environment():
    """Cleanup test environment."""
    # Remove test environment variables
    for key in ["TESTING", "LOG_LEVEL", "MOCK_HARDWARE"]:
        os.environ.pop(key, None)


# Setup test environment when module is imported
setup_test_environment()