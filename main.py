"""
Automation Studio – entry point.
Run with: python main.py
"""
import sys
import os

# Ensure the project root is on sys.path so all sub-packages resolve correctly.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QFont
from gui.main_window import MainWindow


def main() -> None:
    app = QApplication(sys.argv)
    app.setApplicationName("Automation Studio")
    app.setOrganizationName("AutoStudio")

    font = QFont("Segoe UI", 10)
    app.setFont(font)

    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
