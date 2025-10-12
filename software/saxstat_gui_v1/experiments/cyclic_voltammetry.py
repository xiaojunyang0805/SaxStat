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
    - START command: START:<start_v>:<end_v>:<scan_rate>:<cycles>
    - Data format: ADC values (0-32767 for ADS1115)
    - Completion: "CV complete." message
    """

    def __init__(self):
        super().__init__()
        self.experiment_name = "Cyclic Voltammetry"

        # Hardware calibration (from v0)
        self.tia_resistance = 10000  # 10kΩ TIA resistance
        self.vref = 1.0  # 1.0V reference voltage
        self.adc_max = 32767  # ADS1115 single-ended max
        self.adc_vref = 4.096  # ADS1115 voltage reference

        # Data processing
        self.offset_current = 0.0  # Calibrated offset (µA)
        self.skip_initial_points = 50  # Skip transient data
        self.points_skipped = 0

    def get_name(self) -> str:
        """Return experiment name."""
        return self.experiment_name

    def get_parameters(self) -> Dict[str, Any]:
        """
        Return CV parameter schema.

        Returns:
            dict: Parameter definitions with defaults and constraints
        """
        return {
            'start_voltage': {
                'type': float,
                'default': -0.5,
                'min': -1.5,
                'max': 1.5,
                'unit': 'V',
                'description': 'Starting voltage'
            },
            'end_voltage': {
                'type': float,
                'default': 0.5,
                'min': -1.5,
                'max': 1.5,
                'unit': 'V',
                'description': 'End voltage (reversal point)'
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
        """
        Validate CV parameters.

        Args:
            params: Parameter dictionary

        Returns:
            bool: True if valid

        Raises:
            ValueError: If validation fails with description
        """
        schema = self.get_parameters()

        # Check all required parameters present
        for key in ['start_voltage', 'end_voltage', 'scan_rate', 'cycles']:
            if key not in params:
                raise ValueError(f"Missing required parameter: {key}")

        # Validate ranges
        for key, value in params.items():
            if key not in schema:
                continue  # Allow extra parameters

            param_def = schema[key]
            param_type = param_def['type']

            # Type check
            if not isinstance(value, param_type):
                raise ValueError(
                    f"{key} must be {param_type.__name__}, got {type(value).__name__}"
                )

            # Range check
            if 'min' in param_def and value < param_def['min']:
                raise ValueError(
                    f"{key} = {value} below minimum {param_def['min']}"
                )
            if 'max' in param_def and value > param_def['max']:
                raise ValueError(
                    f"{key} = {value} above maximum {param_def['max']}"
                )

        # Logical validation
        if params['start_voltage'] == params['end_voltage']:
            raise ValueError("Start and end voltages cannot be equal")

        return True

    def generate_command(self, params: Dict[str, Any]) -> str:
        """
        Generate START command for firmware.

        Args:
            params: Validated parameters

        Returns:
            str: Command string in format:
                START:<start_v>:<end_v>:<scan_rate>:<cycles>
        """
        cmd = (
            f"START:"
            f"{params['start_voltage']}:"
            f"{params['end_voltage']}:"
            f"{params['scan_rate']}:"
            f"{params['cycles']}"
        )
        return cmd

    def process_data_point(self, raw_data: str) -> Optional[Dict[str, float]]:
        """
        Process ADC value from firmware.

        Args:
            raw_data: Raw string from serial (ADC value or completion message)

        Returns:
            dict or None: Processed data point with
                {'time': float, 'voltage': float, 'current': float}
                or None if data should be skipped
        """
        # Check for completion message
        if raw_data.strip() == "CV complete.":
            self.complete()
            return None

        # Try to parse as ADC value
        try:
            adc_value = float(raw_data)
        except ValueError:
            # Not a number, skip
            return None

        # Validate ADC range
        if not (0 <= adc_value <= self.adc_max):
            return None

        # Skip initial transient points
        if self.points_skipped < self.skip_initial_points:
            self.points_skipped += 1
            return None

        # Calculate time (elapsed since start)
        from time import time
        if not hasattr(self, '_start_time'):
            self._start_time = time()
        elapsed_time = time() - self._start_time

        # Calculate applied voltage from time and parameters
        applied_voltage = self._calculate_voltage_at_time(elapsed_time)

        # Convert ADC to voltage
        v_out = (adc_value / self.adc_max) * self.adc_vref

        # Calculate current using TIA equation
        # I = (2*Vref - Vout - Vapplied) / R
        current_ua = 1e6 * (
            (2 * self.vref - v_out - applied_voltage) / self.tia_resistance
        )

        # Apply offset correction
        current_ua -= self.offset_current

        # Validate current (sanity check)
        if abs(current_ua) > 1000:  # > 1mA seems wrong
            current_ua = 0.0

        return {
            'time': elapsed_time,
            'voltage': applied_voltage,
            'current': current_ua
        }

    def _calculate_voltage_at_time(self, elapsed_time: float) -> float:
        """
        Calculate applied voltage at given time based on CV parameters.

        Args:
            elapsed_time: Time since start in seconds

        Returns:
            float: Applied voltage in volts
        """
        if not self.parameters:
            return 0.0

        start_v = self.parameters['start_voltage']
        end_v = self.parameters['end_voltage']
        scan_rate = self.parameters['scan_rate']
        cycles = self.parameters['cycles']

        # Calculate cycle parameters
        voltage_range = abs(end_v - start_v)
        half_cycle_time = voltage_range / scan_rate
        full_cycle_time = 2 * half_cycle_time
        total_time = cycles * full_cycle_time

        # Clamp to total time
        if elapsed_time > total_time:
            elapsed_time = total_time

        # Determine position within cycle
        cycle_time = elapsed_time % full_cycle_time

        if cycle_time < half_cycle_time:
            # Forward sweep
            fraction = cycle_time / half_cycle_time
            voltage = start_v + fraction * (end_v - start_v)
        else:
            # Reverse sweep
            fraction = (cycle_time - half_cycle_time) / half_cycle_time
            voltage = end_v - fraction * (end_v - start_v)

        return voltage

    # Hook methods

    def load_calibration(self, calibration: Dict[str, float]):
        """
        Load calibration values from ConfigManager.

        Args:
            calibration: Dict with 'offset_current', 'tia_resistance', 'vref'
        """
        self.offset_current = calibration.get('offset_current', 0.0)
        self.tia_resistance = calibration.get('tia_resistance', 10000)
        self.vref = calibration.get('vref', 1.0)

    def on_started(self):
        """Called when experiment starts - reset counters."""
        self.points_skipped = 0
        if hasattr(self, '_start_time'):
            delattr(self, '_start_time')

    def get_plot_config(self) -> Dict[str, str]:
        """
        Get plotting configuration for this experiment.

        Returns:
            dict: Plot labels and configuration
        """
        return {
            'x_label': 'Applied Voltage (V)',
            'y_label': 'Current (µA)',
            'title': 'Cyclic Voltammogram',
            'x_data': 'voltage',
            'y_data': 'current'
        }
