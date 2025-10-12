"""
Parameter Panel Widget

Dynamic parameter input panel that adapts to selected experiment type.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QLineEdit, QSpinBox, QDoubleSpinBox, QPushButton,
    QGroupBox, QMessageBox, QComboBox, QInputDialog
)
from PyQt5.QtCore import pyqtSignal
from typing import Dict, Any, Optional

from ..experiments import BaseExperiment
from ..config.config_manager import ConfigManager


class ParameterPanel(QWidget):
    """
    Dynamic parameter input panel for experiments.

    Features:
    - Auto-generates input widgets from experiment parameter schema
    - Type-specific inputs (int, float, bool, str)
    - Min/max validation
    - Units display
    - Configure button to apply parameters

    Signals:
    - parameters_configured: Emitted when parameters are validated and ready
    """

    parameters_configured = pyqtSignal(dict)  # {parameter_name: value}

    def __init__(self, config_manager: ConfigManager = None, parent=None):
        super().__init__(parent)

        self.config = config_manager
        self.experiment: Optional[BaseExperiment] = None
        self.input_widgets: Dict[str, QWidget] = {}

        self._init_ui()

    def _init_ui(self):
        """Initialize the UI layout."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Parameter group box
        self.param_group = QGroupBox("Experiment Parameters")
        param_group_layout = QVBoxLayout()

        # Preset controls
        preset_layout = QHBoxLayout()
        preset_layout.addWidget(QLabel("Preset:"))

        self.preset_combo = QComboBox()
        self.preset_combo.currentTextChanged.connect(self._on_preset_selected)
        preset_layout.addWidget(self.preset_combo)

        self.save_preset_btn = QPushButton("Save")
        self.save_preset_btn.clicked.connect(self._on_save_preset_clicked)
        self.save_preset_btn.setEnabled(False)
        preset_layout.addWidget(self.save_preset_btn)

        self.delete_preset_btn = QPushButton("Delete")
        self.delete_preset_btn.clicked.connect(self._on_delete_preset_clicked)
        self.delete_preset_btn.setEnabled(False)
        preset_layout.addWidget(self.delete_preset_btn)

        param_group_layout.addLayout(preset_layout)

        # Form layout for parameters
        self.param_layout = QFormLayout()
        param_group_layout.addLayout(self.param_layout)

        # Configure button inside the group box
        self.configure_btn = QPushButton("Configure Experiment")
        self.configure_btn.clicked.connect(self._on_configure_clicked)
        self.configure_btn.setEnabled(False)
        param_group_layout.addWidget(self.configure_btn)

        self.param_group.setLayout(param_group_layout)
        layout.addWidget(self.param_group)
        layout.addStretch()

    def set_experiment(self, experiment: BaseExperiment):
        """
        Set the current experiment and rebuild parameter inputs.

        Args:
            experiment: Experiment instance
        """
        self.experiment = experiment

        # Clear existing inputs
        self._clear_inputs()

        if experiment is None:
            self.configure_btn.setEnabled(False)
            self.save_preset_btn.setEnabled(False)
            self.delete_preset_btn.setEnabled(False)
            return

        # Get parameter schema
        params = experiment.get_parameters()

        # Create input widgets based on schema
        for param_name, param_def in params.items():
            widget = self._create_input_widget(param_name, param_def)
            if widget:
                self.input_widgets[param_name] = widget

                # Create label with unit
                label = param_def.get('description', param_name)
                unit = param_def.get('unit', '')
                if unit:
                    label = f"{label} ({unit})"

                self.param_layout.addRow(label, widget)

        self.configure_btn.setEnabled(True)
        self.save_preset_btn.setEnabled(True)

        # Load presets for this experiment
        self._load_presets()

    def _create_input_widget(self, param_name: str, param_def: Dict[str, Any]) -> Optional[QWidget]:
        """
        Create appropriate input widget based on parameter definition.

        Args:
            param_name: Parameter name
            param_def: Parameter definition dict

        Returns:
            QWidget: Input widget
        """
        param_type = param_def.get('type', float)
        default = param_def.get('default', 0)
        min_val = param_def.get('min', None)
        max_val = param_def.get('max', None)

        widget = None

        if param_type == int:
            # Integer spin box
            widget = QSpinBox()
            widget.setValue(default)
            if min_val is not None:
                widget.setMinimum(min_val)
            if max_val is not None:
                widget.setMaximum(max_val)

        elif param_type == float:
            # Double spin box
            widget = QDoubleSpinBox()
            widget.setValue(default)
            widget.setDecimals(3)
            widget.setSingleStep(0.01)
            if min_val is not None:
                widget.setMinimum(min_val)
            if max_val is not None:
                widget.setMaximum(max_val)

        elif param_type == str:
            # Line edit
            widget = QLineEdit()
            widget.setText(str(default))

        return widget

    def _clear_inputs(self):
        """Clear all parameter input widgets."""
        # Remove all rows from form layout
        while self.param_layout.rowCount() > 0:
            self.param_layout.removeRow(0)

        self.input_widgets.clear()

    def get_parameters(self) -> Dict[str, Any]:
        """
        Get current parameter values from input widgets.

        Returns:
            dict: Parameter values
        """
        params = {}

        for param_name, widget in self.input_widgets.items():
            if isinstance(widget, QSpinBox):
                params[param_name] = widget.value()
            elif isinstance(widget, QDoubleSpinBox):
                params[param_name] = widget.value()
            elif isinstance(widget, QLineEdit):
                params[param_name] = widget.text()

        return params

    def _on_configure_clicked(self):
        """Handle configure button click."""
        if self.experiment is None:
            return

        # Get parameter values
        params = self.get_parameters()

        # Validate parameters
        try:
            if self.experiment.validate_parameters(params):
                # Emit signal with validated parameters
                self.parameters_configured.emit(params)

        except ValueError as e:
            # Show validation error
            QMessageBox.warning(
                self,
                "Invalid Parameters",
                f"Parameter validation failed:\n{str(e)}"
            )

    def set_enabled(self, enabled: bool):
        """
        Enable or disable all parameter inputs.

        Args:
            enabled: Enable state
        """
        self.param_group.setEnabled(enabled)
        self.configure_btn.setEnabled(enabled and self.experiment is not None)

    def set_parameters(self, parameters: Dict[str, Any]):
        """
        Set parameter values in the input widgets.

        Args:
            parameters: Dictionary of parameter_name -> value
        """
        for param_name, value in parameters.items():
            if param_name in self.input_widgets:
                widget = self.input_widgets[param_name]

                if isinstance(widget, (QSpinBox, QDoubleSpinBox)):
                    widget.setValue(value)
                elif isinstance(widget, QLineEdit):
                    widget.setText(str(value))

    # Preset management

    def _load_presets(self):
        """Load presets for current experiment into combo box."""
        if not self.config or not self.experiment:
            return

        # Get experiment name
        exp_name = self.experiment.get_name()

        # Clear combo box
        self.preset_combo.blockSignals(True)
        self.preset_combo.clear()

        # Add default option
        self.preset_combo.addItem("-- Select Preset --")

        # Load presets from config
        presets = self.config.get_presets(exp_name)
        for preset_name in sorted(presets.keys()):
            self.preset_combo.addItem(preset_name)

        self.preset_combo.blockSignals(False)

        # Enable/disable delete button
        self.delete_preset_btn.setEnabled(False)

    def _on_preset_selected(self, preset_name: str):
        """Handle preset selection from combo box."""
        if not self.config or not self.experiment:
            return

        if preset_name == "-- Select Preset --" or not preset_name:
            self.delete_preset_btn.setEnabled(False)
            return

        # Load preset parameters
        exp_name = self.experiment.get_name()
        parameters = self.config.load_preset(exp_name, preset_name)

        if parameters:
            # Apply parameters to widgets
            self.set_parameters(parameters)
            self.delete_preset_btn.setEnabled(True)

    def _on_save_preset_clicked(self):
        """Handle save preset button click."""
        if not self.config or not self.experiment:
            return

        # Get preset name from user
        name, ok = QInputDialog.getText(
            self,
            "Save Preset",
            "Enter preset name:",
            QLineEdit.Normal,
            ""
        )

        if ok and name:
            # Get current parameters
            parameters = self.get_parameters()

            # Save preset
            exp_name = self.experiment.get_name()
            self.config.save_preset(exp_name, name, parameters)

            # Reload presets
            self._load_presets()

            # Select the newly saved preset
            index = self.preset_combo.findText(name)
            if index >= 0:
                self.preset_combo.setCurrentIndex(index)

            QMessageBox.information(
                self,
                "Preset Saved",
                f"Preset '{name}' saved successfully!"
            )

    def _on_delete_preset_clicked(self):
        """Handle delete preset button click."""
        if not self.config or not self.experiment:
            return

        preset_name = self.preset_combo.currentText()
        if preset_name == "-- Select Preset --" or not preset_name:
            return

        # Confirm deletion
        reply = QMessageBox.question(
            self,
            "Delete Preset",
            f"Are you sure you want to delete preset '{preset_name}'?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            # Delete preset
            exp_name = self.experiment.get_name()
            self.config.delete_preset(exp_name, preset_name)

            # Reload presets
            self._load_presets()

            QMessageBox.information(
                self,
                "Preset Deleted",
                f"Preset '{preset_name}' deleted successfully!"
            )
