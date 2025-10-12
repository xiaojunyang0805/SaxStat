"""
Normal Pulse Voltammetry Experiment

Implementation of normal pulse voltammetry based on prototype v03 firmware protocol.
NPV provides excellent discrimination against charging current.
"""

from typing import Dict, Any, Optional
from .base_experiment import BaseExperiment
from .experiment_registry import register_experiment


@register_experiment
class NormalPulseVoltammetry(BaseExperiment):
    """
    Normal Pulse Voltammetry (NPV) experiment implementation.

    NPV applies a series of pulses from a constant baseline potential
    to increasing pulse potentials. Current is measured near the end
    of each pulse when charging current has decayed.

    Key advantages:
    - Excellent discrimination against charging current
    - Good sensitivity for irreversible systems
    - Well-defined baseline (all pulses start from same potential)
    - Useful for systems with slow electrode kinetics

    Compatible with prototype v03 firmware protocol:
    - START command: NPV:<baseline>:<start_v>:<end_v>:<step>:<period>:<width>
    - Data format: Current measured at end of each pulse
    - Completion: "NPV complete." message

    Note: If firmware doesn't support NPV directly, can be implemented
    with custom pulse sequence.
    """

    def __init__(self):
        super().__init__()
        self.experiment_name = "Normal Pulse Voltammetry"

        # Hardware calibration (from v0)
        self.tia_resistance = 10000  # 10kΩ TIA resistance
        self.vref = 1.0  # 1.0V reference voltage
        self.adc_max = 32767  # ADS1115 single-ended max
        self.adc_vref = 4.096  # ADS1115 voltage reference

        # Data processing
        self.offset_current = 0.0  # Calibrated offset (µA)
        self.skip_initial_points = 10  # Skip fewer points for NPV
        self.points_skipped = 0

        # NPV-specific
        self.baseline_potential = 0.0

    def get_name(self) -> str:
        """Return experiment name."""
        return self.experiment_name

    def get_parameters(self) -> Dict[str, Any]:
        """
        Return NPV parameter schema.

        Returns:
            dict: Parameter definitions with defaults and constraints
        """
        return {
            'baseline_potential': {
                'type': float,
                'default': 0.0,
                'min': -1.5,
                'max': 1.5,
                'unit': 'V',
                'description': 'Baseline potential (between pulses)'
            },
            'start_voltage': {
                'type': float,
                'default': -0.5,
                'min': -1.5,
                'max': 1.5,
                'unit': 'V',
                'description': 'Starting pulse voltage'
            },
            'end_voltage': {
                'type': float,
                'default': 0.5,
                'min': -1.5,
                'max': 1.5,
                'unit': 'V',
                'description': 'End pulse voltage'
            },
            'step_height': {
                'type': float,
                'default': 0.005,
                'min': 0.001,
                'max': 0.01,
                'unit': 'V',
                'description': 'Pulse height increment'
            },
            'pulse_period': {
                'type': float,
                'default': 1.0,
                'min': 0.1,
                'max': 10.0,
                'unit': 's',
                'description': 'Time between pulses'
            },
            'pulse_width': {
                'type': float,
                'default': 0.05,
                'min': 0.01,
                'max': 1.0,
                'unit': 's',
                'description': 'Duration of pulse'
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
        Validate NPV parameters.

        Args:
            params: Parameter dictionary

        Returns:
            bool: True if valid

        Raises:
            ValueError: If validation fails with description
        """
        schema = self.get_parameters()

        # Check all required parameters present
        required_params = ['baseline_potential', 'start_voltage', 'end_voltage',
                          'step_height', 'pulse_period', 'pulse_width']
        for key in required_params:
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

        # Pulse width must be less than pulse period
        if params['pulse_width'] >= params['pulse_period']:
            raise ValueError(
                "Pulse width must be less than pulse period"
            )

        # Baseline should be different from pulse range for meaningful measurement
        baseline = params['baseline_potential']
        start = params['start_voltage']
        end = params['end_voltage']
        if baseline == start or baseline == end:
            import warnings
            warnings.warn(
                "Baseline potential equals start or end voltage - "
                "consider using a distinct baseline for better results"
            )

        return True

    def generate_command(self, params: Dict[str, Any]) -> str:
        """
        Generate START command for firmware.

        Args:
            params: Validated parameters

        Returns:
            str: Command string in format:
                NPV:<baseline>:<start_v>:<end_v>:<step>:<period>:<width>

        Note: If firmware doesn't support NPV, this will need to be
        implemented through custom pulse sequence.
        """
        self.baseline_potential = params['baseline_potential']

        cmd = (
            f"NPV:"
            f"{params['baseline_potential']}:"
            f"{params['start_voltage']}:"
            f"{params['end_voltage']}:"
            f"{params['step_height']}:"
            f"{params['pulse_period']}:"
            f"{params['pulse_width']}"
        )
        return cmd

    def process_data_point(self, raw_data: str) -> Optional[Dict[str, float]]:
        """
        Process data from firmware.

        For NPV, current is measured near the end of each pulse.

        Args:
            raw_data: Raw string from serial

        Returns:
            dict or None: Processed data point with
                {'time': float, 'voltage': float, 'current': float}
                or None if data should be skipped
        """
        # Check for completion message
        if raw_data.strip() in ["NPV complete.", "CV complete."]:
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

        # Calculate time
        from time import time
        if not hasattr(self, '_start_time'):
            self._start_time = time()
        elapsed_time = time() - self._start_time

        # Convert ADC to voltage
        v_out = (adc_value / self.adc_max) * self.adc_vref

        # Calculate voltage position in pulse sequence
        voltage = self._calculate_voltage_at_time(elapsed_time)

        # Calculate current using TIA equation
        current_ua = 1e6 * (
            (2 * self.vref - v_out - voltage) / self.tia_resistance
        )

        # Apply offset correction
        current_ua -= self.offset_current

        # Validate current
        if abs(current_ua) > 1000:
            current_ua = 0.0

        return {
            'time': elapsed_time,
            'voltage': voltage,
            'current': current_ua
        }

    def _calculate_voltage_at_time(self, elapsed_time: float) -> float:
        """
        Calculate applied voltage at given time for NPV.

        NPV pulses from baseline to increasing pulse potentials.

        Args:
            elapsed_time: Time since start in seconds

        Returns:
            float: Applied voltage in volts
        """
        if not self.parameters:
            return 0.0

        baseline = self.parameters['baseline_potential']
        start_v = self.parameters['start_voltage']
        end_v = self.parameters['end_voltage']
        step = self.parameters['step_height']
        period = self.parameters['pulse_period']
        width = self.parameters['pulse_width']

        # Calculate number of steps
        voltage_range = abs(end_v - start_v)
        num_steps = int(voltage_range / step)

        # Calculate current pulse number
        pulse_number = int(elapsed_time / period)
        if pulse_number >= num_steps:
            pulse_number = num_steps - 1

        # Time within current period
        time_in_period = elapsed_time % period

        # Determine if we're in pulse or at baseline
        if time_in_period < width:
            # During pulse
            pulse_voltage = start_v + pulse_number * step * (1 if end_v > start_v else -1)
            return pulse_voltage
        else:
            # At baseline
            return baseline

    # Hook methods

    def on_configured(self):
        """Called after configuration - store offset current and baseline."""
        if 'offset_current' in self.parameters:
            self.offset_current = self.parameters['offset_current']
        if 'baseline_potential' in self.parameters:
            self.baseline_potential = self.parameters['baseline_potential']

    def on_started(self):
        """Called when experiment starts - reset counters."""
        self.points_skipped = 0
        if hasattr(self, '_start_time'):
            delattr(self, '_start_time')

    def get_plot_config(self) -> Dict[str, str]:
        """
        Get plotting configuration for this experiment.

        NPV typically plots current vs pulse voltage.

        Returns:
            dict: Plot labels and configuration
        """
        return {
            'x_label': 'Pulse Voltage (V)',
            'y_label': 'Current (µA)',
            'title': f'Normal Pulse Voltammogram (baseline: {self.baseline_potential:.3f} V)',
            'x_data': 'voltage',
            'y_data': 'current'
        }
