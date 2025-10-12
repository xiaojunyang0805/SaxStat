"""
Parameter Panel Widget

Dynamic parameter input panel that adapts to selected experiment type.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QLineEdit, QSpinBox, QDoubleSpinBox, QPushButton,
    QGroupBox, QMessageBox
)
from PyQt5.QtCore import pyqtSignal
from typing import Dict, Any, Optional

from ..experiments import BaseExperiment


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

    def __init__(self, parent=None):
        super().__init__(parent)

        self.experiment: Optional[BaseExperiment] = None
        self.input_widgets: Dict[str, QWidget] = {}

        self._init_ui()

    def _init_ui(self):
        """Initialize the UI layout."""
        layout = QVBoxLayout(self)

        # Parameter group box
        self.param_group = QGroupBox("Experiment Parameters")
        self.param_layout = QFormLayout()
        self.param_group.setLayout(self.param_layout)

        layout.addWidget(self.param_group)

        # Configure button
        button_layout = QHBoxLayout()
        self.configure_btn = QPushButton("Configure Experiment")
        self.configure_btn.clicked.connect(self._on_configure_clicked)
        self.configure_btn.setEnabled(False)
        button_layout.addStretch()
        button_layout.addWidget(self.configure_btn)

        layout.addLayout(button_layout)
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
