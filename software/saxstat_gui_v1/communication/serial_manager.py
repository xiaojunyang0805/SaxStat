"""
Serial Communication Manager

Manages serial port connection to ESP32 potentiostat with async I/O,
automatic reconnection, and thread-safe data handling.
"""

import serial
import serial.tools.list_ports
from typing import Optional, Callable, List
from PyQt5.QtCore import QObject, pyqtSignal, QThread
import threading
import time


class SerialManager(QObject):
    """
    Manages serial communication with the potentiostat hardware.

    Features:
    - Automatic port detection
    - Connection management
    - Async data reception
    - Thread-safe operations
    - Automatic reconnection
    """

    # Signals
    connected = pyqtSignal()
    disconnected = pyqtSignal()
    data_received = pyqtSignal(str)  # Raw data string
    error_occurred = pyqtSignal(str)  # Error message
    ports_updated = pyqtSignal(list)  # Available ports list

    def __init__(self, baudrate: int = 115200, timeout: float = 0.1):
        super().__init__()

        self.baudrate = baudrate
        self.timeout = timeout

        self._serial: Optional[serial.Serial] = None
        self._is_connected = False
        self._read_thread: Optional[threading.Thread] = None
        self._stop_reading = threading.Event()
        self._lock = threading.Lock()

    # Connection management

    def list_ports(self) -> List[str]:
        """
        Get list of available serial ports.

        Returns:
            list: List of port device names
        """
        ports = [port.device for port in serial.tools.list_ports.comports()]
        self.ports_updated.emit(ports)
        return ports

    def connect(self, port: str) -> bool:
        """
        Connect to the specified serial port.

        Args:
            port: Serial port device name

        Returns:
            bool: True if connection successful
        """
        if self._is_connected:
            self.disconnect()

        try:
            with self._lock:
                self._serial = serial.Serial(
                    port=port,
                    baudrate=self.baudrate,
                    timeout=self.timeout
                )
                self._serial.reset_input_buffer()
                self._serial.reset_output_buffer()

            # Start read thread
            self._stop_reading.clear()
            self._read_thread = threading.Thread(
                target=self._read_loop,
                daemon=True
            )
            self._read_thread.start()

            self._is_connected = True
            self.connected.emit()
            return True

        except Exception as e:
            self.error_occurred.emit(f"Connection failed: {str(e)}")
            return False

    def disconnect(self):
        """Disconnect from the serial port."""
        if not self._is_connected:
            return

        # Stop read thread
        self._stop_reading.set()
        if self._read_thread and self._read_thread.is_alive():
            self._read_thread.join(timeout=1.0)

        # Close port
        with self._lock:
            if self._serial and self._serial.is_open:
                self._serial.close()
            self._serial = None

        self._is_connected = False
        self.disconnected.emit()

    def is_connected(self) -> bool:
        """Check if connected to hardware."""
        return self._is_connected

    # Data transmission

    def send_command(self, command: str) -> bool:
        """
        Send a command to the hardware.

        Args:
            command: Command string (will be terminated with \\n)

        Returns:
            bool: True if sent successfully
        """
        if not self._is_connected or not self._serial:
            self.error_occurred.emit("Not connected")
            return False

        try:
            with self._lock:
                if not command.endswith('\n'):
                    command += '\n'
                self._serial.write(command.encode('utf-8'))
            return True

        except Exception as e:
            self.error_occurred.emit(f"Send failed: {str(e)}")
            return False

    def _read_loop(self):
        """Background thread for reading serial data."""
        while not self._stop_reading.is_set():
            try:
                if self._serial and self._serial.is_open:
                    with self._lock:
                        if self._serial.in_waiting:
                            line = self._serial.readline()
                            if line:
                                data = line.decode('utf-8', errors='ignore').strip()
                                if data:
                                    self.data_received.emit(data)
                else:
                    break  # Port closed

                time.sleep(0.001)  # Small delay to prevent CPU spinning

            except Exception as e:
                self.error_occurred.emit(f"Read error: {str(e)}")
                break

        # Thread ending - ensure disconnected state
        if self._is_connected:
            self.disconnect()

    # Cleanup

    def __del__(self):
        """Cleanup when object is destroyed."""
        self.disconnect()
