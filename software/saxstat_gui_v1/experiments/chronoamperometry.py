"""
Chronoamperometry Experiment

Measures current response over time at a fixed potential.
"""

from typing import Dict, Any, Optional
from .base_experiment import BaseExperiment
from .experiment_registry import register_experiment


@register_experiment
class Chronoamperometry(BaseExperiment):
    """
    Chronoamperometry (CA) experiment implementation.

    Firmware protocol:
    - Command: CA:<potential>:<duration>:<sample_interval>
    - Data format: DATA:<vramp>,<adc>
    - Completion: "CA complete."
    """

    def __init__(self):
        super().__init__()
        self.experiment_name = "Chronoamperometry"

        # Hardware calibration
        self.tia_resistance = 10000
        self.vref = 1.0
        self.adc_max = 32767
        self.adc_vref = 4.096

        # Data processing
        self.offset_current = 0.0
        self.applied_potential = 0.0
        self._data_started = False

    def get_name(self) -> str:
        return self.experiment_name

    def get_parameters(self) -> Dict[str, Any]:
        return {
            'potential': {
                'type': float, 'default': 0.0, 'min': -0.2, 'max': 1.5,
                'unit': 'V', 'description': 'Applied potential'
            },
            'duration': {
                'type': float, 'default': 10.0, 'min': 0.1, 'max': 300.0,
                'unit': 's', 'description': 'Measurement duration'
            },
            'sample_interval': {
                'type': float, 'default': 0.1, 'min': 0.01, 'max': 10.0,
                'unit': 's', 'description': 'Sampling interval'
            },
            'offset_current': {
                'type': float, 'default': 0.0, 'min': -1000, 'max': 1000,
                'unit': 'µA', 'description': 'Offset current for baseline correction'
            }
        }

    def validate_parameters(self, params: Dict[str, Any]) -> bool:
        schema = self.get_parameters()
        for key in ['potential', 'duration']:
            if key not in params:
                raise ValueError(f"Missing required parameter: {key}")
        for key, value in params.items():
            if key not in schema:
                continue
            param_def = schema[key]
            if not isinstance(value, param_def['type']):
                raise ValueError(f"{key} must be {param_def['type'].__name__}")
            if 'min' in param_def and value < param_def['min']:
                raise ValueError(f"{key} = {value} below minimum {param_def['min']}")
            if 'max' in param_def and value > param_def['max']:
                raise ValueError(f"{key} = {value} above maximum {param_def['max']}")
        if 'sample_interval' in params and 'duration' in params:
            if params['sample_interval'] >= params['duration']:
                raise ValueError("Sample interval must be less than duration")
        return True

    def generate_command(self, params: Dict[str, Any]) -> str:
        self.applied_potential = params['potential']
        return (
            f"CA:{params['potential']}:"
            f"{params['duration']}:"
            f"{params.get('sample_interval', 0.1)}"
        )

    def process_data_point(self, raw_data: str) -> Optional[Dict[str, float]]:
        line = raw_data.strip()

        if line == "CA complete." or line == "CV complete.":
            self.complete()
            return None

        if line == "START_CONFIRMED":
            self._data_started = True
            return None

        if not self._data_started:
            return None

        if not line.startswith("DATA:"):
            return None

        try:
            parts = line[5:].split(",")
            if len(parts) != 2:
                return None
            applied_voltage = float(parts[0])
            adc_value = int(parts[1])
        except (ValueError, IndexError):
            return None

        if adc_value < 0:
            return None

        from time import time
        if not hasattr(self, '_start_time'):
            self._start_time = time()
        elapsed_time = time() - self._start_time

        v_out = (adc_value / self.adc_max) * self.adc_vref
        current_ua = 1e6 * (2 * self.vref - v_out - applied_voltage) / self.tia_resistance
        current_ua -= self.offset_current

        return {
            'time': elapsed_time,
            'voltage': applied_voltage,
            'current': current_ua
        }

    def on_configured(self):
        if 'offset_current' in self.parameters:
            self.offset_current = self.parameters['offset_current']
        if 'potential' in self.parameters:
            self.applied_potential = self.parameters['potential']

    def on_started(self):
        self._data_started = False
        if hasattr(self, '_start_time'):
            delattr(self, '_start_time')

    def load_calibration(self, calibration: Dict[str, float]):
        self.offset_current = calibration.get('offset_current', 0.0)
        self.tia_resistance = calibration.get('tia_resistance', 10000)
        self.vref = calibration.get('vref', 1.0)

    def get_plot_config(self) -> Dict[str, str]:
        return {
            'x_label': 'Time (s)',
            'y_label': 'Current (µA)',
            'title': f'Chronoamperometry at {self.applied_potential:.3f} V',
            'x_data': 'time',
            'y_data': 'current'
        }
