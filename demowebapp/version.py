"""
Version management for the Django application.
This module handles version retrieval from various sources during different deployment scenarios.
"""

import os
import subprocess  # nosec B404 - Used for controlled git commands only
from pathlib import Path


def get_version():
    """
    Get the application version from various sources in order of preference:
    1. APP_VERSION environment variable (set during Docker build)
    2. Git tag (if in a git repository and has tags)
    3. VERSION file (fallback for development)
    4. Default development version
    """

    # First try environment variable (used in production builds)
    env_version = os.getenv("APP_VERSION")
    if env_version:
        return env_version.strip()

    # Try to get version from git tags
    try:
        # Check if we're in a git repository
        git_version = subprocess.check_output(  # nosec B603, B607 - Controlled git command
            ["git", "describe", "--tags", "--exact-match", "HEAD"],
            stderr=subprocess.DEVNULL,
            text=True,
            cwd=Path(__file__).parent.parent,
        ).strip()
        if git_version:
            return git_version
    except (subprocess.CalledProcessError, FileNotFoundError):
        # Git command failed or git not found
        pass

    # Try to get the latest git tag (even if not on exact commit)
    try:
        git_version = subprocess.check_output(  # nosec B603, B607 - Controlled git command
            ["git", "describe", "--tags", "--abbrev=0"],
            stderr=subprocess.DEVNULL,
            text=True,
            cwd=Path(__file__).parent.parent,
        ).strip()
        if git_version:
            # Add commit hash for non-release builds
            try:
                commit_hash = subprocess.check_output(  # nosec B603, B607 - Controlled git command
                    ["git", "rev-parse", "--short", "HEAD"],
                    stderr=subprocess.DEVNULL,
                    text=True,
                    cwd=Path(__file__).parent.parent,
                ).strip()
                return f"{git_version}-dev.{commit_hash}"
            except subprocess.CalledProcessError:
                return f"{git_version}-dev"
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass

    # Try to read from VERSION file
    version_file = Path(__file__).parent.parent / "VERSION"
    if version_file.exists():
        try:
            with open(version_file, "r", encoding="utf-8") as f:
                file_version = f.read().strip()
                if file_version:
                    return file_version
        except IOError:
            pass

    # Fallback to development version
    return "dev-unknown"


# Cache the version to avoid repeated system calls
_cached_version = None


def get_cached_version():
    """Get the cached version, computing it only once."""
    global _cached_version
    if _cached_version is None:
        _cached_version = get_version()
    return _cached_version


# Module-level version variable for easy import
__version__ = get_cached_version()
