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
import pyqtgraph as pg

from ..experiments import get_registry, BaseExperiment, ExperimentState
from ..communication.serial_manager import SerialManager
from ..data.data_manager import DataManager
from ..plotting.plot_manager import PlotManager
from ..config.config_manager import ConfigManager
from .parameter_panel import ParameterPanel


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
        self.setWindowTitle("SaxStat v1.0")
        self.setGeometry(100, 100, 1400, 900)

        # Core components
        self.config = ConfigManager()
        self.serial = SerialManager()
        self.data_manager = DataManager()
        self.plot_manager = None  # Created after plot widget
        self.current_experiment: BaseExperiment = None
        self.experiment_registry = get_registry()

        self._setup_ui()
        self._setup_menu()
        self._setup_statusbar()
        self._connect_signals()

        # Load initial configuration
        self._load_config()

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

        # Right panel - Plot
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)

        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setBackground('w')
        self.plot_widget.showGrid(x=True, y=True)
        right_layout.addWidget(self.plot_widget)

        # Create plot manager
        self.plot_manager = PlotManager(self.plot_widget)

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

        # Settings menu
        settings_menu = menubar.addMenu("&Settings")

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
            self.statusbar.showMessage("Experiment completed")
            self.experiment_completed.emit()

        elif state == ExperimentState.ERROR:
            self._reset_ui_after_experiment()
            self.statusbar.showMessage("Experiment error")

    def _on_experiment_data(self, data_point: dict):
        """Handle data point from experiment."""
        # Add to data manager
        self.data_manager.add_data_point(data_point)

        # Update plot
        plot_config = self.current_experiment.get_plot_config()
        x_key = plot_config.get('x_data', 'time')
        y_key = plot_config.get('y_data', 'current')

        if x_key in data_point and y_key in data_point:
            self.plot_manager.add_point(data_point[x_key], data_point[y_key])

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
