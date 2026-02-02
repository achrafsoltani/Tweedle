"""Application entry point and setup."""

import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from tweedle.ui.main_window import MainWindow


def run_app() -> int:
    """Initialize and run the application."""
    QApplication.setAttribute(Qt.AA_ShareOpenGLContexts)

    app = QApplication(sys.argv)
    app.setApplicationName("Tweedle")
    app.setApplicationDisplayName("Tweedle")
    app.setOrganizationName("Tweedle")
    app.setOrganizationDomain("tweedle.local")

    app.setStyle("Fusion")

    window = MainWindow()
    window.show()

    return app.exec()
