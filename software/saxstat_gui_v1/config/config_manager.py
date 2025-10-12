"""
Configuration Manager

Manages application configuration and user preferences using JSON files.
"""

import json
from pathlib import Path
from typing import Any, Dict, Optional
from datetime import datetime


class ConfigManager:
    """
    Manages application configuration and settings.

    Features:
    - JSON-based configuration storage
    - Default values
    - Type-safe access
    - Auto-save on changes
    """

    DEFAULT_CONFIG = {
        'serial': {
            'baudrate': 115200,
            'timeout': 0.1,
            'last_port': ''
        },
        'ui': {
            'window_width': 1400,
            'window_height': 900,
            'theme': 'light'
        },
        'experiments': {
            'last_experiment': 'CV'
        },
        'autosave': {
            'enabled': True,  # ON by default
            'directory': '~/Documents/SaxStat/Data',
            'filename_pattern': '{experiment}_{timestamp}',
            'formats': ['csv'],  # CSV only by default
            'create_directory': True
        },
        'calibration': {
            'offset_current': 0.0,
            'tia_resistance': 10000,
            'vref': 1.0
        }
    }

    def __init__(self, config_file: Optional[Path] = None):
        """
        Initialize configuration manager.

        Args:
            config_file: Path to config file (default: ~/.saxstat/config.json)
        """
        if config_file is None:
            config_dir = Path.home() / '.saxstat'
            config_dir.mkdir(exist_ok=True)
            config_file = config_dir / 'config.json'

        self.config_file = config_file
        self.config: Dict[str, Any] = {}

        self.load()

    def load(self):
        """Load configuration from file."""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    self.config = json.load(f)

                # Merge with defaults for missing keys
                self._merge_defaults()

            except Exception as e:
                print(f"Error loading config: {e}")
                self.config = self.DEFAULT_CONFIG.copy()
        else:
            self.config = self.DEFAULT_CONFIG.copy()
            self.save()

    def save(self):
        """Save configuration to file."""
        try:
            self.config_file.parent.mkdir(parents=True, exist_ok=True)

            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)

        except Exception as e:
            print(f"Error saving config: {e}")

    def _merge_defaults(self):
        """Merge loaded config with defaults for missing keys."""
        def merge_dict(target: dict, source: dict):
            for key, value in source.items():
                if key not in target:
                    target[key] = value
                elif isinstance(value, dict) and isinstance(target[key], dict):
                    merge_dict(target[key], value)

        merge_dict(self.config, self.DEFAULT_CONFIG)

    # Getter methods

    def get(self, key_path: str, default: Any = None) -> Any:
        """
        Get a configuration value by key path.

        Args:
            key_path: Dot-separated key path (e.g., 'serial.baudrate')
            default: Default value if key not found

        Returns:
            Configuration value
        """
        keys = key_path.split('.')
        value = self.config

        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default

        return value

    def set(self, key_path: str, value: Any, auto_save: bool = True):
        """
        Set a configuration value by key path.

        Args:
            key_path: Dot-separated key path (e.g., 'serial.baudrate')
            value: Value to set
            auto_save: Automatically save after setting
        """
        keys = key_path.split('.')
        config = self.config

        # Navigate to parent dict
        for key in keys[:-1]:
            if key not in config:
                config[key] = {}
            config = config[key]

        # Set value
        config[keys[-1]] = value

        if auto_save:
            self.save()

    # Convenience methods for common settings

    def get_serial_config(self) -> Dict[str, Any]:
        """Get serial port configuration."""
        return self.config.get('serial', self.DEFAULT_CONFIG['serial'])

    def set_last_port(self, port: str):
        """Set last used serial port."""
        self.set('serial.last_port', port)

    def get_calibration(self) -> Dict[str, float]:
        """Get calibration values."""
        return self.config.get('calibration', self.DEFAULT_CONFIG['calibration'])

    def set_calibration(self, offset_current: float, tia_resistance: float, vref: float):
        """
        Set calibration values.

        Args:
            offset_current: Offset current in µA
            tia_resistance: TIA resistance in Ω
            vref: Reference voltage in V
        """
        self.config['calibration'] = {
            'offset_current': offset_current,
            'tia_resistance': tia_resistance,
            'vref': vref,
            'calibrated_at': datetime.now().isoformat()
        }
        self.save()

    def get_ui_config(self) -> Dict[str, Any]:
        """Get UI configuration."""
        return self.config.get('ui', self.DEFAULT_CONFIG['ui'])

    def set_window_geometry(self, width: int, height: int):
        """Set window dimensions."""
        self.set('ui.window_width', width, auto_save=False)
        self.set('ui.window_height', height, auto_save=True)

    def reset_to_defaults(self):
        """Reset all configuration to default values."""
        self.config = self.DEFAULT_CONFIG.copy()
        self.save()

    # Parameter Presets

    def get_presets(self, experiment_name: str) -> Dict[str, Dict[str, Any]]:
        """
        Get all presets for an experiment type.

        Args:
            experiment_name: Name of experiment (CV, LSV, etc.)

        Returns:
            dict: Dictionary of preset_name -> parameters
        """
        if 'presets' not in self.config:
            self.config['presets'] = {}

        return self.config['presets'].get(experiment_name, {})

    def save_preset(self, experiment_name: str, preset_name: str, parameters: Dict[str, Any]):
        """
        Save a parameter preset for an experiment.

        Args:
            experiment_name: Name of experiment (CV, LSV, etc.)
            preset_name: Name for this preset
            parameters: Parameter values to save
        """
        if 'presets' not in self.config:
            self.config['presets'] = {}

        if experiment_name not in self.config['presets']:
            self.config['presets'][experiment_name] = {}

        self.config['presets'][experiment_name][preset_name] = parameters.copy()
        self.save()

    def load_preset(self, experiment_name: str, preset_name: str) -> Optional[Dict[str, Any]]:
        """
        Load a parameter preset.

        Args:
            experiment_name: Name of experiment
            preset_name: Name of preset

        Returns:
            dict: Parameter values, or None if preset doesn't exist
        """
        presets = self.get_presets(experiment_name)
        return presets.get(preset_name)

    def delete_preset(self, experiment_name: str, preset_name: str):
        """
        Delete a parameter preset.

        Args:
            experiment_name: Name of experiment
            preset_name: Name of preset to delete
        """
        if 'presets' in self.config:
            if experiment_name in self.config['presets']:
                if preset_name in self.config['presets'][experiment_name]:
                    del self.config['presets'][experiment_name][preset_name]
                    self.save()

    def rename_preset(self, experiment_name: str, old_name: str, new_name: str):
        """
        Rename a parameter preset.

        Args:
            experiment_name: Name of experiment
            old_name: Current preset name
            new_name: New preset name
        """
        if 'presets' in self.config:
            if experiment_name in self.config['presets']:
                if old_name in self.config['presets'][experiment_name]:
                    # Copy to new name
                    self.config['presets'][experiment_name][new_name] = \
                        self.config['presets'][experiment_name][old_name]
                    # Delete old name
                    del self.config['presets'][experiment_name][old_name]
                    self.save()
