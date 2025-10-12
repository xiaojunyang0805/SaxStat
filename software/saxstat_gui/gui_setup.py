import threading
from PyQt5.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QLineEdit, QComboBox, QMessageBox, QStatusBar, QCheckBox
from PyQt5.QtCore import QTimer
import serial.tools.list_ports
from serial_comm import refresh_com_ports, toggle_connection, set_mode
from data_processing import calibrate_offset, start_acquisition, stop_acquisition, save_data
from plotting import update_plots, update_graph_sizes

def list_available_ports():
    ports = [port.device for port in serial.tools.list_ports.comports()]
    print("Available ports:", ports)
    return ports

class CyclicVoltammetryGUI(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Cyclic Voltammetry GUI")
        self.setGeometry(100, 100, 1400, 1000)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QHBoxLayout()
        self.central_widget.setLayout(self.main_layout)

        # Left Panel
        self.left_panel = QWidget()
        self.left_layout = QVBoxLayout()
        self.left_panel.setLayout(self.left_layout)
        self.left_panel.setFixedWidth(300)
        self.main_layout.addWidget(self.left_panel)

        self.start_label = QLabel("Start Voltage (V):")
        self.start_edit = QLineEdit("-0.5")
        self.start_edit.setToolTip("Enter voltage between -1.5 and 1.5 V")
        self.left_layout.addWidget(self.start_label)
        self.left_layout.addWidget(self.start_edit)

        self.end_label = QLabel("End Voltage (V):")
        self.end_edit = QLineEdit("0.5")
        self.end_edit.setToolTip("Enter voltage between -1.5 and 1.5 V")
        self.left_layout.addWidget(self.end_label)
        self.left_layout.addWidget(self.end_edit)

        self.scan_label = QLabel("Scan Rate (V/s):")
        self.scan_edit = QLineEdit("0.02")
        self.scan_edit.setToolTip("Enter scan rate between 0.01 and 0.2 V/s")
        self.left_layout.addWidget(self.scan_label)
        self.left_layout.addWidget(self.scan_edit)

        self.cycle_label = QLabel("Cycles:")
        self.cycle_edit = QLineEdit("2")
        self.cycle_edit.setToolTip("Enter number of cycles (>= 1)")
        self.left_layout.addWidget(self.cycle_label)
        self.left_layout.addWidget(self.cycle_edit)

        self.offset_current_label = QLabel("Offset Current (µA):")
        self.offset_current_edit = QLineEdit("-5")
        self.offset_current_edit.setToolTip("Enter offset current in µA")
        self.left_layout.addWidget(self.offset_current_label)
        self.left_layout.addWidget(self.offset_current_edit)

        self.port_label = QLabel("COM Port:")
        self.port_combo = QComboBox()
        self.port_combo.addItems(list_available_ports())
        self.left_layout.addWidget(self.port_label)
        self.left_layout.addWidget(self.port_combo)

        self.refresh_button = QPushButton("Refresh COM Ports")
        self.refresh_button.clicked.connect(lambda: refresh_com_ports(self))
        self.left_layout.addWidget(self.refresh_button)

        self.connect_button = QPushButton("Connect")
        self.connect_button.clicked.connect(lambda: toggle_connection(self))
        self.connect_button.setEnabled(bool(self.port_combo.count()))
        self.left_layout.addWidget(self.connect_button)

        self.calibrate_button = QPushButton("Calibrate Offset")
        self.calibrate_button.clicked.connect(lambda: calibrate_offset(self))
        self.left_layout.addWidget(self.calibrate_button)

        # Add Current Range Toggles
        self.mode_check_100nA = QCheckBox("Switch to ±100 nA (1MΩ)")
        self.mode_check_100nA.stateChanged.connect(lambda: set_mode(self))
        self.left_layout.addWidget(self.mode_check_100nA)

        self.mode_check_10nA = QCheckBox("Switch to ±10 nA (1MΩ)")
        self.mode_check_10nA.stateChanged.connect(lambda: set_mode(self))
        self.left_layout.addWidget(self.mode_check_10nA)

        self.left_layout.addStretch()

        self.start_button = QPushButton("Start CV")
        self.start_button.clicked.connect(lambda: start_acquisition(self))
        self.start_button.setEnabled(False)
        self.left_layout.addWidget(self.start_button)

        self.stop_button = QPushButton("Stop CV")
        self.stop_button.clicked.connect(lambda: stop_acquisition(self))
        self.stop_button.setEnabled(False)
        self.left_layout.addWidget(self.stop_button)

        self.save_button = QPushButton("Save Data")
        self.save_button.clicked.connect(lambda: save_data(self))
        self.save_button.setEnabled(False)
        self.left_layout.addWidget(self.save_button)

        # Status Bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Disconnected")

        # Right Panel (Graphs)
        self.right_panel = QWidget()
        self.right_layout = QHBoxLayout()
        self.right_panel.setLayout(self.right_layout)
        self.main_layout.addWidget(self.right_panel)

        self.voltage_time_widget = None  # To be set by plotting module
        self.plot_widget = None  # To be set by plotting module
        self.voltage_time_data = None  # To be set by plotting module
        self.plot_data = None  # To be set by plotting module

        # Variables
        self.serial_port = None  # To be set by serial_comm module
        self.applied_voltage_buffer = []
        self.current_buffer = []
        self.time_buffer = []
        self.is_running = False
        self.timer = QTimer()
        self.timer.timeout.connect(lambda: update_plots(self))
        self.lock = threading.Lock()
        self.start_time = None
        self.is_connected = False
        self.resistance = 10000  # Default to 10 kΩ
        self.v_ref = 1.0
        self.offset_current = 0
        self.read_thread = None
        self.cv_params = None
        self.stop_event = threading.Event()
        self.last_graph_size = 0
        self.current_mode = 0  # 0: ±500 µA (10 kΩ), 1: ±100 nA (1 MΩ), 2: ±10 nA (1 MΩ)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        current_size = min(self.right_panel.width() // 2, self.right_panel.height())
        if abs(current_size - self.last_graph_size) > 10:
            from plotting import update_graph_sizes
            update_graph_sizes(self)
            self.last_graph_size = current_size

    def update_button_states(self):
        self.start_button.setEnabled(self.is_connected and not self.is_running)
        self.stop_button.setEnabled(self.is_running)
        self.save_button.setEnabled(bool(self.applied_voltage_buffer))
        self.connect_button.setText("Disconnect" if self.is_connected else "Connect")
        self.connect_button.setEnabled(bool(self.port_combo.count()))

    def debug_timer(self):
        print("Timer triggered, calling update_plots")