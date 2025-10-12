"""
Chronoamperometry Experiment

Implementation of chronoamperometry based on prototype v03 firmware protocol.
Measures current response over time at a fixed potential.
"""

from typing import Dict, Any, Optional
from .base_experiment import BaseExperiment
from .experiment_registry import register_experiment


@register_experiment
class Chronoamperometry(BaseExperiment):
    """
    Chronoamperometry (CA) experiment implementation.

    CA applies a constant potential and measures the resulting current
    over time. Useful for studying diffusion-limited processes,
    electrode kinetics, and surface reactions.

    Compatible with prototype v03 firmware protocol:
    - START command: CA:<potential>:<duration>
    - Data format: Time-current pairs
    - Completion: "CA complete." message

    Note: This requires firmware support for CA mode. If not available,
    can be implemented as CV with start_v = end_v.
    """

    def __init__(self):
        super().__init__()
        self.experiment_name = "Chronoamperometry"

        # Hardware calibration (from v0)
        self.tia_resistance = 10000  # 10kΩ TIA resistance
        self.vref = 1.0  # 1.0V reference voltage
        self.adc_max = 32767  # ADS1115 single-ended max
        self.adc_vref = 4.096  # ADS1115 voltage reference

        # Data processing
        self.offset_current = 0.0  # Calibrated offset (µA)
        self.skip_initial_points = 10  # Skip fewer points for CA
        self.points_skipped = 0

        # CA-specific
        self.applied_potential = 0.0

    def get_name(self) -> str:
        """Return experiment name."""
        return self.experiment_name

    def get_parameters(self) -> Dict[str, Any]:
        """
        Return CA parameter schema.

        Returns:
            dict: Parameter definitions with defaults and constraints
        """
        return {
            'potential': {
                'type': float,
                'default': 0.0,
                'min': -1.5,
                'max': 1.5,
                'unit': 'V',
                'description': 'Applied potential'
            },
            'duration': {
                'type': float,
                'default': 10.0,
                'min': 0.1,
                'max': 300.0,
                'unit': 's',
                'description': 'Measurement duration'
            },
            'sample_interval': {
                'type': float,
                'default': 0.1,
                'min': 0.01,
                'max': 10.0,
                'unit': 's',
                'description': 'Sampling interval'
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
        Validate CA parameters.

        Args:
            params: Parameter dictionary

        Returns:
            bool: True if valid

        Raises:
            ValueError: If validation fails with description
        """
        schema = self.get_parameters()

        # Check all required parameters present
        for key in ['potential', 'duration']:
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
        if 'sample_interval' in params and 'duration' in params:
            if params['sample_interval'] >= params['duration']:
                raise ValueError(
                    "Sample interval must be less than duration"
                )

        return True

    def generate_command(self, params: Dict[str, Any]) -> str:
        """
        Generate START command for firmware.

        For prototype v03, CA can be implemented as CV with start = end voltage
        and very slow scan rate, or with dedicated CA firmware command if available.

        Args:
            params: Validated parameters

        Returns:
            str: Command string
        """
        # Store applied potential for data processing
        self.applied_potential = params['potential']

        # Option 1: If firmware has dedicated CA command
        # cmd = f"CA:{params['potential']}:{params['duration']}"

        # Option 2: Implement as CV with start = end (compatible with v03)
        # Use very slow scan rate to approximate constant potential
        cmd = (
            f"START:"
            f"{params['potential']}:"
            f"{params['potential']}:"
            f"0.001:"  # Very slow scan rate (nearly constant)
            f"1"  # Single "sweep" (constant potential)
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
        # Check for completion messages
        if raw_data.strip() in ["CA complete.", "CV complete."]:
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

        # Skip initial transient points (fewer for CA)
        if self.points_skipped < self.skip_initial_points:
            self.points_skipped += 1
            return None

        # Calculate time (elapsed since start)
        from time import time
        if not hasattr(self, '_start_time'):
            self._start_time = time()
        elapsed_time = time() - self._start_time

        # For CA, voltage is constant at applied potential
        applied_voltage = self.applied_potential

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

    # Hook methods

    def on_configured(self):
        """Called after configuration - store offset current and potential."""
        if 'offset_current' in self.parameters:
            self.offset_current = self.parameters['offset_current']
        if 'potential' in self.parameters:
            self.applied_potential = self.parameters['potential']

    def on_started(self):
        """Called when experiment starts - reset counters."""
        self.points_skipped = 0
        if hasattr(self, '_start_time'):
            delattr(self, '_start_time')

    def get_plot_config(self) -> Dict[str, str]:
        """
        Get plotting configuration for this experiment.

        CA plots current vs time (different from voltammetry).

        Returns:
            dict: Plot labels and configuration
        """
        return {
            'x_label': 'Time (s)',
            'y_label': 'Current (µA)',
            'title': f'Chronoamperometry at {self.applied_potential:.3f} V',
            'x_data': 'time',  # Different from CV/LSV!
            'y_data': 'current'
        }
