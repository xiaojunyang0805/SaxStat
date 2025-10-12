"""
Calibration Dialog

Dialog for calibrating hardware parameters.
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QPushButton, QLabel, QGroupBox, QDoubleSpinBox, QMessageBox
)
from PyQt5.QtCore import Qt
from typing import Dict


class CalibrationDialog(QDialog):
    """
    Dialog for hardware calibration.

    Allows users to calibrate:
    - Offset current (µA)
    - TIA resistance (Ω)
    - Reference voltage (V)
    """

    def __init__(self, config_manager, parent=None):
        """
        Initialize calibration dialog.

        Args:
            config_manager: ConfigManager instance
            parent: Parent widget
        """
        super().__init__(parent)

        self.config = config_manager

        self.setWindowTitle("Hardware Calibration")
        self.setMinimumWidth(500)
        self.setModal(True)

        self._init_ui()
        self._load_current_values()

    def _init_ui(self):
        """Initialize UI layout."""
        layout = QVBoxLayout(self)

        # Instructions
        instructions = QLabel(
            "<b>Hardware Calibration</b><br><br>"
            "Calibrate the potentiostat hardware parameters for accurate measurements.<br>"
            "Use a known reference standard to determine correct values.<br><br>"
            "<b>Warning:</b> Incorrect calibration will affect measurement accuracy."
        )
        instructions.setWordWrap(True)
        layout.addWidget(instructions)

        # Calibration parameters
        params_group = QGroupBox("Calibration Parameters")
        params_layout = QFormLayout()

        # Offset current
        self.offset_current_spin = QDoubleSpinBox()
        self.offset_current_spin.setRange(-100.0, 100.0)
        self.offset_current_spin.setDecimals(3)
        self.offset_current_spin.setSingleStep(0.001)
        self.offset_current_spin.setSuffix(" µA")
        params_layout.addRow("Offset Current:", self.offset_current_spin)

        offset_help = QLabel("Zero-current offset. Measure with no sample connected.")
        offset_help.setStyleSheet("color: #666; font-size: 9pt;")
        offset_help.setWordWrap(True)
        params_layout.addRow("", offset_help)

        # TIA resistance
        self.tia_resistance_spin = QDoubleSpinBox()
        self.tia_resistance_spin.setRange(100, 1000000)
        self.tia_resistance_spin.setDecimals(0)
        self.tia_resistance_spin.setSingleStep(1000)
        self.tia_resistance_spin.setSuffix(" Ω")
        params_layout.addRow("TIA Resistance:", self.tia_resistance_spin)

        tia_help = QLabel("Transimpedance amplifier feedback resistance.")
        tia_help.setStyleSheet("color: #666; font-size: 9pt;")
        tia_help.setWordWrap(True)
        params_layout.addRow("", tia_help)

        # Reference voltage
        self.vref_spin = QDoubleSpinBox()
        self.vref_spin.setRange(0.1, 5.0)
        self.vref_spin.setDecimals(4)
        self.vref_spin.setSingleStep(0.001)
        self.vref_spin.setSuffix(" V")
        params_layout.addRow("Reference Voltage:", self.vref_spin)

        vref_help = QLabel("ADC reference voltage. Typically 1.0V or 3.3V.")
        vref_help.setStyleSheet("color: #666; font-size: 9pt;")
        vref_help.setWordWrap(True)
        params_layout.addRow("", vref_help)

        params_group.setLayout(params_layout)
        layout.addWidget(params_group)

        # Common presets section
        presets_group = QGroupBox("Common Configurations")
        presets_layout = QVBoxLayout()

        preset_label = QLabel("Quick apply common calibration presets:")
        preset_label.setStyleSheet("font-size: 9pt;")
        presets_layout.addWidget(preset_label)

        preset_buttons_layout = QHBoxLayout()

        default_btn = QPushButton("Default (10kΩ, 1.0V)")
        default_btn.clicked.connect(lambda: self._apply_preset(0.0, 10000, 1.0))
        preset_buttons_layout.addWidget(default_btn)

        high_sens_btn = QPushButton("High Sensitivity (100kΩ, 1.0V)")
        high_sens_btn.clicked.connect(lambda: self._apply_preset(0.0, 100000, 1.0))
        preset_buttons_layout.addWidget(high_sens_btn)

        low_sens_btn = QPushButton("Low Sensitivity (1kΩ, 1.0V)")
        low_sens_btn.clicked.connect(lambda: self._apply_preset(0.0, 1000, 1.0))
        preset_buttons_layout.addWidget(low_sens_btn)

        presets_layout.addLayout(preset_buttons_layout)
        presets_group.setLayout(presets_layout)
        layout.addWidget(presets_group)

        # Last calibrated info
        self.last_calibrated_label = QLabel()
        self.last_calibrated_label.setStyleSheet("color: #666; font-size: 9pt; font-style: italic;")
        layout.addWidget(self.last_calibrated_label)

        layout.addStretch()

        # Buttons
        button_layout = QHBoxLayout()

        reset_btn = QPushButton("Reset to Defaults")
        reset_btn.clicked.connect(self._on_reset_clicked)
        button_layout.addWidget(reset_btn)

        button_layout.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        save_btn = QPushButton("Save Calibration")
        save_btn.setDefault(True)
        save_btn.clicked.connect(self._on_save_clicked)
        button_layout.addWidget(save_btn)

        layout.addLayout(button_layout)

    def _load_current_values(self):
        """Load current calibration values from config."""
        calibration = self.config.get_calibration()

        self.offset_current_spin.setValue(calibration.get('offset_current', 0.0))
        self.tia_resistance_spin.setValue(calibration.get('tia_resistance', 10000))
        self.vref_spin.setValue(calibration.get('vref', 1.0))

        # Show last calibrated time
        calibrated_at = calibration.get('calibrated_at')
        if calibrated_at:
            self.last_calibrated_label.setText(f"Last calibrated: {calibrated_at}")
        else:
            self.last_calibrated_label.setText("Not yet calibrated")

    def _apply_preset(self, offset: float, tia: float, vref: float):
        """
        Apply a preset configuration.

        Args:
            offset: Offset current
            tia: TIA resistance
            vref: Reference voltage
        """
        self.offset_current_spin.setValue(offset)
        self.tia_resistance_spin.setValue(tia)
        self.vref_spin.setValue(vref)

    def _on_reset_clicked(self):
        """Handle reset to defaults button click."""
        reply = QMessageBox.question(
            self,
            "Reset Calibration",
            "Reset all calibration values to factory defaults?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            self._apply_preset(0.0, 10000, 1.0)

    def _on_save_clicked(self):
        """Handle save button click."""
        # Get values
        offset_current = self.offset_current_spin.value()
        tia_resistance = self.tia_resistance_spin.value()
        vref = self.vref_spin.value()

        # Validate
        if tia_resistance < 100:
            QMessageBox.warning(
                self,
                "Invalid Value",
                "TIA resistance must be at least 100 Ω"
            )
            return

        if vref < 0.1 or vref > 5.0:
            QMessageBox.warning(
                self,
                "Invalid Value",
                "Reference voltage must be between 0.1V and 5.0V"
            )
            return

        # Save to config
        self.config.set_calibration(offset_current, tia_resistance, vref)

        QMessageBox.information(
            self,
            "Calibration Saved",
            "Calibration values saved successfully!\n\n"
            f"Offset Current: {offset_current:.3f} µA\n"
            f"TIA Resistance: {tia_resistance:.0f} Ω\n"
            f"Reference Voltage: {vref:.4f} V"
        )

        self.accept()

    def get_calibration(self) -> Dict[str, float]:
        """
        Get calibration values from dialog.

        Returns:
            dict: Calibration values
        """
        return {
            'offset_current': self.offset_current_spin.value(),
            'tia_resistance': self.tia_resistance_spin.value(),
            'vref': self.vref_spin.value()
        }
