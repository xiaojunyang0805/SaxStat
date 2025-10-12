"""
Plot Manager

Manages real-time plotting with pyqtgraph for high performance.
"""

import pyqtgraph as pg
from pyqtgraph import PlotWidget
from typing import List, Tuple, Optional
import numpy as np


class PlotManager:
    """
    Manages real-time plotting for experiments.

    Features:
    - High-performance updates with pyqtgraph
    - Multiple plot types (line, scatter)
    - Auto-scaling
    - Plot customization
    - Export to image
    """

    def __init__(self, plot_widget: PlotWidget):
        """
        Initialize plot manager.

        Args:
            plot_widget: PyQtGraph PlotWidget instance
        """
        self.widget = plot_widget
        self.plot_item = self.widget.getPlotItem()

        # Data storage
        self.x_data: List[float] = []
        self.y_data: List[float] = []

        # Plot curves
        self.curve: Optional[pg.PlotDataItem] = None

        # Configure default appearance
        self._setup_plot()

    def _setup_plot(self):
        """Configure plot appearance with Arial font."""
        from PyQt5.QtGui import QFont

        self.plot_item.showGrid(x=True, y=True, alpha=0.3)

        # Set default labels with Arial font
        label_style = {'color': '#212121', 'font-size': '12pt', 'font-family': 'Arial'}
        self.plot_item.setLabel('bottom', 'X Axis', **label_style)
        self.plot_item.setLabel('left', 'Y Axis', **label_style)

        # Set background color
        self.widget.setBackground('w')

        # Set tick font and colors
        tick_font = QFont("Arial", 10)
        self.widget.getAxis('left').setTextPen('#212121')
        self.widget.getAxis('bottom').setTextPen('#212121')
        self.widget.getAxis('left').setPen('#424242')
        self.widget.getAxis('bottom').setPen('#424242')
        self.widget.getAxis('left').setStyle(tickFont=tick_font)
        self.widget.getAxis('bottom').setStyle(tickFont=tick_font)

    # Plot configuration

    def set_labels(self, x_label: str, y_label: str, title: str = ''):
        """
        Set plot labels with darker text and Arial font.

        Args:
            x_label: X-axis label with unit (e.g., 'Time (s)')
            y_label: Y-axis label with unit (e.g., 'Current (µA)')
            title: Plot title
        """
        from PyQt5.QtGui import QFont

        # Create font for tick numbers
        tick_font = QFont("Arial", 10)

        # Set labels with CSS-style formatting for Arial font
        label_style = {'color': '#212121', 'font-size': '12pt', 'font-family': 'Arial'}

        self.plot_item.setLabel('bottom', x_label, **label_style)
        self.plot_item.setLabel('left', y_label, **label_style)

        if title:
            # Set title with HTML formatting for Arial font
            title_html = f'<span style="color: #212121; font-size: 13pt; font-family: Arial; font-weight: bold;">{title}</span>'
            self.plot_item.setTitle(title_html)

        # Update axis text colors and tick font
        self.widget.getAxis('left').setTextPen('#212121')
        self.widget.getAxis('bottom').setTextPen('#212121')
        self.widget.getAxis('left').setPen('#424242')
        self.widget.getAxis('bottom').setPen('#424242')
        self.widget.getAxis('left').setStyle(tickFont=tick_font)
        self.widget.getAxis('bottom').setStyle(tickFont=tick_font)

    def set_axis_ranges(self, x_range: Tuple[float, float],
                       y_range: Tuple[float, float]):
        """
        Set fixed axis ranges.

        Args:
            x_range: (min, max) for x-axis
            y_range: (min, max) for y-axis
        """
        self.plot_item.setXRange(*x_range, padding=0)
        self.plot_item.setYRange(*y_range, padding=0)

    def enable_auto_range(self, enable: bool = True):
        """
        Enable or disable auto-ranging.

        Args:
            enable: True to enable auto-ranging
        """
        self.plot_item.enableAutoRange(enable=enable)

    # Data management

    def clear(self):
        """Clear all plot data."""
        self.x_data.clear()
        self.y_data.clear()

        if self.curve is not None:
            self.plot_item.removeItem(self.curve)
            self.curve = None

    def add_point(self, x: float, y: float):
        """
        Add a single data point.

        Args:
            x: X coordinate
            y: Y coordinate
        """
        self.x_data.append(x)
        self.y_data.append(y)
        self.update()

    def add_points(self, x_points: List[float], y_points: List[float]):
        """
        Add multiple data points.

        Args:
            x_points: List of X coordinates
            y_points: List of Y coordinates
        """
        self.x_data.extend(x_points)
        self.y_data.extend(y_points)
        self.update()

    def set_data(self, x_data: List[float], y_data: List[float]):
        """
        Replace all data with new dataset.

        Args:
            x_data: New X data
            y_data: New Y data
        """
        self.x_data = list(x_data)
        self.y_data = list(y_data)
        self.update()

    # Plotting

    def update(self):
        """Update the plot with current data."""
        if not self.x_data or not self.y_data:
            return

        if self.curve is None:
            # Create curve on first update
            self.curve = self.plot_item.plot(
                self.x_data,
                self.y_data,
                pen=pg.mkPen(color='b', width=2)
            )
        else:
            # Update existing curve
            self.curve.setData(self.x_data, self.y_data)

    def set_line_color(self, color: str, width: int = 2):
        """
        Set line color and width.

        Args:
            color: Color ('r', 'g', 'b', or hex like '#FF0000')
            width: Line width in pixels
        """
        if self.curve is not None:
            self.curve.setPen(pg.mkPen(color=color, width=width))

    # Export

    def export_image(self, filepath: str):
        """
        Export plot to image file.

        Args:
            filepath: Output file path (.png, .jpg, .svg)
        """
        exporter = pg.exporters.ImageExporter(self.plot_item)
        exporter.export(filepath)

    # Utility

    def downsample_data(self, max_points: int = 1000):
        """
        Downsample data for performance if needed.

        Args:
            max_points: Maximum number of points to keep
        """
        if len(self.x_data) > max_points:
            step = len(self.x_data) // max_points
            self.x_data = self.x_data[::step]
            self.y_data = self.y_data[::step]
            self.update()
