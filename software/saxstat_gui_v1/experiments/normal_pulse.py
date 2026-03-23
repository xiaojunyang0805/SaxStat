"""
Normal Pulse Voltammetry Experiment

Measures current at end of increasing-amplitude pulses from a baseline potential.
"""

from typing import Dict, Any, Optional
from .base_experiment import BaseExperiment
from .experiment_registry import register_experiment


@register_experiment
class NormalPulseVoltammetry(BaseExperiment):
    """
    Normal Pulse Voltammetry (NPV) experiment implementation.

    Firmware protocol:
    - Command: NPV:<baseline>:<start_v>:<end_v>:<step>:<period>:<width>
    - Data format: DATA:<vramp>,<adc> (alternating baseline/pulse pairs)
    - Completion: "NPV complete."

    Firmware sends paired measurements per step:
    1. Baseline measurement at baseline potential
    2. Pulse measurement at pulse potential
    The GUI pairs consecutive DATA lines; the pulse current is the primary result.
    """

    def __init__(self):
        super().__init__()
        self.experiment_name = "Normal Pulse Voltammetry"

        # Hardware calibration
        self.tia_resistance = 10000
        self.vref = 1.0
        self.adc_max = 32767
        self.adc_vref = 4.096

        # Data processing
        self.offset_current = 0.0
        self.baseline_potential = 0.0
        self._data_started = False
        self._baseline_point = None

    def get_name(self) -> str:
        return self.experiment_name

    def get_parameters(self) -> Dict[str, Any]:
        return {
            'baseline_potential': {
                'type': float, 'default': 0.0, 'min': -0.2, 'max': 1.5,
                'unit': 'V', 'description': 'Baseline potential (between pulses)'
            },
            'start_voltage': {
                'type': float, 'default': -0.2, 'min': -0.2, 'max': 1.5,
                'unit': 'V', 'description': 'Starting pulse voltage'
            },
            'end_voltage': {
                'type': float, 'default': 0.5, 'min': -0.2, 'max': 1.5,
                'unit': 'V', 'description': 'End pulse voltage'
            },
            'step_height': {
                'type': float, 'default': 0.005, 'min': 0.001, 'max': 0.01,
                'unit': 'V', 'description': 'Pulse height increment'
            },
            'pulse_period': {
                'type': float, 'default': 1.0, 'min': 0.1, 'max': 10.0,
                'unit': 's', 'description': 'Time between pulses'
            },
            'pulse_width': {
                'type': float, 'default': 0.05, 'min': 0.01, 'max': 1.0,
                'unit': 's', 'description': 'Duration of pulse'
            },
            'offset_current': {
                'type': float, 'default': 0.0, 'min': -1000, 'max': 1000,
                'unit': 'µA', 'description': 'Offset current for baseline correction'
            }
        }

    def validate_parameters(self, params: Dict[str, Any]) -> bool:
        schema = self.get_parameters()
        required = ['baseline_potential', 'start_voltage', 'end_voltage',
                     'step_height', 'pulse_period', 'pulse_width']
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
        return True

    def generate_command(self, params: Dict[str, Any]) -> str:
        self.baseline_potential = params['baseline_potential']
        return (
            f"NPV:{params['baseline_potential']}:"
            f"{params['start_voltage']}:"
            f"{params['end_voltage']}:"
            f"{params['step_height']}:"
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

        if line == "NPV complete." or line == "CV complete.":
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

        # NPV firmware sends alternating baseline/pulse pairs
        if self._baseline_point is None:
            # This is the baseline measurement
            self._baseline_point = {
                'voltage': applied_voltage,
                'current': current_ua
            }
            return None
        else:
            # This is the pulse measurement
            self._baseline_point = None

            from time import time
            if not hasattr(self, '_start_time'):
                self._start_time = time()
            elapsed_time = time() - self._start_time

            return {
                'time': elapsed_time,
                'voltage': applied_voltage,  # pulse voltage for x-axis
                'current': current_ua
            }

    def on_configured(self):
        if 'offset_current' in self.parameters:
            self.offset_current = self.parameters['offset_current']
        if 'baseline_potential' in self.parameters:
            self.baseline_potential = self.parameters['baseline_potential']

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
            'x_label': 'Pulse Voltage (V)',
            'y_label': 'Current (µA)',
            'title': f'Normal Pulse Voltammogram (baseline: {self.baseline_potential:.3f} V)',
            'x_data': 'voltage',
            'y_data': 'current'
        }
