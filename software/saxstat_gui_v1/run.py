#!/usr/bin/env python3
"""
SaxStat GUI v1 - Launch Script

Quick launcher for testing and running the application.
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from PyQt5.QtWidgets import QApplication
from saxstat_gui_v1.gui import MainWindow


def main():
    """Launch the SaxStat GUI application."""
    app = QApplication(sys.argv)
    app.setApplicationName("SaxStat")
    app.setOrganizationName("SaxStat")
    app.setApplicationVersion("1.0.0-dev")

    # Create and show main window
    window = MainWindow()
    window.show()

    # Start event loop
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
