import sys
import serial
import serial.tools.list_ports
import threading
import time
import numpy as np
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QPushButton, QWidget,
    QFileDialog, QLabel, QLineEdit, QComboBox, QMessageBox, QStatusBar
)
from PyQt5.QtCore import QTimer
from pyqtgraph import PlotWidget

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
        self.left_panel.setFixedWidth(300)  # Adjusted to 300 as specified
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
        self.offset_current_edit = QLineEdit("-28")
        self.offset_current_edit.setToolTip("Enter offset current in µA")
        self.left_layout.addWidget(self.offset_current_label)
        self.left_layout.addWidget(self.offset_current_edit)

        self.port_label = QLabel("COM Port:")
        self.port_combo = QComboBox()
        self.port_combo.addItems(list_available_ports())
        self.left_layout.addWidget(self.port_label)
        self.left_layout.addWidget(self.port_combo)

        self.refresh_button = QPushButton("Refresh COM Ports")
        self.refresh_button.clicked.connect(self.refresh_com_ports)
        self.left_layout.addWidget(self.refresh_button)

        self.connect_button = QPushButton("Connect")
        self.connect_button.clicked.connect(self.toggle_connection)
        self.connect_button.setEnabled(bool(self.port_combo.count()))
        self.left_layout.addWidget(self.connect_button)

        self.calibrate_button = QPushButton("Calibrate Offset")
        self.calibrate_button.clicked.connect(self.calibrate_offset)
        self.left_layout.addWidget(self.calibrate_button)

        self.left_layout.addStretch()

        self.start_button = QPushButton("Start CV")
        self.start_button.clicked.connect(self.start_acquisition)
        self.start_button.setEnabled(False)
        self.left_layout.addWidget(self.start_button)

        self.stop_button = QPushButton("Stop CV")
        self.stop_button.clicked.connect(self.stop_acquisition)
        self.stop_button.setEnabled(False)
        self.left_layout.addWidget(self.stop_button)

        self.save_button = QPushButton("Save Data")
        self.save_button.clicked.connect(self.save_data)
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

        self.voltage_time_widget = PlotWidget()
        self.right_layout.addWidget(self.voltage_time_widget)
        self.voltage_time_widget.setLabel('left', 'Applied Voltage (V)')
        self.voltage_time_widget.setLabel('bottom', 'Time (s)')
        self.voltage_time_widget.showGrid(x=True, y=True)
        self.voltage_time_widget.setTitle("Applied Voltage vs. Time")
        self.voltage_time_widget.setBackground('w')
        self.voltage_time_data = self.voltage_time_widget.plot(pen="r")

        self.plot_widget = PlotWidget()
        self.right_layout.addWidget(self.plot_widget)
        self.plot_widget.setLabel('left', 'Current (µA)')
        self.plot_widget.setLabel('bottom', 'Applied Voltage (V)')
        self.plot_widget.showGrid(x=True, y=True)
        self.plot_widget.setTitle("Cyclic Voltammogram")
        self.plot_widget.setBackground('w')
        self.plot_data = self.plot_widget.plot(pen="b")  # Fixed to correct widget

        self.update_graph_sizes()

        # Variables
        self.serial_port = serial.Serial()
        self.serial_port.timeout = 0.1  # Reduced to 0.1s for faster reads
        self.applied_voltage_buffer = []
        self.current_buffer = []
        self.time_buffer = []
        self.is_running = False
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_plots)
        self.lock = threading.Lock()
        self.start_time = None
        self.is_connected = False
        self.resistance = 10000  # Fixed TIA resistance (10KΩ)
        self.v_ref = 1.0  # Fixed reference voltage (V)
        self.offset_current = 0  # Calibrated offset current (µA)
        self.read_thread = None
        self.cv_params = None
        self.stop_event = threading.Event()
        self.last_graph_size = 0

    def resizeEvent(self, event):
        super().resizeEvent(event)
        current_size = min(self.right_panel.width() // 2, self.right_panel.height())
        if abs(current_size - self.last_graph_size) > 10:
            self.update_graph_sizes()
            self.last_graph_size = current_size

    def update_graph_sizes(self):
        right_width = self.right_panel.width()
        right_height = self.right_panel.height()
        square_size = min(right_width // 2, right_height, 700)  # Capped at 700 as specified
        square_size = max(500, square_size)  # Minimum 500 pixels
        self.voltage_time_widget.setMinimumSize(square_size, square_size)
        self.voltage_time_widget.setMaximumSize(square_size, square_size)
        self.plot_widget.setMinimumSize(square_size, square_size)
        self.plot_widget.setMaximumSize(square_size, square_size)
        self.right_layout.setStretchFactor(self.voltage_time_widget, 1)
        self.right_layout.setStretchFactor(self.plot_widget, 1)

    def update_button_states(self):
        self.start_button.setEnabled(self.is_connected and not self.is_running)
        self.stop_button.setEnabled(self.is_running)
        self.save_button.setEnabled(bool(self.applied_voltage_buffer))
        self.connect_button.setText("Disconnect" if self.is_connected else "Connect")
        self.connect_button.setEnabled(bool(self.port_combo.count()))

    def configure_serial(self, baud_rate=115200):
        port = self.port_combo.currentText()
        with self.lock:
            if self.serial_port.is_open:
                self.serial_port.close()
            self.serial_port.port = port
            self.serial_port.baudrate = baud_rate
            self.serial_port.timeout = 0.1  # Reduced to 0.1s
            try:
                self.serial_port.open()
                self.serial_port.reset_input_buffer()
                print(f"Connected to {port}")
                self.is_connected = True
                self.status_bar.showMessage(f"Connected to {port}")
            except Exception as e:
                print(f"Failed to open serial port: {e}")
                QMessageBox.warning(self, "Connection Error", f"Could not connect to {port}: {e}")
                self.is_connected = False
        self.update_button_states()

    def disconnect_serial(self):
        with self.lock:
            if self.serial_port.is_open:
                self.serial_port.close()
                print("Serial port closed.")
        self.is_connected = False
        self.status_bar.showMessage("Disconnected")
        self.timer.stop()
        self.update_button_states()

    def toggle_connection(self):
        if self.is_connected:
            self.disconnect_serial()
        else:
            if not self.port_combo.currentText():
                QMessageBox.warning(self, "No Port Selected", "Please select a COM port.")
                return
            self.configure_serial()

    def refresh_com_ports(self):
        self.port_combo.clear()
        ports = list_available_ports()
        self.port_combo.addItems(ports)
        self.update_button_states()
        print("COM ports refreshed.")

    def get_cv_parameters(self):
        try:
            start_v = float(self.start_edit.text())
            end_v = float(self.end_edit.text())
            scan_rate = float(self.scan_edit.text())
            cycles = int(self.cycle_edit.text())
            if start_v < -1.5 or end_v > 1.5 or scan_rate < 0.01 or scan_rate > 0.2 or cycles < 1:
                raise ValueError("Invalid parameter range: Start/End Voltage (-1.5 to 1.5 V), Scan Rate (0.01 to 0.2 V/s), Cycles (>= 1).")
            return start_v, end_v, scan_rate, cycles
        except Exception as e:
            print(f"Parameter error: {e}")
            QMessageBox.warning(self, "Invalid Parameters", str(e))
            return None

    def calibrate_offset(self):
        if not self.is_connected:
            QMessageBox.warning(self, "Not Connected", "Please connect to a COM port first.")
            return
        with self.lock:
            try:
                if not self.serial_port.is_open:
                    QMessageBox.warning(self, "Disconnected", "Serial port is not open.")
                    return
                self.serial_port.write(b"CALIBRATE\n")
                start_time = time.time()
                currents = []
                while time.time() - start_time < 1.0:
                    if self.serial_port.in_waiting:
                        line = self.serial_port.readline().decode('utf-8', errors='ignore').strip()
                        try:
                            adc_value = float(line)
                            if 0 <= adc_value <= 4095:
                                v_ref = self.v_ref
                                resistance = self.resistance
                                v_out = (adc_value / 4095) * 3.3
                                current = (1e6 * (2 * v_ref - v_out) / resistance)
                                currents.append(current)
                        except ValueError:
                            continue
                if currents:
                    self.offset_current = np.mean(currents)
                    self.offset_current_edit.setText(f"{self.offset_current:.2f}")  # Update GUI field
                    print(f"Calibrated offset current: {self.offset_current} µA")
                    QMessageBox.information(self, "Calibration", f"Offset current set to {self.offset_current:.2f} µA")
                else:
                    print("No valid data for calibration.")
                    QMessageBox.warning(self, "Calibration Failed", "No valid data received for calibration.")
            except Exception as e:
                print(f"Calibration error: {e}")
                QMessageBox.warning(self, "Calibration Error", f"Failed to calibrate: {e}")

    def calculate_voltage_ramp(self, elapsed_time):
        if not hasattr(self, 'cv_params') or not self.cv_params:
            return 0.0
        start_v, end_v, scan_rate, cycles = self.cv_params
        voltage_range = abs(end_v - start_v)
        half_cycle_time = voltage_range / scan_rate
        full_cycle_time = 2 * half_cycle_time
        total_time = cycles * full_cycle_time

        if elapsed_time > total_time:
            elapsed_time = total_time

        cycle_time = elapsed_time % full_cycle_time
        if cycle_time < half_cycle_time:
            fraction = cycle_time / half_cycle_time
            return start_v + fraction * (end_v - start_v)
        else:
            fraction = (cycle_time - half_cycle_time) / half_cycle_time
            return end_v - fraction * (end_v - start_v)

    def start_acquisition(self):
        if not self.is_connected:
            QMessageBox.warning(self, "Not Connected", "Please connect to a COM port first.")
            return

        params = self.get_cv_parameters()
        if not params:
            return

        if self.applied_voltage_buffer:
            if self.is_running or (self.read_thread and self.read_thread.is_alive()):
                self.stop_acquisition()
                while self.read_thread and self.read_thread.is_alive():
                    time.sleep(0.1)
                    print("Waiting for read thread to stop...")
            reply = QMessageBox.question(
                self, "Discard Data?", "There is existing data. Discard the data?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                with self.lock:
                    self.applied_voltage_buffer.clear()
                    self.current_buffer.clear()
                    self.time_buffer.clear()
                    print("Buffers cleared successfully.")
                    self.plot_data.clear()
                    self.voltage_time_data.clear()
            else:
                return

        self.cv_params = params
        start_v, end_v, scan_rate, cycles = params
        if self.is_running:
            QMessageBox.warning(self, "Already Running", "An acquisition is already in progress. Stop it first.")
            return

        command = f"START:{start_v}:{end_v}:{scan_rate}:{cycles}\n"
        max_retries = 3
        retry_count = 0
        success = False

        while retry_count < max_retries and not success:
            with self.lock:
                try:
                    if not self.serial_port.is_open:
                        QMessageBox.warning(self, "Disconnected", "Serial port is not open.")
                        return
                    self.serial_port.reset_input_buffer()
                    self.serial_port.write(command.encode())
                    print(f"Sent: {command.strip()}")
                    start_time = time.time()
                    while time.time() - start_time < 2.0:
                        if self.serial_port.in_waiting:
                            line = self.serial_port.readline().decode('utf-8', errors='ignore').strip()
                            if not line:
                                print("Received empty response, continuing to read...")
                                continue
                            print(f"Received: {line}")
                            if any(keyword in line for keyword in ["minValue (DAC):", "Half-cycle time (ms):", "Steps per half-cycle:", "Delay per step (ms):", "Applied Parameters"]):
                                print(f"Confirmed: {line}")
                                success = True
                                break
                            elif "Initial ADC voltage" in line:
                                print(f"Ignoring setup message: {line}")
                                continue
                            elif "Error" in line:
                                print(f"Firmware error: {line}")
                                QMessageBox.warning(self, "Firmware Error", f"Device reported: {line}")
                                return
                            else:
                                print(f"Unexpected response: {line}")
                        time.sleep(0.01)
                except Exception as e:
                    print(f"Error sending START command: {e}")
                    QMessageBox.warning(self, "Command Error", f"Failed to start acquisition: {e}")
                    return
            if not success:
                retry_count += 1
                print(f"Retry {retry_count}/{max_retries} for START command")
                time.sleep(0.5)

        if not success:
            print("No valid confirmation received from firmware after retries.")
            QMessageBox.warning(self, "No Response", "No valid confirmation from device. Check firmware and connection.")
            return

        self.is_running = True
        self.start_time = time.time()
        self.stop_event.clear()
        self.timer.start(50)  # Reduced to 50ms for smoother updates
        self.status_bar.showMessage("Acquisition running")
        self.read_thread = threading.Thread(target=self.read_serial_data, daemon=True)
        self.read_thread.start()
        self.update_button_states()

    def stop_acquisition(self):
        if self.is_running or (self.read_thread and self.read_thread.is_alive()):
            self.is_running = False
            self.stop_event.set()
            self.timer.stop()
            with self.lock:
                try:
                    if self.serial_port.is_open:
                        self.serial_port.write(b"STOP\n")
                        print("Sent STOP command")
                        start_time = time.time()
                        while time.time() - start_time < 1:
                            if self.serial_port.in_waiting:
                                line = self.serial_port.readline().decode('utf-8', errors='ignore').strip()
                                if line == "CV stopped.":
                                    print("Received CV stopped confirmation")
                                    break
                except Exception as e:
                    print(f"Error sending STOP command: {e}")
            if self.read_thread and self.read_thread.is_alive():
                self.read_thread.join(timeout=1.0)
                print(f"Read thread terminated: {not self.read_thread.is_alive()}")
                self.read_thread = None
        self.status_bar.showMessage("Acquisition stopped")
        self.update_button_states()

    def read_serial_data(self):
        initial_skip = 50
        points_skipped = 0
        window_size = 10
        current_window = []

        while self.is_running and self.serial_port.is_open and not self.stop_event.is_set():
            with self.lock:
                try:
                    if not self.serial_port.is_open:
                        print("Serial port disconnected during acquisition.")
                        self.is_running = False
                        break
                    line = self.serial_port.readline().decode('utf-8', errors='ignore').strip()
                    if not line:
                        continue
                    if line == "CV complete.":
                        self.is_running = False
                        break
                    try:
                        adc_value = float(line)
                        if 0 <= adc_value <=32767: # Valid range for ADS1115 single-ended output (0 to 32767)
                            elapsed_time = time.time() - self.start_time
                            applied_voltage = self.calculate_voltage_ramp(elapsed_time)
                            v_ref = self.v_ref
                            resistance = self.resistance
                            v_out = (adc_value / 32767)*4.096
                            current = 1e6 * (2 * v_ref - v_out - applied_voltage) / resistance
                            if np.isnan(current) or np.isinf(current) or abs(current) > 1000:
                                current = 0.0
                                print(f"Invalid current detected, set to 0: ADC={adc_value}, v_out={v_out}")
                            if points_skipped < initial_skip:
                                points_skipped += 1
                                print(f"Skipping transient data, count: {points_skipped}")
                            else:
                                current_window.append(current)
                                if len(current_window) > window_size:
                                    current_window.pop(0)
                                smoothed_current = np.mean(current_window) if current_window else current
                                try:
                                    offset_current = float(self.offset_current_edit.text())
                                    if abs(offset_current) > 1000:
                                        print(f"Invalid offset current: {offset_current} µA, using calibrated value {self.offset_current}")
                                        offset_current = self.offset_current
                                except ValueError:
                                    print(f"Invalid offset current input, using calibrated value {self.offset_current}")
                                    offset_current = self.offset_current
                                adjusted_current = smoothed_current - offset_current
                                self.applied_voltage_buffer.append(applied_voltage)
                                self.current_buffer.append(adjusted_current)
                                self.time_buffer.append(elapsed_time)
                        else:
                            print(f"Ignored out-of-range ADC value: {line}")
                    except ValueError:
                        if line != "CV complete.":
                            print(f"Ignored unexpected data: {line}")
                            if "Skipping transient data" in line:
                                points_skipped += 1
                                print(f"Firmware skipping transient data, count: {points_skipped}")
                            elif "ADC:ERROR" in line:
                                print("Firmware reported ADC error")
                except Exception as e:
                    print(f"Error reading data: {e}")
                    break
        if not self.serial_port.is_open:
            self.disconnect_serial()
            QMessageBox.warning(self, "Disconnected", "Serial port was disconnected. Please reconnect.")
        self.read_thread = None
        self.status_bar.showMessage("Acquisition stopped")
        self.update_button_states()

    def update_plots(self):
        with self.lock:
            if self.applied_voltage_buffer and self.current_buffer:
                if len(self.applied_voltage_buffer) != len(self.current_buffer):
                    print("Buffer length mismatch in CV plot")
                    return
                self.plot_data.setData(self.applied_voltage_buffer, self.current_buffer)
                if self.applied_voltage_buffer:
                    self.plot_widget.setXRange(min(self.applied_voltage_buffer), max(self.applied_voltage_buffer))
                if self.current_buffer:
                    self.plot_widget.setYRange(min(self.current_buffer) - 2, max(self.current_buffer) + 2)

            if self.time_buffer and self.applied_voltage_buffer:
                if len(self.time_buffer) != len(self.applied_voltage_buffer):
                    print("Buffer length mismatch in voltage-time plot")
                    return
                self.voltage_time_data.setData(self.time_buffer, self.applied_voltage_buffer)
                if self.time_buffer:
                    self.voltage_time_widget.setXRange(min(self.time_buffer), max(self.time_buffer))
                if self.applied_voltage_buffer:
                    self.voltage_time_widget.setYRange(min(self.applied_voltage_buffer) - 0.1, max(self.applied_voltage_buffer) + 0.1)

    def save_data(self):
        with self.lock:
            if not self.applied_voltage_buffer:
                print("No data to save.")
                QMessageBox.warning(self, "No Data", "No data available to save.")
                return
            if not (len(self.applied_voltage_buffer) == len(self.current_buffer) == len(self.time_buffer)):
                print("Buffer length mismatch detected.")
                QMessageBox.warning(self, "Data Error", "Data buffers are inconsistent. Cannot save.")
                return
            data_to_save = list(zip(self.time_buffer, self.applied_voltage_buffer, self.current_buffer))

        params = self.get_cv_parameters()
        if not params:
            return
        start_v, end_v, scan_rate, cycles = params
        try:
            offset_current = float(self.offset_current_edit.text())
        except ValueError:
            offset_current = self.offset_current
            print(f"Invalid offset current input, using calibrated value {self.offset_current} for save")

        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save CV Data", "", "CSV Files (*.csv);;All Files (*)", options=options
        )
        if file_path:
            try:
                with open(file_path, "w") as file:
                    file.write(f"# Start Voltage (V): {start_v}\n")
                    file.write(f"# End Voltage (V): {end_v}\n")
                    file.write(f"# Scan Rate (V/s): {scan_rate}\n")
                    file.write(f"# Cycles: {cycles}\n")
                    file.write(f"# Offset Current (µA): {offset_current}\n")
                    file.write("Time (s),Applied Voltage (V),Current (µA)\n")
                    for t, v_applied, current in data_to_save:
                        file.write(f"{t},{v_applied},{current}\n")
                print(f"Data saved to {file_path}")
                with self.lock:
                    self.applied_voltage_buffer.clear()
                    self.current_buffer.clear()
                    self.time_buffer.clear()
                self.plot_data.clear()
                self.voltage_time_data.clear()
                self.update_button_states()
            except Exception as e:
                print(f"Error saving data: {e}")
                QMessageBox.warning(self, "Save Error", f"Failed to save data: {e}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    gui = CyclicVoltammetryGUI()
    gui.show()
    sys.exit(app.exec_())