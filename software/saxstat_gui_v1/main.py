"""
SaxStat GUI v1 - Main Application Entry Point

This module initializes and launches the SaxStat GUI application.
"""

import sys
from PyQt5.QtWidgets import QApplication
from saxstat_gui_v1.gui.main_window import MainWindow


def main():
    """Launch the SaxStat GUI application."""
    app = QApplication(sys.argv)
    app.setApplicationName("SaxStat")
    app.setApplicationVersion("1.0.0-dev")
    app.setOrganizationName("SaxStat")

    window = MainWindow()
    window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
