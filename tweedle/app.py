"""Application entry point and setup."""

import sys
from pathlib import Path
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QIcon

from tweedle.ui.main_window import MainWindow


def get_icon_path() -> Path:
    """Get the path to the application icon."""
    # Try relative to this file
    icon_path = Path(__file__).parent.parent / "resources" / "icons" / "app_icon.png"
    if icon_path.exists():
        return icon_path

    # Try relative to main.py
    icon_path = Path(__file__).parent.parent / "resources" / "icons" / "app_icon.png"
    if icon_path.exists():
        return icon_path

    # Try system location (for installed packages)
    system_paths = [
        Path("/usr/share/icons/hicolor/256x256/apps/tweedle.png"),
        Path("/usr/share/pixmaps/tweedle.png"),
    ]
    for path in system_paths:
        if path.exists():
            return path

    return None


def run_app() -> int:
    """Initialize and run the application."""
    QApplication.setAttribute(Qt.AA_ShareOpenGLContexts)

    app = QApplication(sys.argv)
    app.setApplicationName("Tweedle")
    app.setApplicationDisplayName("Tweedle")
    app.setOrganizationName("Tweedle")
    app.setOrganizationDomain("tweedle.local")

    # Set application icon
    icon_path = get_icon_path()
    if icon_path:
        app_icon = QIcon(str(icon_path))
        app.setWindowIcon(app_icon)

    app.setStyle("Fusion")

    window = MainWindow()
    window.show()

    return app.exec()
