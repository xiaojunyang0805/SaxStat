"""
Main Application Window

The central window that orchestrates all GUI components and manages
application state.
"""

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QMenuBar, QStatusBar, QAction, QComboBox, QPushButton,
    QGroupBox, QLabel, QMessageBox, QFileDialog
)
from PyQt5.QtCore import pyqtSignal, QTimer, Qt
from pathlib import Path
from datetime import datetime
import pyqtgraph as pg

from ..experiments import get_registry, BaseExperiment, ExperimentState
from ..communication.serial_manager import SerialManager
from ..data.data_manager import DataManager
from ..plotting.plot_manager import PlotManager
from ..config.config_manager import ConfigManager
from .parameter_panel import ParameterPanel
from .analysis_panel import AnalysisPanel


class MainWindow(QMainWindow):
    """
    Main application window for SaxStat GUI.

    Manages the overall application layout and coordinates between
    parameter panels, plot displays, and experiment execution.
    """

    # Signals
    experiment_started = pyqtSignal()
    experiment_stopped = pyqtSignal()
    experiment_completed = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setWindowTitle("SaxStat v1.0 - Portable Potentiostat")
        self.setGeometry(100, 100, 1400, 900)

        # Core components
        self.config = ConfigManager()
        self.serial = SerialManager()
        self.data_manager = DataManager()
        self.plot_manager = None  # Created after plot widget
        self.current_experiment: BaseExperiment = None
        self.experiment_registry = get_registry()

        # Apply modern styling
        self._apply_stylesheet()

        # Setup statusbar first (before UI initialization)
        self._setup_statusbar()
        self._setup_ui()
        self._setup_menu()
        self._connect_signals()

        # Load initial configuration
        self._load_config()

    def _apply_stylesheet(self):
        """Apply clean blue and gray stylesheet with Arial font."""
        stylesheet = """
            * {
                font-family: Arial, sans-serif;
            }
            QMainWindow {
                background-color: #f5f5f5;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #64B5F6;
                border-radius: 6px;
                margin-top: 12px;
                padding-top: 10px;
                background-color: #E3F2FD;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
                color: #1976D2;
                font-family: Arial, sans-serif;
            }
            QPushButton {
                background-color: #64B5F6;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
                font-family: Arial, sans-serif;
                min-height: 24px;
            }
            QPushButton:hover {
                background-color: #42A5F5;
            }
            QPushButton:pressed {
                background-color: #1976D2;
            }
            QPushButton:disabled {
                background-color: #BDBDBD;
                color: #757575;
            }
            QComboBox {
                border: 1px solid #90CAF9;
                border-radius: 4px;
                padding: 4px 8px;
                background-color: white;
                color: #212121;
                font-family: Arial, sans-serif;
                min-height: 24px;
            }
            QComboBox:focus {
                border: 2px solid #64B5F6;
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            QLabel {
                color: #212121;
                font-size: 10pt;
                font-family: Arial, sans-serif;
            }
            QStatusBar {
                background-color: #E3F2FD;
                color: #1565C0;
                border-top: 2px solid #64B5F6;
                font-weight: bold;
                font-family: Arial, sans-serif;
                padding: 4px;
            }
            QMenuBar {
                background-color: #ffffff;
                border-bottom: 2px solid #E0E0E0;
                font-family: Arial, sans-serif;
            }
            QMenuBar::item {
                padding: 4px 12px;
                background-color: transparent;
                color: #212121;
            }
            QMenuBar::item:selected {
                background-color: #E3F2FD;
                color: #1565C0;
            }
            QDoubleSpinBox, QSpinBox {
                border: 1px solid #90CAF9;
                border-radius: 4px;
                padding: 4px;
                background-color: white;
                color: #212121;
                font-family: Arial, sans-serif;
                min-height: 20px;
            }
            QDoubleSpinBox:focus, QSpinBox:focus {
                border: 2px solid #64B5F6;
            }
        """
        self.setStyleSheet(stylesheet)

    def _setup_ui(self):
        """Initialize the main user interface layout."""
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)

        # Left panel - Controls and parameters
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_panel.setMaximumWidth(400)

        # Experiment selection
        exp_group = QGroupBox("Experiment Selection")
        exp_layout = QVBoxLayout()
        self.experiment_combo = QComboBox()
        self.experiment_combo.currentTextChanged.connect(self._on_experiment_changed)
        exp_layout.addWidget(self.experiment_combo)
        exp_group.setLayout(exp_layout)
        left_layout.addWidget(exp_group)

        # Serial port connection
        serial_group = QGroupBox("Serial Connection")
        serial_layout = QVBoxLayout()

        port_layout = QHBoxLayout()
        port_layout.addWidget(QLabel("Port:"))
        self.port_combo = QComboBox()
        self.port_combo.setEditable(True)
        port_layout.addWidget(self.port_combo)
        self.refresh_ports_btn = QPushButton("Refresh")
        self.refresh_ports_btn.clicked.connect(self._refresh_ports)
        port_layout.addWidget(self.refresh_ports_btn)
        serial_layout.addLayout(port_layout)

        self.connect_btn = QPushButton("Connect")
        self.connect_btn.clicked.connect(self._on_connect_clicked)
        serial_layout.addWidget(self.connect_btn)

        serial_group.setLayout(serial_layout)
        left_layout.addWidget(serial_group)

        # Parameter panel
        self.param_panel = ParameterPanel()
        left_layout.addWidget(self.param_panel)

        # Control buttons
        control_group = QGroupBox("Experiment Control")
        control_layout = QVBoxLayout()

        self.start_btn = QPushButton("Start Experiment")
        self.start_btn.clicked.connect(self._on_start_clicked)
        self.start_btn.setEnabled(False)
        control_layout.addWidget(self.start_btn)

        self.stop_btn = QPushButton("Stop Experiment")
        self.stop_btn.clicked.connect(self._on_stop_clicked)
        self.stop_btn.setEnabled(False)
        control_layout.addWidget(self.stop_btn)

        self.save_btn = QPushButton("Save Data")
        self.save_btn.clicked.connect(self._on_save_clicked)
        self.save_btn.setEnabled(False)
        control_layout.addWidget(self.save_btn)

        control_group.setLayout(control_layout)
        left_layout.addWidget(control_group)

        left_layout.addStretch()

        # Analysis panel (will be shown as dialog)
        self.analysis_panel = AnalysisPanel()
        self.analysis_panel.analysis_applied.connect(self._on_analysis_applied)

        # Analysis dialog (created once, reused)
        self.analysis_dialog = None

        # Right panel - Dual plots (Applied Voltage + Main Data)
        right_panel = QWidget()
        right_layout = QHBoxLayout(right_panel)

        # Applied voltage vs time plot (left)
        self.voltage_time_widget = pg.PlotWidget()
        self.voltage_time_widget.setBackground('w')
        self.voltage_time_widget.showGrid(x=True, y=True)
        # Axis styling will be set by PlotManager after initialization
        right_layout.addWidget(self.voltage_time_widget)

        # Main data plot (right - current vs voltage or time)
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setBackground('w')
        self.plot_widget.showGrid(x=True, y=True)
        # Axis styling will be set by PlotManager after initialization
        right_layout.addWidget(self.plot_widget)

        # Create plot managers
        self.plot_manager = PlotManager(self.plot_widget)
        self.voltage_plot_manager = PlotManager(self.voltage_time_widget)

        # Set labels for voltage plot after PlotManager initialization (override defaults)
        self.voltage_plot_manager.set_labels('Time (s)', 'Voltage (V)', 'Applied Voltage vs Time')

        # Analysis visualization items
        self.peak_markers = []
        self.baseline_curve = None

        # Add panels to main layout
        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 3)

        main_layout.addWidget(splitter)

        # Populate experiment list
        self._populate_experiments()

        # Refresh ports list
        self._refresh_ports()

    def _setup_menu(self):
        """Create the application menu bar."""
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("&File")

        save_data_action = QAction("&Save Data", self)
        save_data_action.setShortcut("Ctrl+S")
        save_data_action.triggered.connect(self._on_save_clicked)
        file_menu.addAction(save_data_action)

        save_plot_action = QAction("Save &Plot", self)
        save_plot_action.triggered.connect(self._on_save_plot_clicked)
        file_menu.addAction(save_plot_action)

        file_menu.addSeparator()

        exit_action = QAction("E&xit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Analysis menu
        analysis_menu = menubar.addMenu("&Analysis")

        analysis_tools_action = QAction("&Data Analysis Tools", self)
        analysis_tools_action.setShortcut("Ctrl+A")
        analysis_tools_action.triggered.connect(self._on_analysis_tools_clicked)
        analysis_menu.addAction(analysis_tools_action)

        # Settings menu
        settings_menu = menubar.addMenu("&Settings")

        preferences_action = QAction("&Preferences", self)
        preferences_action.setShortcut("Ctrl+P")
        preferences_action.triggered.connect(self._on_preferences_clicked)
        settings_menu.addAction(preferences_action)

        settings_menu.addSeparator()

        calibration_action = QAction("&Calibration", self)
        calibration_action.triggered.connect(self._on_calibration_clicked)
        settings_menu.addAction(calibration_action)

        # Help menu
        help_menu = menubar.addMenu("&Help")

        about_action = QAction("&About", self)
        about_action.triggered.connect(self._on_about_clicked)
        help_menu.addAction(about_action)

    def _setup_statusbar(self):
        """Create the status bar."""
        self.statusbar = QStatusBar()
        self.setStatusBar(self.statusbar)
        self.statusbar.showMessage("Ready")

    def _connect_signals(self):
        """Connect internal signals and slots."""
        # Serial manager signals
        self.serial.connected.connect(self._on_serial_connected)
        self.serial.disconnected.connect(self._on_serial_disconnected)
        self.serial.data_received.connect(self._on_serial_data)
        self.serial.error_occurred.connect(self._on_serial_error)

        # Parameter panel signals
        self.param_panel.parameters_configured.connect(self._on_parameters_configured)

    def _load_config(self):
        """Load configuration from config manager."""
        # Load last port
        last_port = self.config.get('serial.last_port', '')
        if last_port:
            index = self.port_combo.findText(last_port)
            if index >= 0:
                self.port_combo.setCurrentIndex(index)

        # Load window geometry
        ui_config = self.config.get_ui_config()
        self.resize(ui_config.get('window_width', 1400),
                   ui_config.get('window_height', 900))

    def _populate_experiments(self):
        """Populate experiment combo box."""
        exp_names = self.experiment_registry.get_all_names()
        self.experiment_combo.addItems(exp_names)

        # Select last used experiment
        last_exp = self.config.get('experiments.last_experiment', '')
        if last_exp:
            index = self.experiment_combo.findText(last_exp)
            if index >= 0:
                self.experiment_combo.setCurrentIndex(index)

    def _refresh_ports(self):
        """Refresh available serial ports."""
        import serial.tools.list_ports
        ports = [port.device for port in serial.tools.list_ports.comports()]

        self.port_combo.clear()
        self.port_combo.addItems(ports)

        # Restore last port if available
        last_port = self.config.get('serial.last_port', '')
        if last_port in ports:
            self.port_combo.setCurrentText(last_port)

    def _on_experiment_changed(self, exp_name: str):
        """Handle experiment selection change."""
        if not exp_name:
            return

        try:
            # Create experiment instance
            self.current_experiment = self.experiment_registry.create(exp_name)

            # Update parameter panel
            self.param_panel.set_experiment(self.current_experiment)

            # Connect experiment signals
            self.current_experiment.state_changed.connect(self._on_experiment_state_changed)
            self.current_experiment.data_received.connect(self._on_experiment_data)
            self.current_experiment.error_occurred.connect(self._on_experiment_error)

            # Update plot configuration
            plot_config = self.current_experiment.get_plot_config()
            self.plot_manager.set_labels(
                plot_config.get('x_label', 'X'),
                plot_config.get('y_label', 'Y'),
                plot_config.get('title', exp_name)
            )

            # Save to config
            self.config.set('experiments.last_experiment', exp_name)

            self.statusbar.showMessage(f"Selected experiment: {exp_name}")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load experiment:\n{str(e)}")

    def _on_connect_clicked(self):
        """Handle connect button click."""
        if self.serial.is_connected():
            # Disconnect
            self.serial.disconnect()
        else:
            # Connect
            port = self.port_combo.currentText()
            if port:
                if self.serial.connect(port):
                    self.config.set('serial.last_port', port)

    def _on_serial_connected(self):
        """Handle serial connection established."""
        self.connect_btn.setText("Disconnect")
        self.start_btn.setEnabled(self.current_experiment is not None)
        self.statusbar.showMessage(f"Connected to {self.port_combo.currentText()}")

    def _on_serial_disconnected(self):
        """Handle serial disconnection."""
        self.connect_btn.setText("Connect")
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(False)
        self.statusbar.showMessage("Disconnected")

    def _on_serial_data(self, data: str):
        """Handle incoming serial data."""
        if self.current_experiment:
            # Pass data to experiment for processing
            self.current_experiment.receive_data(data)

    def _on_serial_error(self, error: str):
        """Handle serial communication error."""
        self.statusbar.showMessage(f"Serial error: {error}")
        QMessageBox.warning(self, "Serial Error", error)

    def _on_parameters_configured(self, params: dict):
        """Handle parameters configured from parameter panel."""
        if self.current_experiment:
            try:
                # Configure experiment
                self.current_experiment.configure(params)
                self.statusbar.showMessage("Experiment configured successfully")

                # Enable start button if connected
                if self.serial.is_connected():
                    self.start_btn.setEnabled(True)

            except Exception as e:
                QMessageBox.warning(self, "Configuration Error", str(e))

    def _on_start_clicked(self):
        """Handle start experiment button click."""
        if not self.current_experiment or not self.serial.is_connected():
            return

        try:
            # Clear previous data
            self.data_manager.clear()
            self.plot_manager.clear()
            self.voltage_plot_manager.clear()
            self._clear_analysis_overlays()

            # Start experiment
            command = self.current_experiment.start()

            # Send command to hardware
            self.serial.send(command)

            # Update UI state
            self.start_btn.setEnabled(False)
            self.stop_btn.setEnabled(True)
            self.param_panel.set_enabled(False)
            self.experiment_combo.setEnabled(False)

            self.statusbar.showMessage("Experiment started")
            self.experiment_started.emit()

        except Exception as e:
            QMessageBox.critical(self, "Start Error", f"Failed to start experiment:\n{str(e)}")

    def _on_stop_clicked(self):
        """Handle stop experiment button click."""
        if self.current_experiment:
            try:
                # Stop experiment
                command = self.current_experiment.stop()

                # Send stop command
                if command:
                    self.serial.send(command)

                self._reset_ui_after_experiment()

                self.statusbar.showMessage("Experiment stopped")
                self.experiment_stopped.emit()

            except Exception as e:
                QMessageBox.warning(self, "Stop Error", str(e))

    def _on_experiment_state_changed(self, state: ExperimentState):
        """Handle experiment state change."""
        if state == ExperimentState.COMPLETED:
            self._reset_ui_after_experiment()
            self.save_btn.setEnabled(True)

            # Auto-save if enabled
            if self.config.get('autosave.enabled', True):
                self._auto_save_data()
            else:
                self.statusbar.showMessage("Experiment completed")

            self.experiment_completed.emit()

        elif state == ExperimentState.ERROR:
            self._reset_ui_after_experiment()
            self.statusbar.showMessage("Experiment error")

    def _on_experiment_data(self, data_point: dict):
        """Handle data point from experiment."""
        # Add to data manager
        self.data_manager.add_data_point(data_point)

        # Update applied voltage plot (always time vs voltage)
        if 'time' in data_point and 'voltage' in data_point:
            self.voltage_plot_manager.add_point(data_point['time'], data_point['voltage'])

        # Update main plot
        plot_config = self.current_experiment.get_plot_config()
        x_key = plot_config.get('x_data', 'time')
        y_key = plot_config.get('y_data', 'current')

        if x_key in data_point and y_key in data_point:
            self.plot_manager.add_point(data_point[x_key], data_point[y_key])

        # Update analysis panel with latest data
        if len(self.plot_manager.x_data) > 10:  # Wait for sufficient data
            import numpy as np
            self.analysis_panel.set_data(
                np.array(self.plot_manager.x_data),
                np.array(self.plot_manager.y_data)
            )

    def _on_experiment_error(self, error: str):
        """Handle experiment error."""
        QMessageBox.critical(self, "Experiment Error", error)
        self._reset_ui_after_experiment()

    def _reset_ui_after_experiment(self):
        """Reset UI state after experiment stops."""
        self.start_btn.setEnabled(self.serial.is_connected())
        self.stop_btn.setEnabled(False)
        self.param_panel.set_enabled(True)
        self.experiment_combo.setEnabled(True)

    def _on_save_clicked(self):
        """Handle save data button click."""
        if self.data_manager.data is None or self.data_manager.data.empty:
            QMessageBox.information(self, "No Data", "No data to save")
            return

        # Get save file path
        file_path, file_filter = QFileDialog.getSaveFileName(
            self,
            "Save Data",
            "",
            "CSV Files (*.csv);;Excel Files (*.xlsx);;JSON Files (*.json)"
        )

        if file_path:
            try:
                file_path = Path(file_path)

                # Save based on file extension
                if file_filter.startswith("CSV"):
                    self.data_manager.export_csv(file_path)
                elif file_filter.startswith("Excel"):
                    self.data_manager.export_excel(file_path)
                elif file_filter.startswith("JSON"):
                    self.data_manager.export_json(file_path)

                self.statusbar.showMessage(f"Data saved to {file_path}")

            except Exception as e:
                QMessageBox.critical(self, "Save Error", f"Failed to save data:\n{str(e)}")

    def _auto_save_data(self):
        """Automatically save experiment data based on configuration."""
        try:
            # Check if there's data to save
            if self.data_manager.data is None or self.data_manager.data.empty:
                self.statusbar.showMessage("Experiment completed (no data to save)")
                return

            # Get autosave configuration
            save_dir = Path(self.config.get('autosave.directory', '~/Documents/SaxStat/Data')).expanduser()
            filename_pattern = self.config.get('autosave.filename_pattern', '{experiment}_{timestamp}')
            formats = self.config.get('autosave.formats', ['csv'])
            create_dir = self.config.get('autosave.create_directory', True)

            # Create directory if needed
            if create_dir:
                save_dir.mkdir(parents=True, exist_ok=True)

            # Generate filename from pattern
            timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
            exp_name = self.current_experiment.get_name() if self.current_experiment else 'Unknown'

            filename_base = filename_pattern.format(
                experiment=exp_name,
                timestamp=timestamp,
                date=datetime.now().strftime('%Y-%m-%d'),
                time=datetime.now().strftime('%H-%M-%S')
            )

            # Save in all configured formats
            saved_files = []
            for fmt in formats:
                # Generate filepath with suffix protection
                filepath = self._get_unique_filepath(save_dir, filename_base, fmt)

                # Save based on format
                if fmt == 'csv':
                    self.data_manager.export_csv(filepath)
                elif fmt == 'json':
                    self.data_manager.export_json(filepath)
                elif fmt == 'excel':
                    self.data_manager.export_excel(filepath)

                saved_files.append(filepath.name)

            # Show success message
            if len(saved_files) == 1:
                self.statusbar.showMessage(f"Data auto-saved to: {saved_files[0]}")
            else:
                self.statusbar.showMessage(f"Data auto-saved to: {', '.join(saved_files)}")

        except Exception as e:
            # Show error message but don't block user
            error_msg = f"Autosave failed: {str(e)}"
            self.statusbar.showMessage(error_msg)
            print(f"ERROR: {error_msg}")  # Log to console for debugging

    def _get_unique_filepath(self, directory: Path, filename_base: str, extension: str) -> Path:
        """
        Generate unique filepath with suffix if file exists.

        Args:
            directory: Target directory
            filename_base: Base filename without extension
            extension: File extension (csv, json, excel)

        Returns:
            Unique filepath
        """
        filepath = directory / f"{filename_base}.{extension}"

        # If file doesn't exist, return as-is
        if not filepath.exists():
            return filepath

        # Add numeric suffix until we find unique name
        counter = 1
        while True:
            filepath = directory / f"{filename_base}_{counter:03d}.{extension}"
            if not filepath.exists():
                return filepath
            counter += 1

            # Safety check to prevent infinite loop
            if counter > 999:
                raise ValueError("Too many files with same base name (>999)")

    def _on_save_plot_clicked(self):
        """Handle save plot menu action."""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Plot",
            "",
            "PNG Files (*.png);;JPEG Files (*.jpg)"
        )

        if file_path:
            try:
                self.plot_manager.export_image(Path(file_path))
                self.statusbar.showMessage(f"Plot saved to {file_path}")

            except Exception as e:
                QMessageBox.critical(self, "Save Error", f"Failed to save plot:\n{str(e)}")

    def _on_analysis_tools_clicked(self):
        """Handle analysis tools menu action."""
        from PyQt5.QtWidgets import QDialog, QVBoxLayout

        # Create dialog only once
        if self.analysis_dialog is None:
            self.analysis_dialog = QDialog(self)
            self.analysis_dialog.setWindowTitle("Data Analysis Tools")
            self.analysis_dialog.setMinimumSize(450, 600)

            # Add analysis panel to dialog
            layout = QVBoxLayout(self.analysis_dialog)
            layout.addWidget(self.analysis_panel)

        # Show dialog (non-modal so it can stay open)
        self.analysis_dialog.show()
        self.analysis_dialog.raise_()
        self.analysis_dialog.activateWindow()

    def _on_preferences_clicked(self):
        """Handle preferences menu action."""
        from .preferences_dialog import PreferencesDialog

        dialog = PreferencesDialog(self.config, self)
        dialog.exec_()

    def _on_calibration_clicked(self):
        """Handle calibration menu action."""
        # TODO: Implement calibration dialog
        QMessageBox.information(self, "Calibration", "Calibration feature coming soon")

    def _on_about_clicked(self):
        """Handle about menu action."""
        about_text = """
        <h2>SaxStat v1.0</h2>
        <p>Portable potentiostat for electrochemical testing</p>
        <p><b>Hardware:</b> ESP32-based with AD5761 DAC and ADS1115 ADC</p>
        <p><b>Voltage Range:</b> -1.5V to +1.5V</p>
        <p><b>Experiments:</b> CV, LSV, CA, SWV, DPV (more coming)</p>
        <br>
        <p>For more information, visit the project repository.</p>
        """
        QMessageBox.about(self, "About SaxStat", about_text)

    def _on_analysis_applied(self, analysis_data: dict):
        """Handle analysis result from analysis panel."""
        analysis_type = analysis_data.get('type')

        # Clear previous analysis overlays
        self._clear_analysis_overlays()

        if analysis_type == 'peak_detection':
            # Visualize detected peaks
            self._visualize_peaks(analysis_data)

        elif analysis_type == 'baseline_correction':
            # Visualize baseline
            self._visualize_baseline(analysis_data)

        elif analysis_type == 'smoothing':
            # Update plot with smoothed data
            self._visualize_smoothed(analysis_data)

        # Integration doesn't need visualization (results shown in text)

    def _clear_analysis_overlays(self):
        """Clear all analysis visualization overlays."""
        # Clear peak markers
        for marker in self.peak_markers:
            self.plot_widget.removeItem(marker)
        self.peak_markers.clear()

        # Clear baseline curve
        if self.baseline_curve is not None:
            self.plot_widget.removeItem(self.baseline_curve)
            self.baseline_curve = None

    def _visualize_peaks(self, analysis_data: dict):
        """Visualize detected peaks on plot."""
        import numpy as np

        results = analysis_data.get('results', {})
        x_data = np.array(self.plot_manager.x_data)
        y_data = np.array(self.plot_manager.y_data)

        # Anodic peaks (red markers)
        anodic_peaks = results.get('anodic_peaks', [])
        for peak_idx in anodic_peaks:
            if peak_idx < len(x_data):
                scatter = pg.ScatterPlotItem(
                    [x_data[peak_idx]],
                    [y_data[peak_idx]],
                    symbol='o',
                    size=12,
                    pen=pg.mkPen('r', width=2),
                    brush=pg.mkBrush(255, 0, 0, 100)
                )
                self.plot_widget.addItem(scatter)
                self.peak_markers.append(scatter)

        # Cathodic peaks (blue markers)
        cathodic_peaks = results.get('cathodic_peaks', [])
        for peak_idx in cathodic_peaks:
            if peak_idx < len(x_data):
                scatter = pg.ScatterPlotItem(
                    [x_data[peak_idx]],
                    [y_data[peak_idx]],
                    symbol='o',
                    size=12,
                    pen=pg.mkPen('b', width=2),
                    brush=pg.mkBrush(0, 0, 255, 100)
                )
                self.plot_widget.addItem(scatter)
                self.peak_markers.append(scatter)

    def _visualize_baseline(self, analysis_data: dict):
        """Visualize baseline correction on plot."""
        import numpy as np

        baseline = analysis_data.get('baseline')
        x_data = np.array(self.plot_manager.x_data)

        if baseline is not None and len(baseline) == len(x_data):
            # Add baseline curve (orange dashed line)
            self.baseline_curve = self.plot_widget.plot(
                x_data,
                baseline,
                pen=pg.mkPen(color='orange', width=2, style=Qt.DashLine)
            )

    def _visualize_smoothed(self, analysis_data: dict):
        """Visualize smoothed data on plot."""
        import numpy as np

        smoothed_data = analysis_data.get('smoothed_data')
        x_data = np.array(self.plot_manager.x_data)

        if smoothed_data is not None and len(smoothed_data) == len(x_data):
            # Add smoothed curve (green line)
            smoothed_curve = self.plot_widget.plot(
                x_data,
                smoothed_data,
                pen=pg.mkPen(color='green', width=2)
            )
            self.peak_markers.append(smoothed_curve)  # Store for clearing

    def closeEvent(self, event):
        """Handle window close event."""
        # Check if experiment is running
        if self.current_experiment and self.current_experiment.state == ExperimentState.RUNNING:
            reply = QMessageBox.question(
                self,
                "Experiment Running",
                "An experiment is currently running. Are you sure you want to exit?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )

            if reply == QMessageBox.No:
                event.ignore()
                return

            # Stop experiment
            try:
                self.current_experiment.stop()
            except:
                pass

        # Save window geometry
        self.config.set_window_geometry(self.width(), self.height())

        # Disconnect serial
        if self.serial.is_connected():
            self.serial.disconnect()

        event.accept()
