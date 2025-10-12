"""
Data Analysis Module

Provides tools for post-processing electrochemical data:
- Peak detection
- Baseline correction
- Integration/charge calculation
- Smoothing filters
"""

from .peak_detection import PeakDetector
from .baseline_correction import BaselineCorrector
from .integration import DataIntegrator
from .smoothing import DataSmoother

__all__ = [
    'PeakDetector',
    'BaselineCorrector',
    'DataIntegrator',
    'DataSmoother',
]
