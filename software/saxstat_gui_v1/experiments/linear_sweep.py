"""
Linear Sweep Voltammetry Experiment

Measures current response during a single linear potential sweep.
"""

from typing import Dict, Any, Optional
from .base_experiment import BaseExperiment
from .experiment_registry import register_experiment


@register_experiment
class LinearSweepVoltammetry(BaseExperiment):
    """
    Linear Sweep Voltammetry (LSV) experiment implementation.

    Firmware protocol:
    - Command: LSV:<start_v>:<end_v>:<scan_rate>
    - Data format: DATA:<vramp>,<adc>
    - Completion: "LSV complete."
    """

    def __init__(self):
        super().__init__()
        self.experiment_name = "Linear Sweep Voltammetry"

        # Hardware calibration
        self.tia_resistance = 10000
        self.vref = 1.0
        self.adc_max = 32767
        self.adc_vref = 4.096

        # Data processing
        self.offset_current = 0.0
        self._data_started = False

    def get_name(self) -> str:
        return self.experiment_name

    def get_parameters(self) -> Dict[str, Any]:
        return {
            'start_voltage': {
                'type': float, 'default': -0.2, 'min': -0.2, 'max': 1.5,
                'unit': 'V', 'description': 'Starting voltage'
            },
            'end_voltage': {
                'type': float, 'default': 0.5, 'min': -0.2, 'max': 1.5,
                'unit': 'V', 'description': 'End voltage'
            },
            'scan_rate': {
                'type': float, 'default': 0.05, 'min': 0.01, 'max': 0.2,
                'unit': 'V/s', 'description': 'Scan rate'
            },
            'offset_current': {
                'type': float, 'default': 0.0, 'min': -1000, 'max': 1000,
                'unit': 'µA', 'description': 'Offset current for baseline correction'
            }
        }

    def validate_parameters(self, params: Dict[str, Any]) -> bool:
        schema = self.get_parameters()
        for key in ['start_voltage', 'end_voltage', 'scan_rate']:
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
        if params['start_voltage'] == params['end_voltage']:
            raise ValueError("Start and end voltages cannot be equal")
        return True

    def generate_command(self, params: Dict[str, Any]) -> str:
        return (
            f"LSV:{params['start_voltage']}:"
            f"{params['end_voltage']}:"
            f"{params['scan_rate']}"
        )

    def process_data_point(self, raw_data: str) -> Optional[Dict[str, float]]:
        line = raw_data.strip()

        if line == "LSV complete." or line == "CV complete.":
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
            'x_label': 'Applied Voltage (V)',
            'y_label': 'Current (µA)',
            'title': 'Linear Sweep Voltammogram',
            'x_data': 'voltage',
            'y_data': 'current'
        }
