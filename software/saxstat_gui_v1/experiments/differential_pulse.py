"""
Differential Pulse Voltammetry Experiment

Measures differential current from paired baseline/pulse measurements.
"""

from typing import Dict, Any, Optional
from .base_experiment import BaseExperiment
from .experiment_registry import register_experiment


@register_experiment
class DifferentialPulseVoltammetry(BaseExperiment):
    """
    Differential Pulse Voltammetry (DPV) experiment implementation.

    Firmware protocol:
    - Command: DPV:<start_v>:<end_v>:<step>:<pulse>:<period>:<width>
    - Data format: DATA:<vramp>,<adc> (alternating baseline/pulse pairs)
    - Completion: "DPV complete."

    Firmware sends paired measurements per step:
    1. Baseline measurement at base voltage
    2. Pulse measurement at base + pulse_amplitude
    The GUI pairs consecutive DATA lines and computes differential current.
    """

    def __init__(self):
        super().__init__()
        self.experiment_name = "Differential Pulse Voltammetry"

        # Hardware calibration
        self.tia_resistance = 10000
        self.vref = 1.0
        self.adc_max = 32767
        self.adc_vref = 4.096

        # Data processing
        self.offset_current = 0.0
        self._data_started = False
        self._baseline_point = None  # stores parsed baseline awaiting pulse

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
            'step_height': {
                'type': float, 'default': 0.004, 'min': 0.001, 'max': 0.01,
                'unit': 'V', 'description': 'Potential step height'
            },
            'pulse_amplitude': {
                'type': float, 'default': 0.05, 'min': 0.001, 'max': 0.1,
                'unit': 'V', 'description': 'Pulse amplitude'
            },
            'pulse_period': {
                'type': float, 'default': 0.5, 'min': 0.1, 'max': 5.0,
                'unit': 's', 'description': 'Time between pulses'
            },
            'pulse_width': {
                'type': float, 'default': 0.05, 'min': 0.01, 'max': 0.5,
                'unit': 's', 'description': 'Duration of pulse'
            },
            'offset_current': {
                'type': float, 'default': 0.0, 'min': -1000, 'max': 1000,
                'unit': 'µA', 'description': 'Offset current for baseline correction'
            }
        }

    def validate_parameters(self, params: Dict[str, Any]) -> bool:
        schema = self.get_parameters()
        required = ['start_voltage', 'end_voltage', 'step_height',
                     'pulse_amplitude', 'pulse_period', 'pulse_width']
        for key in required:
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
        if params['pulse_width'] >= params['pulse_period']:
            raise ValueError("Pulse width must be less than pulse period")
        if params['pulse_amplitude'] < params['step_height']:
            raise ValueError("Pulse amplitude should be at least equal to step height")
        return True

    def generate_command(self, params: Dict[str, Any]) -> str:
        return (
            f"DPV:{params['start_voltage']}:"
            f"{params['end_voltage']}:"
            f"{params['step_height']}:"
            f"{params['pulse_amplitude']}:"
            f"{params['pulse_period']}:"
            f"{params['pulse_width']}"
        )

    def _adc_to_current(self, applied_voltage: float, adc_value: int) -> float:
        v_out = (adc_value / self.adc_max) * self.adc_vref
        current_ua = 1e6 * (2 * self.vref - v_out - applied_voltage) / self.tia_resistance
        current_ua -= self.offset_current
        return current_ua

    def process_data_point(self, raw_data: str) -> Optional[Dict[str, float]]:
        line = raw_data.strip()

        if line == "DPV complete." or line == "CV complete.":
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

        current_ua = self._adc_to_current(applied_voltage, adc_value)

        # DPV firmware sends alternating baseline/pulse pairs
        if self._baseline_point is None:
            # This is the baseline measurement
            self._baseline_point = {
                'voltage': applied_voltage,
                'current': current_ua
            }
            return None
        else:
            # This is the pulse measurement - compute differential
            baseline = self._baseline_point
            self._baseline_point = None

            from time import time
            if not hasattr(self, '_start_time'):
                self._start_time = time()
            elapsed_time = time() - self._start_time

            differential = current_ua - baseline['current']

            return {
                'time': elapsed_time,
                'voltage': baseline['voltage'],  # base voltage for x-axis
                'current': differential,
                'baseline_current': baseline['current'],
                'pulse_current': current_ua
            }

    def on_configured(self):
        if 'offset_current' in self.parameters:
            self.offset_current = self.parameters['offset_current']

    def on_started(self):
        self._data_started = False
        self._baseline_point = None
        if hasattr(self, '_start_time'):
            delattr(self, '_start_time')

    def load_calibration(self, calibration: Dict[str, float]):
        self.offset_current = calibration.get('offset_current', 0.0)
        self.tia_resistance = calibration.get('tia_resistance', 10000)
        self.vref = calibration.get('vref', 1.0)

    def get_plot_config(self) -> Dict[str, str]:
        return {
            'x_label': 'Applied Voltage (V)',
            'y_label': 'Differential Current (µA)',
            'title': 'Differential Pulse Voltammogram',
            'x_data': 'voltage',
            'y_data': 'current'
        }
