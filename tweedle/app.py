"""Application entry point and setup."""

import sys
import os
from pathlib import Path
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon


def get_icon_path() -> Path:
    """Get the path to the application icon."""
    # Try relative to this file (development)
    icon_path = Path(__file__).parent.parent / "resources" / "icons" / "app_icon.png"
    if icon_path.exists():
        return icon_path

    # Try system locations (installed)
    system_paths = [
        Path("/usr/share/icons/hicolor/256x256/apps/tweedle.png"),
        Path("/usr/share/pixmaps/tweedle.png"),
        Path.home() / ".local/share/icons/tweedle.png",
    ]
    for path in system_paths:
        if path.exists():
            return path

    return None


def run_app() -> int:
    """Initialize and run the application."""
    # Set app ID for proper taskbar grouping on Linux
    if sys.platform == "linux":
        os.environ.setdefault("QT_QPA_PLATFORMTHEME", "gtk3")
        # Set the desktop file name for proper icon display
        try:
            from PySide6.QtGui import QGuiApplication
            QGuiApplication.setDesktopFileName("tweedle")
        except Exception:
            pass

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

    # Import here to avoid circular imports
    from tweedle.ui.main_window import MainWindow

    window = MainWindow()

    # Set window icon explicitly
    if icon_path:
        window.setWindowIcon(QIcon(str(icon_path)))

    window.show()

    return app.exec()
