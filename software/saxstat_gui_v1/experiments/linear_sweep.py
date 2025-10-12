"""
Linear Sweep Voltammetry Experiment

Implementation of linear sweep voltammetry based on prototype v03 firmware protocol.
Similar to CV but performs a single linear sweep from start to end voltage.
"""

from typing import Dict, Any, Optional
from .base_experiment import BaseExperiment
from .experiment_registry import register_experiment


@register_experiment
class LinearSweepVoltammetry(BaseExperiment):
    """
    Linear Sweep Voltammetry (LSV) experiment implementation.

    LSV performs a single potential sweep from start to end voltage,
    measuring current response. Useful for studying irreversible reactions
    and determining kinetic parameters.

    Compatible with prototype v03 firmware protocol:
    - START command: START:<start_v>:<end_v>:<scan_rate>:1
    - Data format: ADC values (0-32767 for ADS1115)
    - Completion: "CV complete." message (firmware uses same endpoint)
    """

    def __init__(self):
        super().__init__()
        self.experiment_name = "Linear Sweep Voltammetry"

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
        Return LSV parameter schema.

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
                'description': 'End voltage'
            },
            'scan_rate': {
                'type': float,
                'default': 0.05,
                'min': 0.01,
                'max': 0.2,
                'unit': 'V/s',
                'description': 'Scan rate'
            },
            'offset_current': {
                'type': float,
                'default': 0.0,
                'min': -1000,
                'max': 1000,
                'unit': 'µA',
                'description': 'Offset current for baseline correction'
            }
        }

    def validate_parameters(self, params: Dict[str, Any]) -> bool:
        """
        Validate LSV parameters.

        Args:
            params: Parameter dictionary

        Returns:
            bool: True if valid

        Raises:
            ValueError: If validation fails with description
        """
        schema = self.get_parameters()

        # Check all required parameters present
        for key in ['start_voltage', 'end_voltage', 'scan_rate']:
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

        LSV is implemented as CV with 1 cycle. The firmware uses the same
        command format.

        Args:
            params: Validated parameters

        Returns:
            str: Command string in format:
                START:<start_v>:<end_v>:<scan_rate>:1
        """
        cmd = (
            f"START:"
            f"{params['start_voltage']}:"
            f"{params['end_voltage']}:"
            f"{params['scan_rate']}:"
            f"1"  # Single sweep = 1 cycle
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
        Calculate applied voltage at given time for linear sweep.

        For LSV, voltage changes linearly from start to end.

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

        # Calculate sweep parameters
        voltage_range = abs(end_v - start_v)
        sweep_time = voltage_range / scan_rate

        # Clamp to sweep time
        if elapsed_time > sweep_time:
            return end_v

        # Linear interpolation
        fraction = elapsed_time / sweep_time
        voltage = start_v + fraction * (end_v - start_v)

        return voltage

    # Hook methods

    def on_configured(self):
        """Called after configuration - store offset current."""
        if 'offset_current' in self.parameters:
            self.offset_current = self.parameters['offset_current']

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
            'title': 'Linear Sweep Voltammogram',
            'x_data': 'voltage',
            'y_data': 'current'
        }
