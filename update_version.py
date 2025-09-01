#!/usr/bin/env python3
"""
Utility script to update the application version.
This script can be used during development to set or update the version file.
"""

import argparse
import subprocess  # nosec B404 - Used for controlled git commands only
import sys
from pathlib import Path


def get_git_version():
    """Get version from git tags."""
    try:
        # Try to get the exact tag first
        version = subprocess.check_output(  # nosec B603, B607 - Controlled git command
            ["git", "describe", "--tags", "--exact-match", "HEAD"], stderr=subprocess.DEVNULL, text=True
        ).strip()
        return version
    except subprocess.CalledProcessError:
        # Fall back to latest tag with commit info
        try:
            version = subprocess.check_output(  # nosec B603, B607 - Controlled git command
                ["git", "describe", "--tags", "--abbrev=7", "--dirty"], stderr=subprocess.DEVNULL, text=True
            ).strip()
            return version
        except subprocess.CalledProcessError:
            return None


def write_version_file(version):
    """Write version to VERSION file."""
    version_file = Path(__file__).parent / "VERSION"
    with open(version_file, "w", encoding="utf-8") as f:
        f.write(version + "\n")
    print(f"✅ Written version '{version}' to VERSION file")


def main():
    parser = argparse.ArgumentParser(description="Update application version")
    parser.add_argument("version", nargs="?", help="Version to set (if not provided, tries to get from git)")
    parser.add_argument("--from-git", action="store_true", help="Force getting version from git")

    args = parser.parse_args()

    if args.version:
        version = args.version
        print(f"📝 Setting version to: {version}")
    elif args.from_git or not args.version:
        print("🔍 Getting version from git...")
        version = get_git_version()
        if not version:
            print("❌ Could not determine version from git. No tags found.")
            print("💡 Create a git tag first: git tag v1.0.0")
            sys.exit(1)
        print(f"📝 Found git version: {version}")

    write_version_file(version)

    # Import and check the version module
    try:
        from demowebapp.version import get_cached_version

        detected_version = get_cached_version()
        print(f"✅ Application will now report version: {detected_version}")

        if detected_version != version:
            print("⚠️  Note: Application detected different version due to fallback logic")
    except ImportError as e:
        print(f"⚠️  Could not verify version import: {e}")


if __name__ == "__main__":
    main()
