"""
Data Smoothing

Filters for noise reduction and smoothing of electrochemical data.
"""

import numpy as np
from scipy.signal import savgol_filter
from scipy.ndimage import uniform_filter1d
from typing import Optional


class DataSmoother:
    """
    Data smoothing and noise reduction.

    Features:
    - Savitzky-Golay filter (preserves peaks)
    - Moving average filter
    - Exponential moving average
    - Gaussian smoothing
    """

    def __init__(self):
        self.smoothed_data: Optional[np.ndarray] = None
        self.last_method: Optional[str] = None

    def savitzky_golay(self,
                      y_data: np.ndarray,
                      window_length: int = 11,
                      polyorder: int = 3) -> np.ndarray:
        """
        Apply Savitzky-Golay filter (preserves peak shapes).

        Args:
            y_data: Y-axis data to smooth
            window_length: Length of filter window (must be odd)
            polyorder: Polynomial order (must be less than window_length)

        Returns:
            ndarray: Smoothed data
        """
        if len(y_data) < window_length:
            raise ValueError(f"Data length ({len(y_data)}) must be >= window_length ({window_length})")

        if window_length % 2 == 0:
            window_length += 1  # Make odd

        if polyorder >= window_length:
            polyorder = window_length - 1

        self.smoothed_data = savgol_filter(y_data, window_length, polyorder)
        self.last_method = 'savitzky_golay'

        return self.smoothed_data

    def moving_average(self,
                      y_data: np.ndarray,
                      window_size: int = 5) -> np.ndarray:
        """
        Apply simple moving average filter.

        Args:
            y_data: Y-axis data to smooth
            window_size: Size of moving window

        Returns:
            ndarray: Smoothed data
        """
        if len(y_data) < window_size:
            raise ValueError(f"Data length ({len(y_data)}) must be >= window_size ({window_size})")

        # Use uniform_filter1d for efficient moving average
        self.smoothed_data = uniform_filter1d(y_data, size=window_size, mode='nearest')
        self.last_method = 'moving_average'

        return self.smoothed_data

    def exponential_moving_average(self,
                                  y_data: np.ndarray,
                                  alpha: float = 0.3) -> np.ndarray:
        """
        Apply exponential moving average (more weight on recent data).

        Args:
            y_data: Y-axis data to smooth
            alpha: Smoothing factor (0 < alpha <= 1)
                  Higher alpha = less smoothing

        Returns:
            ndarray: Smoothed data
        """
        if not 0 < alpha <= 1:
            raise ValueError("alpha must be between 0 and 1")

        smoothed = np.zeros_like(y_data)
        smoothed[0] = y_data[0]

        for i in range(1, len(y_data)):
            smoothed[i] = alpha * y_data[i] + (1 - alpha) * smoothed[i-1]

        self.smoothed_data = smoothed
        self.last_method = 'exponential_moving_average'

        return self.smoothed_data

    def gaussian_smooth(self,
                       y_data: np.ndarray,
                       sigma: float = 2.0) -> np.ndarray:
        """
        Apply Gaussian smoothing.

        Args:
            y_data: Y-axis data to smooth
            sigma: Standard deviation of Gaussian kernel

        Returns:
            ndarray: Smoothed data
        """
        from scipy.ndimage import gaussian_filter1d

        self.smoothed_data = gaussian_filter1d(y_data, sigma=sigma)
        self.last_method = 'gaussian'

        return self.smoothed_data

    def smooth(self,
              y_data: np.ndarray,
              method: str = 'savitzky_golay',
              **kwargs) -> np.ndarray:
        """
        Apply smoothing using specified method.

        Args:
            y_data: Y-axis data to smooth
            method: Smoothing method ('savitzky_golay', 'moving_average',
                   'exponential', 'gaussian')
            **kwargs: Additional arguments for smoothing method

        Returns:
            ndarray: Smoothed data
        """
        if method == 'savitzky_golay':
            window_length = kwargs.get('window_length', 11)
            polyorder = kwargs.get('polyorder', 3)
            return self.savitzky_golay(y_data, window_length, polyorder)

        elif method == 'moving_average':
            window_size = kwargs.get('window_size', 5)
            return self.moving_average(y_data, window_size)

        elif method == 'exponential':
            alpha = kwargs.get('alpha', 0.3)
            return self.exponential_moving_average(y_data, alpha)

        elif method == 'gaussian':
            sigma = kwargs.get('sigma', 2.0)
            return self.gaussian_smooth(y_data, sigma)

        else:
            raise ValueError(f"Unknown method: {method}")

    def denoise(self,
               y_data: np.ndarray,
               level: str = 'medium') -> np.ndarray:
        """
        Quick denoise with preset parameters.

        Args:
            y_data: Y-axis data to denoise
            level: Denoising level ('light', 'medium', 'heavy')

        Returns:
            ndarray: Denoised data
        """
        if level == 'light':
            return self.savitzky_golay(y_data, window_length=7, polyorder=3)
        elif level == 'medium':
            return self.savitzky_golay(y_data, window_length=11, polyorder=3)
        elif level == 'heavy':
            return self.savitzky_golay(y_data, window_length=15, polyorder=2)
        else:
            raise ValueError(f"Unknown level: {level}. Use 'light', 'medium', or 'heavy'")

    def get_smoothed_data(self) -> Optional[np.ndarray]:
        """
        Get the last smoothed data.

        Returns:
            ndarray or None: Smoothed data if available
        """
        return self.smoothed_data

    def compare_methods(self,
                       y_data: np.ndarray) -> dict:
        """
        Apply multiple smoothing methods for comparison.

        Args:
            y_data: Y-axis data to smooth

        Returns:
            dict: Dictionary of smoothed data for each method
        """
        results = {}

        try:
            results['savitzky_golay'] = self.savitzky_golay(y_data.copy())
        except Exception as e:
            results['savitzky_golay'] = None

        try:
            results['moving_average'] = self.moving_average(y_data.copy())
        except Exception as e:
            results['moving_average'] = None

        try:
            results['exponential'] = self.exponential_moving_average(y_data.copy())
        except Exception as e:
            results['exponential'] = None

        try:
            results['gaussian'] = self.gaussian_smooth(y_data.copy())
        except Exception as e:
            results['gaussian'] = None

        return results
