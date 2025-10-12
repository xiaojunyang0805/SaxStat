"""
Potentiometry Experiment

Implementation of open-circuit potentiometry for potential monitoring.
POT measures electrode potential without applying current.
"""

from typing import Dict, Any, Optional
from .base_experiment import BaseExperiment
from .experiment_registry import register_experiment


@register_experiment
class Potentiometry(BaseExperiment):
    """
    Potentiometry (POT) experiment implementation.

    POT measures the open-circuit potential (OCP) of an electrochemical
    cell over time without applying current. This technique is useful for:

    Key applications:
    - pH measurements with ion-selective electrodes
    - Monitoring battery/fuel cell open-circuit voltage
    - Studying corrosion potential
    - Observing potential changes during chemical reactions
    - Equilibrium potential measurements

    Compatible with prototype v03 firmware protocol:
    - START command: POT:<duration>:<interval>
    - Data format: Time-potential pairs
    - Completion: "POT complete." message

    Note: This requires high-impedance voltage measurement capability.
    For potentiostats with TIA, may need to operate in voltage monitoring mode.
    """

    def __init__(self):
        super().__init__()
        self.experiment_name = "Potentiometry"

        # Hardware calibration (from v0)
        self.vref = 1.0  # 1.0V reference voltage
        self.adc_max = 32767  # ADS1115 single-ended max
        self.adc_vref = 4.096  # ADS1115 voltage reference

        # Data processing
        self.offset_voltage = 0.0  # Calibrated offset (V)
        self.skip_initial_points = 5  # Skip very few points for POT
        self.points_skipped = 0

    def get_name(self) -> str:
        """Return experiment name."""
        return self.experiment_name

    def get_parameters(self) -> Dict[str, Any]:
        """
        Return POT parameter schema.

        Returns:
            dict: Parameter definitions with defaults and constraints
        """
        return {
            'duration': {
                'type': float,
                'default': 60.0,
                'min': 1.0,
                'max': 3600.0,
                'unit': 's',
                'description': 'Measurement duration'
            },
            'sample_interval': {
                'type': float,
                'default': 1.0,
                'min': 0.1,
                'max': 60.0,
                'unit': 's',
                'description': 'Sampling interval'
            },
            'offset_voltage': {
                'type': float,
                'default': 0.0,
                'min': -5.0,
                'max': 5.0,
                'unit': 'V',
                'description': 'Offset voltage for calibration'
            }
        }

    def validate_parameters(self, params: Dict[str, Any]) -> bool:
        """
        Validate POT parameters.

        Args:
            params: Parameter dictionary

        Returns:
            bool: True if valid

        Raises:
            ValueError: If validation fails with description
        """
        schema = self.get_parameters()

        # Check all required parameters present
        for key in ['duration', 'sample_interval']:
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
        if params['sample_interval'] >= params['duration']:
            raise ValueError(
                "Sample interval must be less than duration"
            )

        return True

    def generate_command(self, params: Dict[str, Any]) -> str:
        """
        Generate START command for firmware.

        Args:
            params: Validated parameters

        Returns:
            str: Command string in format:
                POT:<duration>:<interval>

        Note: This requires firmware support for open-circuit measurement.
        If not available, can be implemented by reading ADC without
        applying potential.
        """
        cmd = (
            f"POT:"
            f"{params['duration']}:"
            f"{params['sample_interval']}"
        )
        return cmd

    def process_data_point(self, raw_data: str) -> Optional[Dict[str, float]]:
        """
        Process potential data from firmware.

        For POT, we measure voltage directly (no current flow).

        Args:
            raw_data: Raw string from serial (ADC value or completion message)

        Returns:
            dict or None: Processed data point with
                {'time': float, 'voltage': float, 'current': float}
                (current is 0 or near-zero for open circuit)
                or None if data should be skipped
        """
        # Check for completion messages
        if raw_data.strip() in ["POT complete.", "CV complete."]:
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

        # Convert ADC to voltage (direct measurement)
        # For open-circuit measurement, we're reading the cell potential directly
        measured_voltage = (adc_value / self.adc_max) * self.adc_vref

        # Apply offset correction
        measured_voltage += self.offset_voltage

        # For potentiometry, we're measuring potential, not current
        # Current should be near-zero (open circuit)
        current_ua = 0.0

        return {
            'time': elapsed_time,
            'voltage': measured_voltage,
            'current': current_ua  # Open circuit, no current
        }

    # Hook methods

    def on_configured(self):
        """Called after configuration - store offset voltage."""
        if 'offset_voltage' in self.parameters:
            self.offset_voltage = self.parameters['offset_voltage']

    def on_started(self):
        """Called when experiment starts - reset counters."""
        self.points_skipped = 0
        if hasattr(self, '_start_time'):
            delattr(self, '_start_time')

    def get_plot_config(self) -> Dict[str, str]:
        """
        Get plotting configuration for this experiment.

        POT plots potential vs time (open-circuit monitoring).

        Returns:
            dict: Plot labels and configuration
        """
        return {
            'x_label': 'Time (s)',
            'y_label': 'Potential (V)',
            'title': 'Open Circuit Potential vs Time',
            'x_data': 'time',
            'y_data': 'voltage'  # Plotting voltage, not current!
        }
