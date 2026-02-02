#!/usr/bin/env python3
"""Build script for Tweedle email client."""

import os
import sys
import shutil
import subprocess
import platform
from pathlib import Path

PROJECT_NAME = "Tweedle"
PROJECT_NAME_LOWER = "tweedle"
VERSION = "1.0.0"
AUTHOR = "Achraf SOLTANI"
DESCRIPTION = "A modern email client for Linux and Windows"

ROOT_DIR = Path(__file__).parent
DIST_DIR = ROOT_DIR / "dist"
BUILD_DIR = ROOT_DIR / "build"
RESOURCES_DIR = ROOT_DIR / "resources"
ICONS_DIR = RESOURCES_DIR / "icons"


def clean():
    """Clean build artifacts."""
    print("Cleaning build artifacts...")

    dirs_to_clean = [DIST_DIR, BUILD_DIR, ROOT_DIR / "__pycache__"]
    for d in dirs_to_clean:
        if d.exists():
            shutil.rmtree(d)
            print(f"  Removed {d}")

    # Clean pycache in subdirectories
    for pycache in ROOT_DIR.rglob("__pycache__"):
        shutil.rmtree(pycache)
        print(f"  Removed {pycache}")

    # Clean .pyc files
    for pyc in ROOT_DIR.rglob("*.pyc"):
        pyc.unlink()
        print(f"  Removed {pyc}")

    # Clean spec files
    for spec in ROOT_DIR.glob("*.spec"):
        spec.unlink()
        print(f"  Removed {spec}")

    print("Clean complete.")


def create_ico():
    """Create Windows ICO file from PNG."""
    print("Creating Windows ICO file...")

    png_path = ICONS_DIR / "app_icon.png"
    ico_path = ICONS_DIR / "app_icon.ico"

    if not png_path.exists():
        print(f"  Error: {png_path} not found")
        return False

    try:
        from PIL import Image

        img = Image.open(png_path)

        # Create multiple sizes for ICO
        sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
        icons = []

        for size in sizes:
            resized = img.resize(size, Image.Resampling.LANCZOS)
            icons.append(resized)

        icons[0].save(
            ico_path,
            format='ICO',
            sizes=[(s[0], s[1]) for s in sizes],
            append_images=icons[1:]
        )

        print(f"  Created {ico_path}")
        return True

    except ImportError:
        print("  Error: Pillow not installed. Run: pip install Pillow")
        return False
    except Exception as e:
        print(f"  Error creating ICO: {e}")
        return False


def build():
    """Build the application using PyInstaller."""
    print(f"Building {PROJECT_NAME} v{VERSION}...")

    system = platform.system().lower()
    print(f"  Platform: {system}")

    # Determine icon path
    if system == "windows":
        icon_path = ICONS_DIR / "app_icon.ico"
        if not icon_path.exists():
            print("  Creating ICO file for Windows...")
            create_ico()
    else:
        icon_path = ICONS_DIR / "app_icon.png"

    # PyInstaller command
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name", PROJECT_NAME,
        "--onedir",
        "--windowed",
        "--clean",
        "--noconfirm",
    ]

    # Add icon if exists
    if icon_path.exists():
        cmd.extend(["--icon", str(icon_path)])

    # Add hidden imports for PySide6
    hidden_imports = [
        "PySide6.QtCore",
        "PySide6.QtGui",
        "PySide6.QtWidgets",
        "PySide6.QtWebEngineWidgets",
        "PySide6.QtWebEngineCore",
        "imapclient",
        "keyring",
        "keyring.backends",
    ]

    for imp in hidden_imports:
        cmd.extend(["--hidden-import", imp])

    # Collect all PySide6 data
    cmd.extend(["--collect-all", "PySide6"])

    # Add the main script
    cmd.append(str(ROOT_DIR / "main.py"))

    print(f"  Running: {' '.join(cmd[:5])}...")

    result = subprocess.run(cmd, cwd=ROOT_DIR)

    if result.returncode == 0:
        print(f"\nBuild successful!")
        print(f"  Output: {DIST_DIR / PROJECT_NAME}")
    else:
        print(f"\nBuild failed with code {result.returncode}")
        sys.exit(1)


def run_tests():
    """Run the test suite."""
    print("Running tests...")

    result = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/", "-v"],
        cwd=ROOT_DIR
    )

    if result.returncode != 0:
        print("Tests failed!")
        sys.exit(1)

    print("All tests passed.")


def show_help():
    """Show help message."""
    print(f"""
{PROJECT_NAME} Build Script
===========================

Usage: python build.py <command>

Commands:
  clean     Remove build artifacts
  build     Build standalone executable
  ico       Create Windows ICO from PNG
  test      Run test suite
  help      Show this help message

Examples:
  python build.py clean
  python build.py build
  python build.py clean build
""")


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        show_help()
        sys.exit(0)

    commands = {
        "clean": clean,
        "build": build,
        "ico": create_ico,
        "test": run_tests,
        "help": show_help,
    }

    for arg in sys.argv[1:]:
        if arg in commands:
            commands[arg]()
        else:
            print(f"Unknown command: {arg}")
            show_help()
            sys.exit(1)


if __name__ == "__main__":
    main()
