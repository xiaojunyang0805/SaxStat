"""
Experiments Module - Electrochemical experiment implementations.

This module contains the base experiment class and specific implementations
for different electrochemical techniques (CV, LSV, CA, SWV, DPV, etc.).
"""

from .base_experiment import BaseExperiment, ExperimentState
from .experiment_registry import ExperimentRegistry, get_registry, register_experiment

# Phase 2 experiments (basic techniques)
from .cyclic_voltammetry import CyclicVoltammetry
from .linear_sweep import LinearSweepVoltammetry
from .chronoamperometry import Chronoamperometry

# Phase 5 experiments (advanced techniques)
from .square_wave import SquareWaveVoltammetry
from .differential_pulse import DifferentialPulseVoltammetry
from .normal_pulse import NormalPulseVoltammetry
from .potentiometry import Potentiometry

__all__ = [
    'BaseExperiment',
    'ExperimentState',
    'ExperimentRegistry',
    'get_registry',
    'register_experiment',
    # Phase 2 experiments
    'CyclicVoltammetry',
    'LinearSweepVoltammetry',
    'Chronoamperometry',
    # Phase 5 experiments
    'SquareWaveVoltammetry',
    'DifferentialPulseVoltammetry',
    'NormalPulseVoltammetry',
    'Potentiometry'
]
