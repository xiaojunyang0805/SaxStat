"""
Peak Detection

Automatic detection of peaks in electrochemical data using scipy algorithms.
"""

import numpy as np
from scipy.signal import find_peaks
from typing import List, Dict, Tuple, Optional


class PeakDetector:
    """
    Peak detection for electrochemical data.

    Features:
    - Automatic peak finding using scipy.signal.find_peaks
    - Configurable prominence and width thresholds
    - Peak properties (height, prominence, width, area)
    - Support for both anodic and cathodic peaks
    """

    def __init__(self):
        self.peaks_anodic: List[int] = []
        self.peaks_cathodic: List[int] = []
        self.peak_properties_anodic: Dict = {}
        self.peak_properties_cathodic: Dict = {}

    def detect_peaks(self,
                    x_data: np.ndarray,
                    y_data: np.ndarray,
                    prominence: float = None,
                    width: float = None,
                    height: float = None,
                    distance: int = None) -> Dict[str, any]:
        """
        Detect peaks in data.

        Args:
            x_data: X-axis data (voltage or time)
            y_data: Y-axis data (current)
            prominence: Minimum prominence of peaks (default: auto from data range)
            width: Minimum width of peaks in samples
            height: Minimum height of peaks
            distance: Minimum distance between peaks in samples

        Returns:
            dict: Peak information with keys:
                - 'anodic_peaks': indices of anodic peaks
                - 'cathodic_peaks': indices of cathodic peaks
                - 'anodic_properties': properties of anodic peaks
                - 'cathodic_properties': properties of cathodic peaks
        """
        if len(x_data) != len(y_data):
            raise ValueError("x_data and y_data must have same length")

        if len(y_data) < 3:
            return {
                'anodic_peaks': np.array([]),
                'cathodic_peaks': np.array([]),
                'anodic_properties': {},
                'cathodic_properties': {}
            }

        # Auto-calculate prominence if not provided
        if prominence is None:
            prominence = (np.max(y_data) - np.min(y_data)) * 0.1  # 10% of range

        # Detect anodic peaks (positive current)
        self.peaks_anodic, self.peak_properties_anodic = find_peaks(
            y_data,
            prominence=prominence,
            width=width,
            height=height,
            distance=distance
        )

        # Detect cathodic peaks (negative current) by inverting data
        self.peaks_cathodic, self.peak_properties_cathodic = find_peaks(
            -y_data,
            prominence=prominence,
            width=width,
            height=height if height is None else -height,
            distance=distance
        )

        return {
            'anodic_peaks': self.peaks_anodic,
            'cathodic_peaks': self.peaks_cathodic,
            'anodic_properties': self.peak_properties_anodic,
            'cathodic_properties': self.peak_properties_cathodic
        }

    def get_peak_values(self,
                       x_data: np.ndarray,
                       y_data: np.ndarray,
                       peak_type: str = 'anodic') -> List[Tuple[float, float]]:
        """
        Get (x, y) coordinates of detected peaks.

        Args:
            x_data: X-axis data
            y_data: Y-axis data
            peak_type: 'anodic' or 'cathodic'

        Returns:
            list: List of (x, y) tuples for each peak
        """
        if peak_type == 'anodic':
            peaks = self.peaks_anodic
        elif peak_type == 'cathodic':
            peaks = self.peaks_cathodic
        else:
            raise ValueError("peak_type must be 'anodic' or 'cathodic'")

        return [(x_data[i], y_data[i]) for i in peaks]

    def get_peak_currents(self, y_data: np.ndarray, peak_type: str = 'anodic') -> np.ndarray:
        """
        Get peak current values.

        Args:
            y_data: Y-axis data (current)
            peak_type: 'anodic' or 'cathodic'

        Returns:
            ndarray: Array of peak current values
        """
        if peak_type == 'anodic':
            peaks = self.peaks_anodic
        elif peak_type == 'cathodic':
            peaks = self.peaks_cathodic
        else:
            raise ValueError("peak_type must be 'anodic' or 'cathodic'")

        return y_data[peaks] if len(peaks) > 0 else np.array([])

    def get_peak_potentials(self, x_data: np.ndarray, peak_type: str = 'anodic') -> np.ndarray:
        """
        Get peak potential values (for voltammetry).

        Args:
            x_data: X-axis data (voltage)
            peak_type: 'anodic' or 'cathodic'

        Returns:
            ndarray: Array of peak potential values
        """
        if peak_type == 'anodic':
            peaks = self.peaks_anodic
        elif peak_type == 'cathodic':
            peaks = self.peaks_cathodic
        else:
            raise ValueError("peak_type must be 'anodic' or 'cathodic'")

        return x_data[peaks] if len(peaks) > 0 else np.array([])

    def calculate_peak_separation(self, x_data: np.ndarray) -> Optional[float]:
        """
        Calculate peak-to-peak separation (for reversible systems).

        Args:
            x_data: X-axis data (voltage)

        Returns:
            float or None: Peak separation in voltage units, or None if insufficient peaks
        """
        if len(self.peaks_anodic) == 0 or len(self.peaks_cathodic) == 0:
            return None

        # Use first anodic and cathodic peaks
        peak_anodic_v = x_data[self.peaks_anodic[0]]
        peak_cathodic_v = x_data[self.peaks_cathodic[0]]

        return abs(peak_anodic_v - peak_cathodic_v)

    def get_summary(self, x_data: np.ndarray, y_data: np.ndarray) -> Dict[str, any]:
        """
        Get summary of peak analysis.

        Args:
            x_data: X-axis data
            y_data: Y-axis data

        Returns:
            dict: Summary with peak counts, values, and separation
        """
        summary = {
            'num_anodic_peaks': len(self.peaks_anodic),
            'num_cathodic_peaks': len(self.peaks_cathodic),
            'anodic_peaks': self.get_peak_values(x_data, y_data, 'anodic'),
            'cathodic_peaks': self.get_peak_values(x_data, y_data, 'cathodic'),
        }

        # Add peak separation if available
        peak_sep = self.calculate_peak_separation(x_data)
        if peak_sep is not None:
            summary['peak_separation'] = peak_sep

        return summary
