import threading
import time
from PyQt5.QtWidgets import QMessageBox
import numpy as np

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
                self.offset_current_edit.setText(f"{self.offset_current:.2f}")
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

    params = get_cv_parameters(self)
    if not params:
        return

    if self.applied_voltage_buffer:
        if self.is_running or (self.read_thread and self.read_thread.is_alive()):
            stop_acquisition(self)
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
    unexpected_count = 0
    max_unexpected = 5  # Limit to avoid infinite unexpected responses

    while retry_count < max_retries and not success:
        with self.lock:
            try:
                if not self.serial_port.is_open:
                    QMessageBox.warning(self, "Disconnected", "Serial port is not open.")
                    return
                self.serial_port.reset_input_buffer()  # Clear any stale data
                self.serial_port.write(command.encode())
                print(f"Sent: {command.strip()}")
                start_time = time.time()
                while time.time() - start_time < 10.0:  # Extended timeout to 10 seconds
                    if self.serial_port.in_waiting:
                        line = self.serial_port.readline().decode('utf-8', errors='ignore').strip()
                        if not line:
                            print("Received empty response, continuing to read...")
                            continue
                        print(f"Received raw: {line}")
                        if "START_CONFIRMED" in line:
                            print(f"Confirmed: {line}")
                            success = True
                            break
                        elif "Error" in line:
                            print(f"Firmware error: {line}")
                            QMessageBox.warning(self, "Firmware Error", f"Device reported: {line}")
                            return
                        else:
                            print(f"Unexpected response: {line}")
                            unexpected_count += 1
                            if unexpected_count > max_unexpected:
                                print(f"Too many unexpected responses, aborting start attempt")
                                break
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
    self.timer.start(50)
    self.status_bar.showMessage("Acquisition running")
    self.read_thread = threading.Thread(target=read_serial_data, args=(self,), daemon=True)
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

    print("Read thread started")
    while self.is_running and self.serial_port.is_open and not self.stop_event.is_set():
        with self.lock:
            try:
                if not self.serial_port.is_open:
                    print("Serial port disconnected during acquisition.")
                    self.is_running = False
                    break
                line = self.serial_port.readline().decode('utf-8', errors='ignore').strip()
                if not line:
                    time.sleep(0.01)  # Avoid tight loop if no data
                    continue
                print(f"Raw line received: {line}")
                if line == "CV complete.":
                    self.is_running = False
                    print("Acquisition complete")
                    break
                try:
                    parts = line.split()
                    print(f"Parsed line '{line}' into parts: {parts}")  # Debug output
                    if len(parts) >= 2 and parts[0] == "Current:":
                        try:
                            current = float(parts[1])
                            # Adjust based on unit and mode
                            if len(parts) > 2:
                                if parts[2] == "nA":
                                    current /= 1000.0  # Convert nA to µA
                                elif parts[2] == "uA" and self.current_mode > 0:
                                    current *= 1000.0  # Convert µA to nA, then adjust range
                                    if self.current_mode == 1:
                                        current /= 100.0  # Scale to ±100 nA range
                                    elif self.current_mode == 2:
                                        current /= 1000.0  # Scale to ±10 nA range
                            elapsed_time = time.time() - self.start_time
                            applied_voltage = calculate_voltage_ramp(self, elapsed_time)
                            current_window.append(current)
                            if len(current_window) > window_size:
                                current_window.pop(0)
                            smoothed_current = np.mean(current_window) if current_window else current
                            adjusted_current = smoothed_current - self.offset_current
                            max_range = [500, 100, 10][self.current_mode] / 1000.0  # Convert to µA
                            if np.isnan(adjusted_current) or np.isinf(adjusted_current) or abs(adjusted_current) > max_range:
                                adjusted_current = 0.0
                                print(f"Invalid current detected, set to 0: Current={current}, Adjusted={adjusted_current}")
                            if points_skipped < initial_skip:
                                points_skipped += 1
                                print(f"Firmware skipping transient data, count: {points_skipped}")
                            else:
                                try:
                                    with self.lock:
                                        self.applied_voltage_buffer.append(applied_voltage)
                                        self.current_buffer.append(adjusted_current)
                                        self.time_buffer.append(elapsed_time)
                                        print(f"Buffer updated: V={applied_voltage:.3f}V, I={adjusted_current:.3f}µA, t={elapsed_time:.3f}s")
                                except Exception as e:
                                    print(f"Error updating buffers: {e}")
                                    break
                        except (ValueError, IndexError) as e:
                            print(f"Invalid current format in '{line}': {e}")
                    elif "Skipping transient data" in line:
                        points_skipped += 1
                        print(f"Firmware skipping transient data, count: {points_skipped}")
                    elif "ADC:ERROR" in line:
                        print("Firmware reported ADC error")
                except Exception as e:
                    print(f"Error processing line '{line}': {e}")
            except Exception as e:
                print(f"Critical error in read loop: {e}")
                break
    print("Read thread exiting")
    if not self.serial_port.is_open:
        from serial_comm import disconnect_serial
        disconnect_serial(self)
        QMessageBox.warning(self, "Disconnected", "Serial port was disconnected. Please reconnect.")
    self.read_thread = None
    self.status_bar.showMessage("Acquisition stopped")
    self.update_button_states()

def update_data(self, applied_voltage, current, elapsed_time):
    with self.lock:
        self.applied_voltage_buffer.append(applied_voltage)
        self.current_buffer.append(current)
        self.time_buffer.append(elapsed_time)

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

    params = get_cv_parameters(self)
    if not params:
        return
    start_v, end_v, scan_rate, cycles = params
    try:
        offset_current = float(self.offset_current_edit.text())
    except ValueError:
        offset_current = self.offset_current
        print(f"Invalid offset current input, using calibrated value {self.offset_current} for save")

    from PyQt5.QtWidgets import QFileDialog
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
                file.write(f"# Offset Current ({['µA', 'nA', 'nA'][self.current_mode]}): {offset_current}\n")
                file.write("Time (s),Applied Voltage (V),Current\n")
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