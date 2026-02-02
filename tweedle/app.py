"""Application entry point and setup."""

import sys
import os
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon


def run_app() -> int:
    """Initialize and run the application."""
    # Enable high DPI scaling
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    QApplication.setAttribute(Qt.AA_ShareOpenGLContexts)

    app = QApplication(sys.argv)
    app.setApplicationName("Tweedle")
    app.setOrganizationName("Tweedle")
    app.setDesktopFileName("tweedle")

    # Set application icon - try theme icon first, fallback to file
    app_icon = QIcon.fromTheme("tweedle")
    if app_icon.isNull():
        base_path = os.path.dirname(os.path.abspath(__file__))
        icon_path = os.path.join(base_path, "..", "resources", "icons", "app_icon.png")
        app_icon = QIcon(icon_path)

    app.setStyle("Fusion")

    # Import here to avoid circular imports
    from tweedle.ui.main_window import MainWindow

    window = MainWindow()
    window.setWindowIcon(app_icon)
    app.setWindowIcon(app_icon)
    window.show()
    window.raise_()
    window.activateWindow()

    return app.exec()
