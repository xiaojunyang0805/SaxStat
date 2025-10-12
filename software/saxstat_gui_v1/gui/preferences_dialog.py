"""
Preferences Dialog

Dialog for configuring application settings including autosave preferences.
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel,
    QCheckBox, QLineEdit, QPushButton, QFileDialog, QComboBox,
    QDialogButtonBox, QMessageBox
)
from PyQt5.QtCore import Qt
from pathlib import Path


class PreferencesDialog(QDialog):
    """
    Preferences dialog for application settings.

    Features:
    - Autosave enable/disable
    - Autosave directory selection
    - Filename pattern configuration
    - Format selection (CSV, JSON, Excel)
    """

    def __init__(self, config_manager, parent=None):
        """
        Initialize preferences dialog.

        Args:
            config_manager: ConfigManager instance
            parent: Parent widget
        """
        super().__init__(parent)
        self.config = config_manager

        self.setWindowTitle("Preferences")
        self.setMinimumWidth(500)
        self.setModal(True)

        self._setup_ui()
        self._load_settings()

    def _setup_ui(self):
        """Create the dialog UI."""
        layout = QVBoxLayout(self)

        # Autosave group
        autosave_group = QGroupBox("Autosave Settings")
        autosave_layout = QVBoxLayout()

        # Enable autosave checkbox
        self.autosave_enabled = QCheckBox("Enable autosave")
        self.autosave_enabled.stateChanged.connect(self._on_autosave_toggled)
        autosave_layout.addWidget(self.autosave_enabled)

        # Directory selection
        dir_layout = QHBoxLayout()
        dir_layout.addWidget(QLabel("Save Directory:"))
        self.directory_edit = QLineEdit()
        dir_layout.addWidget(self.directory_edit)
        self.browse_btn = QPushButton("Browse...")
        self.browse_btn.clicked.connect(self._on_browse_clicked)
        dir_layout.addWidget(self.browse_btn)
        autosave_layout.addLayout(dir_layout)

        # Filename pattern
        pattern_layout = QHBoxLayout()
        pattern_layout.addWidget(QLabel("Filename Pattern:"))
        self.pattern_combo = QComboBox()
        self.pattern_combo.addItems([
            "{experiment}_{timestamp}",
            "{experiment}_{date}_{time}",
            "{date}_{experiment}_{time}",
            "{timestamp}_{experiment}"
        ])
        self.pattern_combo.setEditable(True)
        pattern_layout.addWidget(self.pattern_combo)
        autosave_layout.addLayout(pattern_layout)

        # Pattern help text
        help_label = QLabel(
            "Available placeholders:\n"
            "  {experiment} - Experiment name (CV, LSV, etc.)\n"
            "  {timestamp} - Full timestamp (YYYY-MM-DD_HH-MM-SS)\n"
            "  {date} - Date only (YYYY-MM-DD)\n"
            "  {time} - Time only (HH-MM-SS)"
        )
        help_label.setStyleSheet("color: #666; font-size: 9pt;")
        autosave_layout.addWidget(help_label)

        # Format selection
        format_label = QLabel("Save Formats:")
        autosave_layout.addWidget(format_label)

        format_layout = QHBoxLayout()
        self.format_csv = QCheckBox("CSV")
        self.format_json = QCheckBox("JSON")
        self.format_excel = QCheckBox("Excel")
        format_layout.addWidget(self.format_csv)
        format_layout.addWidget(self.format_json)
        format_layout.addWidget(self.format_excel)
        format_layout.addStretch()
        autosave_layout.addLayout(format_layout)

        autosave_group.setLayout(autosave_layout)
        layout.addWidget(autosave_group)

        # Add stretch to push everything to top
        layout.addStretch()

        # Dialog buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        button_box.accepted.connect(self._on_accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def _load_settings(self):
        """Load current settings from config."""
        # Autosave enabled
        enabled = self.config.get('autosave.enabled', True)
        self.autosave_enabled.setChecked(enabled)

        # Directory
        directory = self.config.get('autosave.directory', '~/Documents/SaxStat/Data')
        self.directory_edit.setText(directory)

        # Filename pattern
        pattern = self.config.get('autosave.filename_pattern', '{experiment}_{timestamp}')
        index = self.pattern_combo.findText(pattern)
        if index >= 0:
            self.pattern_combo.setCurrentIndex(index)
        else:
            self.pattern_combo.setCurrentText(pattern)

        # Formats
        formats = self.config.get('autosave.formats', ['csv'])
        self.format_csv.setChecked('csv' in formats)
        self.format_json.setChecked('json' in formats)
        self.format_excel.setChecked('excel' in formats)

        # Update enabled state
        self._on_autosave_toggled(Qt.Checked if enabled else Qt.Unchecked)

    def _on_autosave_toggled(self, state):
        """Handle autosave checkbox toggle."""
        enabled = (state == Qt.Checked)
        self.directory_edit.setEnabled(enabled)
        self.browse_btn.setEnabled(enabled)
        self.pattern_combo.setEnabled(enabled)
        self.format_csv.setEnabled(enabled)
        self.format_json.setEnabled(enabled)
        self.format_excel.setEnabled(enabled)

    def _on_browse_clicked(self):
        """Handle browse button click."""
        current_dir = self.directory_edit.text()

        # Expand ~ if present
        if current_dir.startswith('~'):
            current_dir = str(Path(current_dir).expanduser())

        directory = QFileDialog.getExistingDirectory(
            self,
            "Select Autosave Directory",
            current_dir
        )

        if directory:
            self.directory_edit.setText(directory)

    def _on_accept(self):
        """Handle OK button click - validate and save settings."""
        # Validate at least one format is selected
        if self.autosave_enabled.isChecked():
            if not (self.format_csv.isChecked() or
                    self.format_json.isChecked() or
                    self.format_excel.isChecked()):
                QMessageBox.warning(
                    self,
                    "Invalid Configuration",
                    "Please select at least one save format."
                )
                return

        # Save settings
        self._save_settings()
        self.accept()

    def _save_settings(self):
        """Save settings to config."""
        # Autosave enabled
        self.config.set('autosave.enabled', self.autosave_enabled.isChecked())

        # Directory
        self.config.set('autosave.directory', self.directory_edit.text())

        # Filename pattern
        self.config.set('autosave.filename_pattern', self.pattern_combo.currentText())

        # Formats
        formats = []
        if self.format_csv.isChecked():
            formats.append('csv')
        if self.format_json.isChecked():
            formats.append('json')
        if self.format_excel.isChecked():
            formats.append('excel')

        self.config.set('autosave.formats', formats)
