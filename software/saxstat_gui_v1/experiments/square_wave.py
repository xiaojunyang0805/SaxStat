"""
Square Wave Voltammetry Experiment

Measures differential current from paired forward/reverse pulse measurements.
"""

from typing import Dict, Any, Optional
from .base_experiment import BaseExperiment
from .experiment_registry import register_experiment


@register_experiment
class SquareWaveVoltammetry(BaseExperiment):
    """
    Square Wave Voltammetry (SWV) experiment implementation.

    Firmware protocol:
    - Command: SWV:<start_v>:<end_v>:<step>:<pulse>:<freq>
    - Data format: DATA:<vramp>,<adc> (alternating forward/reverse pairs)
    - Completion: "SWV complete."

    Firmware sends paired measurements per step:
    1. Forward pulse (base + amplitude)
    2. Reverse pulse (base - amplitude)
    The GUI pairs consecutive DATA lines and computes differential current.
    """

    def __init__(self):
        super().__init__()
        self.experiment_name = "Square Wave Voltammetry"

        # Hardware calibration
        self.tia_resistance = 10000
        self.vref = 1.0
        self.adc_max = 32767
        self.adc_vref = 4.096

        # Data processing
        self.offset_current = 0.0
        self._data_started = False
        self._forward_point = None  # stores parsed forward awaiting reverse

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
                'unit': 'V', 'description': 'Staircase step height'
            },
            'pulse_amplitude': {
                'type': float, 'default': 0.025, 'min': 0.001, 'max': 0.1,
                'unit': 'V', 'description': 'Square wave pulse amplitude'
            },
            'frequency': {
                'type': float, 'default': 15.0, 'min': 1.0, 'max': 100.0,
                'unit': 'Hz', 'description': 'Square wave frequency'
            },
            'offset_current': {
                'type': float, 'default': 0.0, 'min': -1000, 'max': 1000,
                'unit': 'µA', 'description': 'Offset current for baseline correction'
            }
        }

    def validate_parameters(self, params: Dict[str, Any]) -> bool:
        schema = self.get_parameters()
        for key in ['start_voltage', 'end_voltage', 'step_height', 'pulse_amplitude', 'frequency']:
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
        if params['pulse_amplitude'] < params['step_height']:
            raise ValueError("Pulse amplitude should be larger than step height")
        return True

    def generate_command(self, params: Dict[str, Any]) -> str:
        return (
            f"SWV:{params['start_voltage']}:"
            f"{params['end_voltage']}:"
            f"{params['step_height']}:"
            f"{params['pulse_amplitude']}:"
            f"{params['frequency']}"
        )

    def _adc_to_current(self, applied_voltage: float, adc_value: int) -> float:
        v_out = (adc_value / self.adc_max) * self.adc_vref
        current_ua = 1e6 * (2 * self.vref - v_out - applied_voltage) / self.tia_resistance
        current_ua -= self.offset_current
        return current_ua

    def process_data_point(self, raw_data: str) -> Optional[Dict[str, float]]:
        line = raw_data.strip()

        if line == "SWV complete." or line == "CV complete.":
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

        # SWV firmware sends alternating forward/reverse pairs
        if self._forward_point is None:
            # This is the forward pulse measurement
            self._forward_point = {
                'voltage': applied_voltage,
                'current': current_ua
            }
            return None
        else:
            # This is the reverse pulse measurement - compute differential
            forward = self._forward_point
            self._forward_point = None

            from time import time
            if not hasattr(self, '_start_time'):
                self._start_time = time()
            elapsed_time = time() - self._start_time

            # Base voltage is midpoint between forward and reverse pulse voltages
            base_voltage = (forward['voltage'] + applied_voltage) / 2.0
            differential = forward['current'] - current_ua

            return {
                'time': elapsed_time,
                'voltage': base_voltage,
                'current': differential,
                'forward_current': forward['current'],
                'reverse_current': current_ua
            }

    def on_configured(self):
        if 'offset_current' in self.parameters:
            self.offset_current = self.parameters['offset_current']

    def on_started(self):
        self._data_started = False
        self._forward_point = None
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
            'title': 'Square Wave Voltammogram',
            'x_data': 'voltage',
            'y_data': 'current'
        }
