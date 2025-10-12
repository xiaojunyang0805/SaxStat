"""
Square Wave Voltammetry Experiment

Implementation of square wave voltammetry based on prototype v03 firmware protocol.
SWV provides enhanced sensitivity for trace analysis through differential measurements.
"""

from typing import Dict, Any, Optional
from .base_experiment import BaseExperiment
from .experiment_registry import register_experiment


@register_experiment
class SquareWaveVoltammetry(BaseExperiment):
    """
    Square Wave Voltammetry (SWV) experiment implementation.

    SWV superimposes a square wave modulation on a staircase potential sweep.
    By measuring current at both forward and reverse pulses and calculating
    the difference, SWV achieves high sensitivity and discrimination against
    background currents.

    Key advantages:
    - Enhanced sensitivity for trace analysis (sub-micromolar)
    - Better signal-to-noise ratio than LSV/CV
    - Discrimination against charging currents
    - Faster than DPV for similar sensitivity

    Compatible with prototype v03 firmware protocol:
    - START command: SWV:<start_v>:<end_v>:<step>:<pulse>:<freq>
    - Data format: Forward, reverse, and differential currents
    - Completion: "SWV complete." message

    Note: If firmware doesn't support SWV directly, can approximate with
    fast CV or custom waveform generation.
    """

    def __init__(self):
        super().__init__()
        self.experiment_name = "Square Wave Voltammetry"

        # Hardware calibration (from v0)
        self.tia_resistance = 10000  # 10kΩ TIA resistance
        self.vref = 1.0  # 1.0V reference voltage
        self.adc_max = 32767  # ADS1115 single-ended max
        self.adc_vref = 4.096  # ADS1115 voltage reference

        # Data processing
        self.offset_current = 0.0  # Calibrated offset (µA)
        self.skip_initial_points = 20  # Skip fewer points for SWV
        self.points_skipped = 0

        # SWV-specific data
        self.current_forward = []
        self.current_reverse = []
        self.in_forward_pulse = True

    def get_name(self) -> str:
        """Return experiment name."""
        return self.experiment_name

    def get_parameters(self) -> Dict[str, Any]:
        """
        Return SWV parameter schema.

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
            'step_height': {
                'type': float,
                'default': 0.004,
                'min': 0.001,
                'max': 0.01,
                'unit': 'V',
                'description': 'Staircase step height'
            },
            'pulse_amplitude': {
                'type': float,
                'default': 0.025,
                'min': 0.001,
                'max': 0.1,
                'unit': 'V',
                'description': 'Square wave pulse amplitude'
            },
            'frequency': {
                'type': float,
                'default': 15.0,
                'min': 1.0,
                'max': 100.0,
                'unit': 'Hz',
                'description': 'Square wave frequency'
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
        Validate SWV parameters.

        Args:
            params: Parameter dictionary

        Returns:
            bool: True if valid

        Raises:
            ValueError: If validation fails with description
        """
        schema = self.get_parameters()

        # Check all required parameters present
        for key in ['start_voltage', 'end_voltage', 'step_height', 'pulse_amplitude', 'frequency']:
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

        # Pulse amplitude should be larger than step height for meaningful differential
        if params['pulse_amplitude'] < params['step_height']:
            raise ValueError(
                "Pulse amplitude should be larger than step height for optimal results"
            )

        return True

    def generate_command(self, params: Dict[str, Any]) -> str:
        """
        Generate START command for firmware.

        Args:
            params: Validated parameters

        Returns:
            str: Command string in format:
                SWV:<start_v>:<end_v>:<step>:<pulse>:<freq>

        Note: If firmware doesn't support SWV, this will need to be
        implemented through custom waveform or multiple CV sweeps.
        """
        cmd = (
            f"SWV:"
            f"{params['start_voltage']}:"
            f"{params['end_voltage']}:"
            f"{params['step_height']}:"
            f"{params['pulse_amplitude']}:"
            f"{params['frequency']}"
        )
        return cmd

    def process_data_point(self, raw_data: str) -> Optional[Dict[str, float]]:
        """
        Process data from firmware.

        For SWV, we expect triplets: voltage, forward_current, reverse_current
        The differential current is calculated as: diff = forward - reverse

        Args:
            raw_data: Raw string from serial

        Returns:
            dict or None: Processed data point with
                {'time': float, 'voltage': float, 'current': float,
                 'forward_current': float, 'reverse_current': float}
                or None if data should be skipped
        """
        # Check for completion message
        if raw_data.strip() in ["SWV complete.", "CV complete."]:
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

        # Calculate voltage position in sweep
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

        # For SWV, we need to track forward and reverse pulses
        # This is simplified - real SWV needs synchronized sampling
        if self.in_forward_pulse:
            self.current_forward.append(current_ua)
            self.in_forward_pulse = False
            # Don't return yet, wait for reverse
            return None
        else:
            self.current_reverse.append(current_ua)
            self.in_forward_pulse = True

            # Calculate differential current
            if len(self.current_forward) > 0:
                forward = self.current_forward[-1]
                reverse = current_ua
                differential = forward - reverse

                return {
                    'time': elapsed_time,
                    'voltage': voltage,
                    'current': differential,  # Main plot shows differential
                    'forward_current': forward,
                    'reverse_current': reverse
                }

        return None

    def _calculate_voltage_at_time(self, elapsed_time: float) -> float:
        """
        Calculate applied voltage at given time for SWV.

        SWV uses a staircase waveform with square wave modulation.

        Args:
            elapsed_time: Time since start in seconds

        Returns:
            float: Applied voltage in volts
        """
        if not self.parameters:
            return 0.0

        start_v = self.parameters['start_voltage']
        end_v = self.parameters['end_voltage']
        step = self.parameters['step_height']
        freq = self.parameters['frequency']

        # Calculate number of steps
        voltage_range = abs(end_v - start_v)
        num_steps = int(voltage_range / step)

        # Time per step (2 pulses per period)
        time_per_step = 1.0 / freq

        # Calculate current step
        step_number = int(elapsed_time / time_per_step)
        if step_number >= num_steps:
            return end_v

        # Base voltage on staircase
        voltage = start_v + step_number * step * (1 if end_v > start_v else -1)

        return voltage

    # Hook methods

    def on_configured(self):
        """Called after configuration - store offset current."""
        if 'offset_current' in self.parameters:
            self.offset_current = self.parameters['offset_current']

    def on_started(self):
        """Called when experiment starts - reset counters and data."""
        self.points_skipped = 0
        self.current_forward = []
        self.current_reverse = []
        self.in_forward_pulse = True
        if hasattr(self, '_start_time'):
            delattr(self, '_start_time')

    def get_plot_config(self) -> Dict[str, str]:
        """
        Get plotting configuration for this experiment.

        SWV typically plots differential current vs voltage.

        Returns:
            dict: Plot labels and configuration
        """
        return {
            'x_label': 'Applied Voltage (V)',
            'y_label': 'Differential Current (µA)',
            'title': 'Square Wave Voltammogram',
            'x_data': 'voltage',
            'y_data': 'current'  # Differential current
        }
