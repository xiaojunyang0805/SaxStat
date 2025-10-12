"""
Analysis Panel Widget

UI for data analysis tools including peak detection, baseline correction,
integration, and smoothing.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
    QPushButton, QLabel, QSpinBox, QDoubleSpinBox,
    QComboBox, QTextEdit, QFormLayout, QMessageBox
)
from PyQt5.QtCore import pyqtSignal
import numpy as np
from typing import Optional

from ..analysis import PeakDetector, BaselineCorrector, DataIntegrator, DataSmoother


class AnalysisPanel(QWidget):
    """
    Analysis tools panel for post-processing data.

    Features:
    - Peak detection with configurable parameters
    - Baseline correction methods
    - Charge/integration calculation
    - Data smoothing filters
    - Results display

    Signals:
    - analysis_applied: Emitted when analysis is performed (data_dict)
    """

    analysis_applied = pyqtSignal(dict)  # {type, results, modified_data}

    def __init__(self, parent=None):
        super().__init__(parent)

        # Analysis tools
        self.peak_detector = PeakDetector()
        self.baseline_corrector = BaselineCorrector()
        self.integrator = DataIntegrator()
        self.smoother = DataSmoother()

        # Current data
        self.x_data: Optional[np.ndarray] = None
        self.y_data: Optional[np.ndarray] = None

        self._init_ui()

    def _init_ui(self):
        """Initialize the UI layout."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Analysis tools group
        analysis_group = QGroupBox("Data Analysis Tools")
        analysis_layout = QVBoxLayout()

        # Peak Detection section
        peak_layout = QVBoxLayout()
        peak_label = QLabel("Peak Detection")
        peak_label.setStyleSheet("font-weight: bold;")
        peak_layout.addWidget(peak_label)

        peak_controls = QHBoxLayout()
        self.prominence_spin = QDoubleSpinBox()
        self.prominence_spin.setPrefix("Prom: ")
        self.prominence_spin.setDecimals(3)
        self.prominence_spin.setRange(0.001, 1000)
        self.prominence_spin.setValue(0.1)
        self.prominence_spin.setSingleStep(0.01)
        peak_controls.addWidget(self.prominence_spin)

        self.detect_peaks_btn = QPushButton("Detect Peaks")
        self.detect_peaks_btn.clicked.connect(self._on_detect_peaks)
        peak_controls.addWidget(self.detect_peaks_btn)
        peak_layout.addLayout(peak_controls)
        analysis_layout.addLayout(peak_layout)

        # Baseline Correction section
        baseline_layout = QVBoxLayout()
        baseline_label = QLabel("Baseline Correction")
        baseline_label.setStyleSheet("font-weight: bold;")
        baseline_layout.addWidget(baseline_label)

        baseline_controls = QHBoxLayout()
        self.baseline_method = QComboBox()
        self.baseline_method.addItems(['Polynomial', 'Spline', 'Linear', 'Endpoints'])
        baseline_controls.addWidget(self.baseline_method)

        self.baseline_btn = QPushButton("Apply Baseline")
        self.baseline_btn.clicked.connect(self._on_apply_baseline)
        baseline_controls.addWidget(self.baseline_btn)
        baseline_layout.addLayout(baseline_controls)
        analysis_layout.addLayout(baseline_layout)

        # Integration section
        integration_layout = QVBoxLayout()
        integration_label = QLabel("Integration")
        integration_label.setStyleSheet("font-weight: bold;")
        integration_layout.addWidget(integration_label)

        integration_controls = QHBoxLayout()
        self.integration_method = QComboBox()
        self.integration_method.addItems(['Trapezoidal', 'Simpson'])
        integration_controls.addWidget(self.integration_method)

        self.integrate_btn = QPushButton("Calculate Charge")
        self.integrate_btn.clicked.connect(self._on_calculate_charge)
        integration_controls.addWidget(self.integrate_btn)
        integration_layout.addLayout(integration_controls)
        analysis_layout.addLayout(integration_layout)

        # Smoothing section
        smoothing_layout = QVBoxLayout()
        smoothing_label = QLabel("Smoothing")
        smoothing_label.setStyleSheet("font-weight: bold;")
        smoothing_layout.addWidget(smoothing_label)

        smoothing_controls = QHBoxLayout()
        self.smoothing_method = QComboBox()
        self.smoothing_method.addItems(['Savitzky-Golay', 'Moving Average', 'Gaussian'])
        smoothing_controls.addWidget(self.smoothing_method)

        self.smooth_btn = QPushButton("Apply Smoothing")
        self.smooth_btn.clicked.connect(self._on_apply_smoothing)
        smoothing_controls.addWidget(self.smooth_btn)
        smoothing_layout.addLayout(smoothing_controls)
        analysis_layout.addLayout(smoothing_layout)

        analysis_group.setLayout(analysis_layout)
        layout.addWidget(analysis_group)

        # Results display
        results_group = QGroupBox("Analysis Results")
        results_layout = QVBoxLayout()

        self.results_text = QTextEdit()
        self.results_text.setReadOnly(True)
        self.results_text.setMaximumHeight(120)
        results_layout.addWidget(self.results_text)

        self.clear_results_btn = QPushButton("Clear Results")
        self.clear_results_btn.clicked.connect(self._clear_results)
        results_layout.addWidget(self.clear_results_btn)

        results_group.setLayout(results_layout)
        layout.addWidget(results_group)

        layout.addStretch()

        # Initially disabled
        self.set_enabled(False)

    def set_data(self, x_data: np.ndarray, y_data: np.ndarray):
        """
        Set current data for analysis.

        Args:
            x_data: X-axis data
            y_data: Y-axis data
        """
        self.x_data = x_data
        self.y_data = y_data
        self.set_enabled(len(x_data) > 0)

    def _on_detect_peaks(self):
        """Handle peak detection button click."""
        if self.x_data is None or self.y_data is None:
            return

        try:
            prominence = self.prominence_spin.value()

            # Detect peaks
            results = self.peak_detector.detect_peaks(
                self.x_data,
                self.y_data,
                prominence=prominence
            )

            # Get summary
            summary = self.peak_detector.get_summary(self.x_data, self.y_data)

            # Display results
            result_text = f"Peak Detection Results:\n"
            result_text += f"Anodic peaks: {summary['num_anodic_peaks']}\n"
            result_text += f"Cathodic peaks: {summary['num_cathodic_peaks']}\n"

            if summary['num_anodic_peaks'] > 0:
                result_text += "\nAnodic peaks (x, y):\n"
                for x, y in summary['anodic_peaks'][:5]:  # Show first 5
                    result_text += f"  ({x:.4f}, {y:.6e})\n"

            if summary['num_cathodic_peaks'] > 0:
                result_text += "\nCathodic peaks (x, y):\n"
                for x, y in summary['cathodic_peaks'][:5]:  # Show first 5
                    result_text += f"  ({x:.4f}, {y:.6e})\n"

            if 'peak_separation' in summary:
                result_text += f"\nPeak separation: {summary['peak_separation']:.4f}\n"

            self.results_text.append(result_text)

            # Emit signal with peak data
            self.analysis_applied.emit({
                'type': 'peak_detection',
                'results': results,
                'summary': summary
            })

        except Exception as e:
            QMessageBox.warning(self, "Peak Detection Error", str(e))

    def _on_apply_baseline(self):
        """Handle baseline correction button click."""
        if self.x_data is None or self.y_data is None:
            return

        try:
            method_name = self.baseline_method.currentText()
            method_map = {
                'Polynomial': 'polynomial',
                'Spline': 'spline',
                'Linear': 'linear',
                'Endpoints': 'endpoints'
            }
            method = method_map[method_name]

            # Apply baseline correction
            baseline, corrected = self.baseline_corrector.correct(
                self.x_data,
                self.y_data,
                method=method
            )

            # Display results
            result_text = f"Baseline Correction ({method_name}):\n"
            result_text += f"Method: {method}\n"
            result_text += f"Baseline range: [{np.min(baseline):.6e}, {np.max(baseline):.6e}]\n"
            result_text += f"Corrected data range: [{np.min(corrected):.6e}, {np.max(corrected):.6e}]\n"

            self.results_text.append(result_text)

            # Emit signal with corrected data
            self.analysis_applied.emit({
                'type': 'baseline_correction',
                'baseline': baseline,
                'corrected_data': corrected,
                'method': method
            })

        except Exception as e:
            QMessageBox.warning(self, "Baseline Correction Error", str(e))

    def _on_calculate_charge(self):
        """Handle charge calculation button click."""
        if self.x_data is None or self.y_data is None:
            return

        try:
            method_name = self.integration_method.currentText()
            method = 'trapz' if method_name == 'Trapezoidal' else 'simpson'

            # Calculate charge
            charge = self.integrator.calculate_charge(
                self.x_data,
                self.y_data,
                method=method
            )

            # Get statistics
            stats = self.integrator.get_statistics(self.x_data, self.y_data)

            # Display results
            result_text = f"Integration Results ({method_name}):\n"
            result_text += f"Total charge: {charge:.6e} C\n"
            result_text += f"Duration: {stats['duration']:.3f} s\n"
            result_text += f"Average current: {stats['average_current']:.6e} A\n"
            result_text += f"Peak current: {stats['peak_current']:.6e} A\n"

            self.results_text.append(result_text)

            # Emit signal with charge data
            self.analysis_applied.emit({
                'type': 'integration',
                'charge': charge,
                'statistics': stats,
                'method': method
            })

        except Exception as e:
            QMessageBox.warning(self, "Integration Error", str(e))

    def _on_apply_smoothing(self):
        """Handle smoothing button click."""
        if self.x_data is None or self.y_data is None:
            return

        try:
            method_name = self.smoothing_method.currentText()
            method_map = {
                'Savitzky-Golay': 'savitzky_golay',
                'Moving Average': 'moving_average',
                'Gaussian': 'gaussian'
            }
            method = method_map[method_name]

            # Apply smoothing
            smoothed = self.smoother.smooth(self.y_data, method=method)

            # Calculate noise reduction
            noise_before = np.std(np.diff(self.y_data))
            noise_after = np.std(np.diff(smoothed))
            noise_reduction = (1 - noise_after / noise_before) * 100

            # Display results
            result_text = f"Smoothing Results ({method_name}):\n"
            result_text += f"Method: {method}\n"
            result_text += f"Noise reduction: {noise_reduction:.1f}%\n"
            result_text += f"Data points: {len(smoothed)}\n"

            self.results_text.append(result_text)

            # Emit signal with smoothed data
            self.analysis_applied.emit({
                'type': 'smoothing',
                'smoothed_data': smoothed,
                'method': method,
                'noise_reduction': noise_reduction
            })

        except Exception as e:
            QMessageBox.warning(self, "Smoothing Error", str(e))

    def _clear_results(self):
        """Clear results display."""
        self.results_text.clear()

    def set_enabled(self, enabled: bool):
        """
        Enable or disable analysis controls.

        Args:
            enabled: Enable state
        """
        self.detect_peaks_btn.setEnabled(enabled)
        self.baseline_btn.setEnabled(enabled)
        self.integrate_btn.setEnabled(enabled)
        self.smooth_btn.setEnabled(enabled)
