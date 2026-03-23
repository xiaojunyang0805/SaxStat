"""
Potentiometry Experiment

Open-circuit potential monitoring without applying current.
"""

from typing import Dict, Any, Optional
from .base_experiment import BaseExperiment
from .experiment_registry import register_experiment


@register_experiment
class Potentiometry(BaseExperiment):
    """
    Potentiometry (POT) experiment implementation.

    Firmware protocol:
    - Command: POT:<duration>:<interval>
    - Data format: DATA:0.0000,<adc> (no applied voltage)
    - Completion: "POT complete."

    Measures open-circuit potential over time. No TIA current calculation
    needed since no potential is applied.
    """

    def __init__(self):
        super().__init__()
        self.experiment_name = "Potentiometry"

        # Hardware calibration
        self.adc_max = 32767
        self.adc_vref = 4.096

        # Data processing
        self.offset_voltage = 0.0
        self._data_started = False

    def get_name(self) -> str:
        return self.experiment_name

    def get_parameters(self) -> Dict[str, Any]:
        return {
            'duration': {
                'type': float, 'default': 60.0, 'min': 1.0, 'max': 3600.0,
                'unit': 's', 'description': 'Measurement duration'
            },
            'sample_interval': {
                'type': float, 'default': 1.0, 'min': 0.1, 'max': 60.0,
                'unit': 's', 'description': 'Sampling interval'
            },
            'offset_voltage': {
                'type': float, 'default': 0.0, 'min': -5.0, 'max': 5.0,
                'unit': 'V', 'description': 'Offset voltage for calibration'
            }
        }

    def validate_parameters(self, params: Dict[str, Any]) -> bool:
        schema = self.get_parameters()
        for key in ['duration', 'sample_interval']:
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
        if params['sample_interval'] >= params['duration']:
            raise ValueError("Sample interval must be less than duration")
        return True

    def generate_command(self, params: Dict[str, Any]) -> str:
        return (
            f"POT:{params['duration']}:"
            f"{params['sample_interval']}"
        )

    def process_data_point(self, raw_data: str) -> Optional[Dict[str, float]]:
        line = raw_data.strip()

        if line == "POT complete." or line == "CV complete.":
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
            # vramp field is 0.0 for POT (no applied voltage)
            adc_value = int(parts[1])
        except (ValueError, IndexError):
            return None

        if adc_value < 0:
            return None

        from time import time
        if not hasattr(self, '_start_time'):
            self._start_time = time()
        elapsed_time = time() - self._start_time

        # Convert ADC to measured voltage (direct reading)
        measured_voltage = (adc_value / self.adc_max) * self.adc_vref
        measured_voltage += self.offset_voltage

        return {
            'time': elapsed_time,
            'voltage': measured_voltage,
            'current': 0.0  # Open circuit, no current
        }

    def on_configured(self):
        if 'offset_voltage' in self.parameters:
            self.offset_voltage = self.parameters['offset_voltage']

    def on_started(self):
        self._data_started = False
        if hasattr(self, '_start_time'):
            delattr(self, '_start_time')

    def get_plot_config(self) -> Dict[str, str]:
        return {
            'x_label': 'Time (s)',
            'y_label': 'Potential (V)',
            'title': 'Open Circuit Potential vs Time',
            'x_data': 'time',
            'y_data': 'voltage'
        }
