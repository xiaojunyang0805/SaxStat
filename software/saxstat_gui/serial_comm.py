import serial
import threading
import time
from PyQt5.QtWidgets import QMessageBox
import numpy as np

def configure_serial(self, baud_rate=115200):
    port = self.port_combo.currentText()
    with self.lock:
        if self.serial_port and self.serial_port.is_open:
            self.serial_port.close()
        self.serial_port = serial.Serial()
        self.serial_port.port = port
        self.serial_port.baudrate = baud_rate
        self.serial_port.timeout = 0.1
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
        if self.serial_port and self.serial_port.is_open:
            self.serial_port.close()
            print("Serial port closed.")
    self.is_connected = False
    self.status_bar.showMessage("Disconnected")
    self.timer.stop()
    self.update_button_states()

def toggle_connection(self):
    if self.is_connected:
        disconnect_serial(self)
    else:
        if not self.port_combo.currentText():
            QMessageBox.warning(self, "No Port Selected", "Please select a COM port.")
            return
        configure_serial(self)

def refresh_com_ports(self):
    self.port_combo.clear()
    from gui_setup import list_available_ports
    ports = list_available_ports()
    self.port_combo.addItems(ports)
    self.update_button_states()
    print("COM ports refreshed.")

def set_mode(self):
    if self.mode_check_100nA.isChecked() and self.mode_check_10nA.isChecked():
        self.mode_check_100nA.setChecked(False)  # Prioritize ±10 nA if both are checked
    self.current_mode = 1 if self.mode_check_100nA.isChecked() else 2 if self.mode_check_10nA.isChecked() else 0
    self.resistance = 10000 if self.current_mode == 0 else 1000000
    with self.lock:
        if self.serial_port and self.serial_port.is_open:
            self.serial_port.write(f"MODE_{self.current_mode}\n".encode())
            print(f"Sent mode command: MODE_{self.current_mode}")
    self.plot_widget.setLabel('left', f'Current ({["µA", "nA", "nA"][self.current_mode]})')
    self.plot_widget.setYRange(-[500, 100, 10][self.current_mode], [500, 100, 10][self.current_mode])
    self.plot_widget.repaint()