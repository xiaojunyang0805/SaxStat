"""
Baseline Correction

Methods for baseline correction and background subtraction in electrochemical data.
"""

import numpy as np
from scipy.interpolate import UnivariateSpline
from scipy.optimize import curve_fit
from typing import Optional, Tuple


class BaselineCorrector:
    """
    Baseline correction for electrochemical data.

    Features:
    - Polynomial baseline fitting
    - Spline interpolation baseline
    - Linear baseline correction
    - Background subtraction
    """

    def __init__(self):
        self.baseline: Optional[np.ndarray] = None
        self.corrected_data: Optional[np.ndarray] = None

    def fit_polynomial(self,
                      x_data: np.ndarray,
                      y_data: np.ndarray,
                      degree: int = 2) -> np.ndarray:
        """
        Fit polynomial baseline to data.

        Args:
            x_data: X-axis data
            y_data: Y-axis data
            degree: Polynomial degree (default: 2 for quadratic)

        Returns:
            ndarray: Baseline values
        """
        if len(x_data) != len(y_data):
            raise ValueError("x_data and y_data must have same length")

        if len(x_data) < degree + 1:
            raise ValueError(f"Need at least {degree + 1} data points for degree {degree} polynomial")

        # Fit polynomial
        coeffs = np.polyfit(x_data, y_data, degree)
        self.baseline = np.polyval(coeffs, x_data)

        return self.baseline

    def fit_spline(self,
                  x_data: np.ndarray,
                  y_data: np.ndarray,
                  smoothing: float = None,
                  degree: int = 3) -> np.ndarray:
        """
        Fit spline baseline to data.

        Args:
            x_data: X-axis data
            y_data: Y-axis data
            smoothing: Smoothing factor (None for interpolating spline)
            degree: Spline degree (default: 3 for cubic)

        Returns:
            ndarray: Baseline values
        """
        if len(x_data) != len(y_data):
            raise ValueError("x_data and y_data must have same length")

        if len(x_data) < degree + 1:
            raise ValueError(f"Need at least {degree + 1} data points for degree {degree} spline")

        # Auto-calculate smoothing if not provided
        if smoothing is None:
            smoothing = len(x_data) * 0.01  # 1% of data points

        # Fit spline
        spline = UnivariateSpline(x_data, y_data, s=smoothing, k=degree)
        self.baseline = spline(x_data)

        return self.baseline

    def fit_linear(self,
                  x_data: np.ndarray,
                  y_data: np.ndarray,
                  start_points: int = 10,
                  end_points: int = 10) -> np.ndarray:
        """
        Fit linear baseline using start and end points.

        Args:
            x_data: X-axis data
            y_data: Y-axis data
            start_points: Number of points at start to use for baseline
            end_points: Number of points at end to use for baseline

        Returns:
            ndarray: Baseline values
        """
        if len(x_data) != len(y_data):
            raise ValueError("x_data and y_data must have same length")

        if len(x_data) < start_points + end_points:
            raise ValueError("Not enough data points for baseline fitting")

        # Get start and end segments
        x_baseline = np.concatenate([x_data[:start_points], x_data[-end_points:]])
        y_baseline = np.concatenate([y_data[:start_points], y_data[-end_points:]])

        # Fit linear baseline
        coeffs = np.polyfit(x_baseline, y_baseline, 1)
        self.baseline = np.polyval(coeffs, x_data)

        return self.baseline

    def fit_endpoints(self,
                     x_data: np.ndarray,
                     y_data: np.ndarray) -> np.ndarray:
        """
        Fit linear baseline using only first and last points.

        Args:
            x_data: X-axis data
            y_data: Y-axis data

        Returns:
            ndarray: Baseline values
        """
        if len(x_data) < 2:
            raise ValueError("Need at least 2 data points")

        # Calculate slope and intercept
        slope = (y_data[-1] - y_data[0]) / (x_data[-1] - x_data[0])
        intercept = y_data[0] - slope * x_data[0]

        self.baseline = slope * x_data + intercept

        return self.baseline

    def correct(self,
               x_data: np.ndarray,
               y_data: np.ndarray,
               method: str = 'polynomial',
               **kwargs) -> Tuple[np.ndarray, np.ndarray]:
        """
        Apply baseline correction to data.

        Args:
            x_data: X-axis data
            y_data: Y-axis data
            method: Correction method ('polynomial', 'spline', 'linear', 'endpoints')
            **kwargs: Additional arguments for fitting method

        Returns:
            tuple: (baseline, corrected_data)
        """
        if method == 'polynomial':
            degree = kwargs.get('degree', 2)
            baseline = self.fit_polynomial(x_data, y_data, degree)
        elif method == 'spline':
            smoothing = kwargs.get('smoothing', None)
            degree = kwargs.get('degree', 3)
            baseline = self.fit_spline(x_data, y_data, smoothing, degree)
        elif method == 'linear':
            start_points = kwargs.get('start_points', 10)
            end_points = kwargs.get('end_points', 10)
            baseline = self.fit_linear(x_data, y_data, start_points, end_points)
        elif method == 'endpoints':
            baseline = self.fit_endpoints(x_data, y_data)
        else:
            raise ValueError(f"Unknown method: {method}")

        # Subtract baseline
        self.corrected_data = y_data - baseline

        return baseline, self.corrected_data

    def subtract_background(self,
                          y_data: np.ndarray,
                          background: np.ndarray) -> np.ndarray:
        """
        Subtract a background signal from data.

        Args:
            y_data: Y-axis data
            background: Background signal to subtract

        Returns:
            ndarray: Corrected data
        """
        if len(y_data) != len(background):
            raise ValueError("y_data and background must have same length")

        self.corrected_data = y_data - background

        return self.corrected_data

    def get_corrected_data(self) -> Optional[np.ndarray]:
        """
        Get the last corrected data.

        Returns:
            ndarray or None: Corrected data if available
        """
        return self.corrected_data

    def get_baseline(self) -> Optional[np.ndarray]:
        """
        Get the last calculated baseline.

        Returns:
            ndarray or None: Baseline if available
        """
        return self.baseline
