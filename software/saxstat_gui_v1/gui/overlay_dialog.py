"""
Overlay Dialog

Dialog for selecting and comparing multiple experiment runs.
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem,
    QPushButton, QLabel, QGroupBox, QCheckBox, QMessageBox
)
from PyQt5.QtCore import Qt
from typing import List, Dict, Any


class OverlayDialog(QDialog):
    """
    Dialog for managing plot overlays.

    Allows users to:
    - View experiment history
    - Select multiple experiments to overlay
    - Configure overlay appearance
    """

    def __init__(self, history_summary: List[Dict[str, Any]], parent=None):
        """
        Initialize overlay dialog.

        Args:
            history_summary: List of experiment summaries from DataManager
            parent: Parent widget
        """
        super().__init__(parent)

        self.history_summary = history_summary
        self.selected_indices: List[int] = []

        self.setWindowTitle("Compare Experiments")
        self.setMinimumWidth(600)
        self.setMinimumHeight(400)

        self._init_ui()

    def _init_ui(self):
        """Initialize UI layout."""
        layout = QVBoxLayout(self)

        # Instructions
        instructions = QLabel(
            "Select experiments from history to overlay on current plot.\n"
            "Maximum 5 overlays recommended for readability."
        )
        instructions.setWordWrap(True)
        layout.addWidget(instructions)

        # Experiment list
        list_group = QGroupBox("Experiment History")
        list_layout = QVBoxLayout()

        self.experiment_list = QListWidget()
        self.experiment_list.setSelectionMode(QListWidget.MultiSelection)

        # Populate list
        self._populate_list()

        list_layout.addWidget(self.experiment_list)
        list_group.setLayout(list_layout)
        layout.addWidget(list_group)

        # Options
        options_group = QGroupBox("Display Options")
        options_layout = QVBoxLayout()

        self.show_legend_checkbox = QCheckBox("Show legend")
        self.show_legend_checkbox.setChecked(True)
        options_layout.addWidget(self.show_legend_checkbox)

        options_group.setLayout(options_layout)
        layout.addWidget(options_group)

        # Buttons
        button_layout = QHBoxLayout()

        self.clear_btn = QPushButton("Clear All Overlays")
        self.clear_btn.clicked.connect(self.accept)  # Return with empty selection
        button_layout.addWidget(self.clear_btn)

        button_layout.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        apply_btn = QPushButton("Apply Overlays")
        apply_btn.setDefault(True)
        apply_btn.clicked.connect(self._on_apply_clicked)
        button_layout.addWidget(apply_btn)

        layout.addLayout(button_layout)

    def _populate_list(self):
        """Populate experiment list with history."""
        for summary in reversed(self.history_summary):  # Most recent first
            # Format: "CV - 2024-03-15 14:30:25 (250 points)"
            exp_name = summary['experiment_name']
            start_time = summary['start_time']
            data_points = summary['data_points']

            if start_time:
                time_str = start_time.strftime('%Y-%m-%d %H:%M:%S')
            else:
                time_str = 'Unknown time'

            # Get parameter summary
            params = summary.get('parameters', {})
            param_str = ', '.join([f"{k}={v}" for k, v in list(params.items())[:3]])
            if len(params) > 3:
                param_str += "..."

            text = f"{exp_name} - {time_str} ({data_points} pts)"
            if param_str:
                text += f"\n  Parameters: {param_str}"

            item = QListWidgetItem(text)
            item.setData(Qt.UserRole, summary['index'])  # Store index
            self.experiment_list.addItem(item)

    def _on_apply_clicked(self):
        """Handle apply button click."""
        selected_items = self.experiment_list.selectedItems()

        if len(selected_items) > 5:
            QMessageBox.warning(
                self,
                "Too Many Overlays",
                "Maximum 5 overlays recommended for readability.\n"
                "Please select fewer experiments."
            )
            return

        # Get selected indices
        self.selected_indices = [
            item.data(Qt.UserRole) for item in selected_items
        ]

        self.accept()

    def get_selected_indices(self) -> List[int]:
        """
        Get indices of selected experiments.

        Returns:
            list: Indices into history list
        """
        return self.selected_indices

    def show_legend(self) -> bool:
        """
        Check if legend should be shown.

        Returns:
            bool: True if legend should be shown
        """
        return self.show_legend_checkbox.isChecked()
