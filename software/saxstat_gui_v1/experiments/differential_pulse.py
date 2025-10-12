"""
Differential Pulse Voltammetry Experiment

Implementation of differential pulse voltammetry based on prototype v03 firmware protocol.
DPV provides excellent sensitivity for trace analysis through pulse-differential measurements.
"""

from typing import Dict, Any, Optional
from .base_experiment import BaseExperiment
from .experiment_registry import register_experiment


@register_experiment
class DifferentialPulseVoltammetry(BaseExperiment):
    """
    Differential Pulse Voltammetry (DPV) experiment implementation.

    DPV superimposes periodic voltage pulses on a linear potential ramp.
    Current is measured before and at the end of each pulse, and the
    difference is plotted vs potential. This technique offers:

    Key advantages:
    - Excellent sensitivity for trace analysis (nanomolar range possible)
    - High discrimination against background/charging currents
    - Well-defined peak shapes for quantitative analysis
    - Better resolution than normal pulse voltammetry

    Compatible with prototype v03 firmware protocol:
    - START command: DPV:<start_v>:<end_v>:<step>:<pulse>:<period>:<width>
    - Data format: Baseline and pulse currents for differential calculation
    - Completion: "DPV complete." message

    Note: If firmware doesn't support DPV directly, can approximate with
    SWV or custom waveform generation.
    """

    def __init__(self):
        super().__init__()
        self.experiment_name = "Differential Pulse Voltammetry"

        # Hardware calibration (from v0)
        self.tia_resistance = 10000  # 10kΩ TIA resistance
        self.vref = 1.0  # 1.0V reference voltage
        self.adc_max = 32767  # ADS1115 single-ended max
        self.adc_vref = 4.096  # ADS1115 voltage reference

        # Data processing
        self.offset_current = 0.0  # Calibrated offset (µA)
        self.skip_initial_points = 15  # Skip initial transient points
        self.points_skipped = 0

        # DPV-specific data
        self.current_baseline = []
        self.current_pulse = []
        self.in_baseline = True

    def get_name(self) -> str:
        """Return experiment name."""
        return self.experiment_name

    def get_parameters(self) -> Dict[str, Any]:
        """
        Return DPV parameter schema.

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
                'description': 'Potential step height'
            },
            'pulse_amplitude': {
                'type': float,
                'default': 0.05,
                'min': 0.001,
                'max': 0.1,
                'unit': 'V',
                'description': 'Pulse amplitude'
            },
            'pulse_period': {
                'type': float,
                'default': 0.5,
                'min': 0.1,
                'max': 5.0,
                'unit': 's',
                'description': 'Time between pulses'
            },
            'pulse_width': {
                'type': float,
                'default': 0.05,
                'min': 0.01,
                'max': 0.5,
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
        Validate DPV parameters.

        Args:
            params: Parameter dictionary

        Returns:
            bool: True if valid

        Raises:
            ValueError: If validation fails with description
        """
        schema = self.get_parameters()

        # Check all required parameters present
        required_params = ['start_voltage', 'end_voltage', 'step_height',
                          'pulse_amplitude', 'pulse_period', 'pulse_width']
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

        # Pulse amplitude should be comparable to or larger than step height
        if params['pulse_amplitude'] < params['step_height']:
            raise ValueError(
                "Pulse amplitude should be at least equal to step height for optimal results"
            )

        return True

    def generate_command(self, params: Dict[str, Any]) -> str:
        """
        Generate START command for firmware.

        Args:
            params: Validated parameters

        Returns:
            str: Command string in format:
                DPV:<start_v>:<end_v>:<step>:<pulse>:<period>:<width>

        Note: If firmware doesn't support DPV, this will need to be
        implemented through custom waveform or SWV approximation.
        """
        cmd = (
            f"DPV:"
            f"{params['start_voltage']}:"
            f"{params['end_voltage']}:"
            f"{params['step_height']}:"
            f"{params['pulse_amplitude']}:"
            f"{params['pulse_period']}:"
            f"{params['pulse_width']}"
        )
        return cmd

    def process_data_point(self, raw_data: str) -> Optional[Dict[str, float]]:
        """
        Process data from firmware.

        For DPV, we expect pairs: voltage, baseline_current, pulse_current
        The differential current is calculated as: diff = pulse - baseline

        Args:
            raw_data: Raw string from serial

        Returns:
            dict or None: Processed data point with
                {'time': float, 'voltage': float, 'current': float,
                 'baseline_current': float, 'pulse_current': float}
                or None if data should be skipped
        """
        # Check for completion message
        if raw_data.strip() in ["DPV complete.", "CV complete."]:
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

        # For DPV, we need to track baseline and pulse currents
        # This is simplified - real DPV needs synchronized sampling
        if self.in_baseline:
            self.current_baseline.append(current_ua)
            self.in_baseline = False
            # Don't return yet, wait for pulse measurement
            return None
        else:
            self.current_pulse.append(current_ua)
            self.in_baseline = True

            # Calculate differential current
            if len(self.current_baseline) > 0:
                baseline = self.current_baseline[-1]
                pulse = current_ua
                differential = pulse - baseline

                return {
                    'time': elapsed_time,
                    'voltage': voltage,
                    'current': differential,  # Main plot shows differential
                    'baseline_current': baseline,
                    'pulse_current': pulse
                }

        return None

    def _calculate_voltage_at_time(self, elapsed_time: float) -> float:
        """
        Calculate applied voltage at given time for DPV.

        DPV uses a staircase waveform with periodic pulses.

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
        period = self.parameters['pulse_period']

        # Calculate number of steps
        voltage_range = abs(end_v - start_v)
        num_steps = int(voltage_range / step)

        # Time per step
        time_per_step = period

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
        self.current_baseline = []
        self.current_pulse = []
        self.in_baseline = True
        if hasattr(self, '_start_time'):
            delattr(self, '_start_time')

    def get_plot_config(self) -> Dict[str, str]:
        """
        Get plotting configuration for this experiment.

        DPV typically plots differential current vs voltage.

        Returns:
            dict: Plot labels and configuration
        """
        return {
            'x_label': 'Applied Voltage (V)',
            'y_label': 'Differential Current (µA)',
            'title': 'Differential Pulse Voltammogram',
            'x_data': 'voltage',
            'y_data': 'current'  # Differential current
        }
