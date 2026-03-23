"""
Cyclic Voltammetry Experiment

Implementation of cyclic voltammetry based on prototype v03 firmware protocol.
"""

from typing import Dict, Any, Optional
from .base_experiment import BaseExperiment
from .experiment_registry import register_experiment


@register_experiment
class CyclicVoltammetry(BaseExperiment):
    """
    Cyclic Voltammetry (CV) experiment implementation.

    Compatible with prototype v03 firmware protocol:
    - START command: START:<initial_v>:<high_v>:<low_v>:<scan_rate>:<cycles>
    - Data format: DATA:<vramp>,<adc>
    - Completion: "CV complete." message

    Sweep pattern: initial → high → [low ↔ high] × cycles → initial
    """

    def __init__(self):
        super().__init__()
        self.experiment_name = "Cyclic Voltammetry"

        # Hardware calibration
        self.tia_resistance = 10000  # 10kΩ TIA resistance
        self.vref = 1.0  # 1.0V TIA reference voltage
        self.adc_max = 32767  # ADS1115 single-ended max
        self.adc_vref = 4.096  # ADS1115 voltage reference

        # Data processing
        self.offset_current = 0.0  # Calibrated offset (µA)

        # Firmware output parsing state
        self._data_started = False

    def get_name(self) -> str:
        """Return experiment name."""
        return self.experiment_name

    def get_parameters(self) -> Dict[str, Any]:
        """
        Return CV parameter schema.

        Parameters follow standard CV convention:
        - initial_voltage: Where the scan starts and ends
        - high_voltage: Upper vertex potential
        - low_voltage: Lower vertex potential
        """
        return {
            'initial_voltage': {
                'type': float,
                'default': 0.0,
                'min': -0.2,
                'max': 1.5,
                'unit': 'V',
                'description': 'Initial voltage'
            },
            'high_voltage': {
                'type': float,
                'default': 0.5,
                'min': -0.2,
                'max': 1.5,
                'unit': 'V',
                'description': 'High voltage (upper vertex)'
            },
            'low_voltage': {
                'type': float,
                'default': -0.2,
                'min': -0.2,
                'max': 1.5,
                'unit': 'V',
                'description': 'Low voltage (lower vertex)'
            },
            'scan_rate': {
                'type': float,
                'default': 0.02,
                'min': 0.01,
                'max': 0.2,
                'unit': 'V/s',
                'description': 'Scan rate'
            },
            'cycles': {
                'type': int,
                'default': 2,
                'min': 1,
                'max': 10,
                'unit': 'cycles',
                'description': 'Number of cycles'
            }
        }

    def validate_parameters(self, params: Dict[str, Any]) -> bool:
        """Validate CV parameters."""
        schema = self.get_parameters()

        for key in ['initial_voltage', 'high_voltage', 'low_voltage', 'scan_rate', 'cycles']:
            if key not in params:
                raise ValueError(f"Missing required parameter: {key}")

        for key, value in params.items():
            if key not in schema:
                continue
            param_def = schema[key]
            param_type = param_def['type']

            if not isinstance(value, param_type):
                raise ValueError(
                    f"{key} must be {param_type.__name__}, got {type(value).__name__}"
                )
            if 'min' in param_def and value < param_def['min']:
                raise ValueError(f"{key} = {value} below minimum {param_def['min']}")
            if 'max' in param_def and value > param_def['max']:
                raise ValueError(f"{key} = {value} above maximum {param_def['max']}")

        if params['low_voltage'] >= params['high_voltage']:
            raise ValueError("Low voltage must be less than high voltage")

        if params['initial_voltage'] < params['low_voltage'] or \
           params['initial_voltage'] > params['high_voltage']:
            raise ValueError("Initial voltage must be between low and high voltage")

        return True

    def generate_command(self, params: Dict[str, Any]) -> str:
        """
        Generate START command for firmware.

        Format: START:<initial_v>:<high_v>:<low_v>:<scan_rate>:<cycles>
        """
        return (
            f"START:"
            f"{params['initial_voltage']}:"
            f"{params['high_voltage']}:"
            f"{params['low_voltage']}:"
            f"{params['scan_rate']}:"
            f"{params['cycles']}"
        )

    def process_data_point(self, raw_data: str) -> Optional[Dict[str, float]]:
        """
        Parse firmware serial output and produce data points.

        Firmware sends one line per measurement: DATA:<vramp>,<adc>
        We extract the actual DAC voltage and raw ADC value, then compute
        current using the TIA equation matching the firmware.

        Args:
            raw_data: Raw string line from serial port

        Returns:
            dict or None: {'time': float, 'voltage': float, 'current': float}
        """
        line = raw_data.strip()

        # Check for completion
        if line == "CV complete.":
            self.complete()
            return None

        # Wait for acquisition to begin
        if line == "START_CONFIRMED":
            self._data_started = True
            return None

        if not self._data_started:
            return None

        # Parse data line: DATA:<vramp>,<adc>
        if not line.startswith("DATA:"):
            return None

        try:
            payload = line[5:]  # Strip "DATA:" prefix
            parts = payload.split(",")
            if len(parts) != 2:
                return None

            applied_voltage = float(parts[0])
            adc_value = int(parts[1])
        except (ValueError, IndexError):
            return None

        if adc_value < 0:
            return None

        # Record elapsed time
        from time import time
        if not hasattr(self, '_start_time'):
            self._start_time = time()
        elapsed_time = time() - self._start_time

        # Convert ADC to TIA output voltage
        v_out = (adc_value / self.adc_max) * self.adc_vref

        # TIA current calculation:
        # At zero current, TIA output = 2*Vref - Vapplied (circuit DC bias)
        # With current:  Vout = 2*Vref - Vapplied - I*R
        # Solving for I: I = (2*Vref - Vout - Vapplied) / R
        current_ua = 1e6 * (
            (2 * self.vref - v_out - applied_voltage) / self.tia_resistance
        )

        # Apply calibration offset
        current_ua -= self.offset_current

        return {
            'time': elapsed_time,
            'voltage': applied_voltage,
            'current': current_ua
        }

    # Hook methods

    def load_calibration(self, calibration: Dict[str, float]):
        """Load calibration values from ConfigManager."""
        self.offset_current = calibration.get('offset_current', 0.0)
        self.tia_resistance = calibration.get('tia_resistance', 10000)
        self.vref = calibration.get('vref', 1.0)

    def on_started(self):
        """Called when experiment starts - reset state."""
        self._data_started = False
        if hasattr(self, '_start_time'):
            delattr(self, '_start_time')

    def get_plot_config(self) -> Dict[str, str]:
        """Get plotting configuration for this experiment."""
        return {
            'x_label': 'Applied Voltage (V)',
            'y_label': 'Current (µA)',
            'title': 'Cyclic Voltammogram',
            'x_data': 'voltage',
            'y_data': 'current'
        }
