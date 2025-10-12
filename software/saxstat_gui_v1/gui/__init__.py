"""
GUI Module - User interface components.

This module contains all PyQt5 GUI components including the main window,
parameter panels, plot displays, and status indicators.
"""

from .main_window import MainWindow
from .parameter_panel import ParameterPanel
from .preferences_dialog import PreferencesDialog
from .overlay_dialog import OverlayDialog
from .calibration_dialog import CalibrationDialog

__all__ = ['MainWindow', 'ParameterPanel', 'PreferencesDialog', 'OverlayDialog', 'CalibrationDialog']
