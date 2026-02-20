"""
Base Experiment Class

Abstract base class defining the interface and lifecycle for all
electrochemical experiments. Uses template method pattern.
"""

from abc import ABCMeta, abstractmethod
from typing import Dict, Any, Optional
from PyQt5.QtCore import QObject, pyqtSignal
from enum import Enum


class ExperimentState(Enum):
    """Experiment execution states."""
    IDLE = "idle"
    CONFIGURING = "configuring"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPING = "stopping"
    COMPLETED = "completed"
    ERROR = "error"


# Combined metaclass to resolve QObject and ABCMeta conflict
class QABCMeta(type(QObject), ABCMeta):
    """Metaclass combining QObject's metaclass with ABCMeta."""
    pass


class BaseExperiment(QObject, metaclass=QABCMeta):
    """
    Abstract base class for all electrochemical experiments.

    Subclasses must implement:
    - get_name()
    - get_parameters()
    - validate_parameters()
    - generate_command()
    - process_data_point()
    """

    # Signals
    state_changed = pyqtSignal(ExperimentState)
    data_received = pyqtSignal(dict)  # {time, voltage, current, ...}
    progress_updated = pyqtSignal(float)  # Progress 0.0 to 1.0
    error_occurred = pyqtSignal(str)  # Error message

    def __init__(self):
        super().__init__()
        self.state = ExperimentState.IDLE
        self.parameters: Dict[str, Any] = {}
        self.data_buffer = []

    # Abstract methods - must be implemented by subclasses

    @abstractmethod
    def get_name(self) -> str:
        """Return the experiment name (e.g., 'Cyclic Voltammetry')."""
        pass

    @abstractmethod
    def get_parameters(self) -> Dict[str, Any]:
        """
        Return parameter schema with default values.

        Returns:
            dict: Parameter schema in format:
                {
                    'param_name': {
                        'type': str|int|float,
                        'default': value,
                        'min': min_value,
                        'max': max_value,
                        'unit': 'V'|'mA'|'s', etc.
                        'description': 'Parameter description'
                    }
                }
        """
        pass

    @abstractmethod
    def validate_parameters(self, params: Dict[str, Any]) -> bool:
        """
        Validate experiment parameters.

        Args:
            params: Dictionary of parameter values

        Returns:
            bool: True if valid, False otherwise

        Raises:
            ValueError: With description of validation error
        """
        pass

    @abstractmethod
    def generate_command(self, params: Dict[str, Any]) -> str:
        """
        Generate the serial command string for the hardware.

        Args:
            params: Validated parameter dictionary

        Returns:
            str: Command string to send to hardware
        """
        pass

    @abstractmethod
    def process_data_point(self, raw_data: str) -> Optional[Dict[str, float]]:
        """
        Process a single data point from hardware.

        Args:
            raw_data: Raw string from serial port

        Returns:
            dict or None: Processed data point with keys like
                {'time': float, 'voltage': float, 'current': float}
                or None if data should be skipped
        """
        pass

    # Template method - defines experiment lifecycle

    def configure(self, params: Dict[str, Any]):
        """Configure experiment with parameters (template method)."""
        self._set_state(ExperimentState.CONFIGURING)

        try:
            if self.validate_parameters(params):
                self.parameters = params.copy()
                self.on_configured()
            else:
                raise ValueError("Parameter validation failed")
        except Exception as e:
            self._set_state(ExperimentState.ERROR)
            self.error_occurred.emit(str(e))
            raise

        self._set_state(ExperimentState.IDLE)

    def start(self):
        """Start experiment execution (template method)."""
        if self.state != ExperimentState.IDLE:
            raise RuntimeError(f"Cannot start from state {self.state}")

        self._set_state(ExperimentState.RUNNING)
        self.data_buffer.clear()
        self.on_started()

    def stop(self):
        """Stop experiment execution (template method)."""
        if self.state != ExperimentState.RUNNING:
            return

        self._set_state(ExperimentState.STOPPING)
        self.on_stopping()
        self._set_state(ExperimentState.IDLE)

    def complete(self):
        """Mark experiment as completed (template method)."""
        self._set_state(ExperimentState.COMPLETED)
        self.on_completed()

    # Hook methods - can be overridden by subclasses

    def on_configured(self):
        """Called after successful configuration."""
        pass

    def on_started(self):
        """Called when experiment starts."""
        pass

    def on_stopping(self):
        """Called when experiment is stopping."""
        pass

    def on_completed(self):
        """Called when experiment completes."""
        pass

    # Utility methods

    def _set_state(self, new_state: ExperimentState):
        """Update experiment state and emit signal."""
        if self.state != new_state:
            self.state = new_state
            self.state_changed.emit(new_state)

    def add_data_point(self, data_point: Dict[str, float]):
        """Add a processed data point to buffer and emit signal."""
        self.data_buffer.append(data_point)
        self.data_received.emit(data_point)

    def get_data(self) -> list:
        """Return all collected data points."""
        return self.data_buffer.copy()

    def set_tia_resistance(self, resistance: float):
        """Set TIA feedback resistance for current calculation."""
        self.tia_resistance = resistance

    def clear_data(self):
        """Clear the data buffer."""
        self.data_buffer.clear()
