"""
Experiments Module - Electrochemical experiment implementations.

This module contains the base experiment class and specific implementations
for different electrochemical techniques (CV, LSV, CA, etc.).
"""

from .base_experiment import BaseExperiment, ExperimentState
from .experiment_registry import ExperimentRegistry, get_registry, register_experiment
from .cyclic_voltammetry import CyclicVoltammetry

__all__ = [
    'BaseExperiment',
    'ExperimentState',
    'ExperimentRegistry',
    'get_registry',
    'register_experiment',
    'CyclicVoltammetry'
]
