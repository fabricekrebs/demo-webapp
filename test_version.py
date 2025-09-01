#!/usr/bin/env python3
"""
Test script to demonstrate version detection in different scenarios.
"""

import os
import sys
from pathlib import Path

# Add the project directory to the path
sys.path.insert(0, str(Path(__file__).parent))

from demowebapp.version import get_version


def test_scenarios():
    """Test different version detection scenarios."""
    print("=== Version Detection Test ===\n")

    # Scenario 1: Current state (should detect git version)
    print("1. Current state (from git):")
    version = get_version()
    print(f"   Detected: {version}")
    print()

    # Scenario 2: With APP_VERSION environment variable
    print("2. With APP_VERSION environment variable:")
    os.environ["APP_VERSION"] = "v2.1.0"
    # Need to clear the cache and re-import to test this
    import importlib

    import demowebapp.version

    importlib.reload(demowebapp.version)
    version = demowebapp.version.get_version()
    print(f"   Detected: {version}")
    del os.environ["APP_VERSION"]
    print()

    # Scenario 3: Create a VERSION file
    print("3. With VERSION file:")
    version_file = Path(__file__).parent / "VERSION"
    version_file.write_text("v3.0.0-beta.1\n")

    # Reload the module again
    importlib.reload(demowebapp.version)
    version = demowebapp.version.get_version()
    print(f"   Detected: {version}")

    # Clean up
    version_file.unlink()
    print()

    # Scenario 4: No git, no VERSION file, no env var
    print("4. Fallback scenario (simulated):")
    print("   Would detect: dev-unknown")
    print()

    print("=== API Endpoints ===")
    print("Health check: http://localhost:8000/health/")
    print("App info: http://localhost:8000/api/info/")
    print("\n=== In Production ===")
    print("Version will be injected via Docker build args during CI/CD:")
    print("  docker build --build-arg APP_VERSION=v1.2.3 .")


if __name__ == "__main__":
    test_scenarios()
