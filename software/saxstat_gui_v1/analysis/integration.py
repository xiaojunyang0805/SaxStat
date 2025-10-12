"""
Data Integration

Numerical integration for charge calculation and peak area analysis.
"""

import numpy as np
from scipy.integrate import simpson, trapezoid
from typing import Tuple, Optional


class DataIntegrator:
    """
    Numerical integration for electrochemical data.

    Features:
    - Trapezoidal integration
    - Simpson's rule integration
    - Charge calculation from current
    - Peak area calculation
    - Time-range integration
    """

    def __init__(self):
        self.last_integral: Optional[float] = None
        self.last_method: Optional[str] = None

    def integrate_trapz(self,
                       x_data: np.ndarray,
                       y_data: np.ndarray) -> float:
        """
        Integrate using trapezoidal rule.

        Args:
            x_data: X-axis data (time or voltage)
            y_data: Y-axis data (current)

        Returns:
            float: Integrated value
        """
        if len(x_data) != len(y_data):
            raise ValueError("x_data and y_data must have same length")

        if len(x_data) < 2:
            raise ValueError("Need at least 2 data points for integration")

        self.last_integral = trapezoid(y_data, x_data)
        self.last_method = 'trapz'

        return self.last_integral

    def integrate_simpson(self,
                         x_data: np.ndarray,
                         y_data: np.ndarray) -> float:
        """
        Integrate using Simpson's rule (more accurate for smooth data).

        Args:
            x_data: X-axis data (time or voltage)
            y_data: Y-axis data (current)

        Returns:
            float: Integrated value
        """
        if len(x_data) != len(y_data):
            raise ValueError("x_data and y_data must have same length")

        if len(x_data) < 3:
            raise ValueError("Need at least 3 data points for Simpson's rule")

        self.last_integral = simpson(y_data, x=x_data)
        self.last_method = 'simpson'

        return self.last_integral

    def integrate_range(self,
                       x_data: np.ndarray,
                       y_data: np.ndarray,
                       x_start: float,
                       x_end: float,
                       method: str = 'trapz') -> float:
        """
        Integrate data within a specified range.

        Args:
            x_data: X-axis data
            y_data: Y-axis data
            x_start: Start of integration range
            x_end: End of integration range
            method: Integration method ('trapz' or 'simpson')

        Returns:
            float: Integrated value
        """
        if len(x_data) != len(y_data):
            raise ValueError("x_data and y_data must have same length")

        # Find indices within range
        mask = (x_data >= x_start) & (x_data <= x_end)
        x_range = x_data[mask]
        y_range = y_data[mask]

        if len(x_range) < 2:
            raise ValueError("Not enough data points in specified range")

        # Integrate
        if method == 'trapz':
            return self.integrate_trapz(x_range, y_range)
        elif method == 'simpson':
            return self.integrate_simpson(x_range, y_range)
        else:
            raise ValueError(f"Unknown method: {method}")

    def calculate_charge(self,
                        time_data: np.ndarray,
                        current_data: np.ndarray,
                        method: str = 'trapz') -> float:
        """
        Calculate total charge from current vs time data.

        Q = ∫ I(t) dt

        Args:
            time_data: Time data in seconds
            current_data: Current data in amperes
            method: Integration method ('trapz' or 'simpson')

        Returns:
            float: Charge in coulombs (C)
        """
        if method == 'trapz':
            charge = self.integrate_trapz(time_data, current_data)
        elif method == 'simpson':
            charge = self.integrate_simpson(time_data, current_data)
        else:
            raise ValueError(f"Unknown method: {method}")

        return charge

    def calculate_peak_area(self,
                           x_data: np.ndarray,
                           y_data: np.ndarray,
                           peak_index: int,
                           width: int = 10,
                           method: str = 'trapz') -> float:
        """
        Calculate area under a specific peak.

        Args:
            x_data: X-axis data
            y_data: Y-axis data
            peak_index: Index of peak center
            width: Number of points on each side of peak to include
            method: Integration method ('trapz' or 'simpson')

        Returns:
            float: Peak area
        """
        # Define peak range
        start_idx = max(0, peak_index - width)
        end_idx = min(len(x_data), peak_index + width + 1)

        x_peak = x_data[start_idx:end_idx]
        y_peak = y_data[start_idx:end_idx]

        # Calculate baseline (linear between endpoints)
        baseline = np.linspace(y_peak[0], y_peak[-1], len(y_peak))

        # Subtract baseline
        y_corrected = y_peak - baseline

        # Integrate
        if method == 'trapz':
            return self.integrate_trapz(x_peak, y_corrected)
        elif method == 'simpson':
            return self.integrate_simpson(x_peak, y_corrected)
        else:
            raise ValueError(f"Unknown method: {method}")

    def calculate_cumulative_charge(self,
                                   time_data: np.ndarray,
                                   current_data: np.ndarray) -> np.ndarray:
        """
        Calculate cumulative charge over time.

        Args:
            time_data: Time data in seconds
            current_data: Current data in amperes

        Returns:
            ndarray: Cumulative charge at each time point (coulombs)
        """
        if len(time_data) != len(current_data):
            raise ValueError("time_data and current_data must have same length")

        # Calculate cumulative integral using trapezoidal rule
        cumulative = np.zeros(len(time_data))

        for i in range(1, len(time_data)):
            dt = time_data[i] - time_data[i-1]
            avg_current = (current_data[i] + current_data[i-1]) / 2
            cumulative[i] = cumulative[i-1] + avg_current * dt

        return cumulative

    def get_last_integral(self) -> Optional[float]:
        """
        Get the last calculated integral value.

        Returns:
            float or None: Last integral if available
        """
        return self.last_integral

    def get_statistics(self,
                      time_data: np.ndarray,
                      current_data: np.ndarray) -> dict:
        """
        Calculate integration statistics.

        Args:
            time_data: Time data in seconds
            current_data: Current data in amperes

        Returns:
            dict: Statistics including total charge, average current, etc.
        """
        # Total charge
        total_charge = self.calculate_charge(time_data, current_data, method='trapz')

        # Time duration
        duration = time_data[-1] - time_data[0]

        # Average current
        avg_current = np.mean(current_data)

        # Peak current
        max_current = np.max(np.abs(current_data))

        return {
            'total_charge': total_charge,
            'duration': duration,
            'average_current': avg_current,
            'peak_current': max_current,
            'charge_per_time': total_charge / duration if duration > 0 else 0
        }
