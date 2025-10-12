"""
Experiment Registry

Manages registration and creation of experiment types using the Registry pattern.
"""

from typing import Dict, Type, List
from .base_experiment import BaseExperiment


class ExperimentRegistry:
    """
    Registry for managing available experiment types.

    Features:
    - Register experiment classes
    - Create experiment instances by name
    - List available experiments
    - Singleton pattern for global access
    """

    _instance = None
    _experiments: Dict[str, Type[BaseExperiment]] = {}

    def __new__(cls):
        """Singleton pattern - only one registry instance."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialize the registry."""
        # Only initialize once
        if not hasattr(self, '_initialized'):
            self._experiments = {}
            self._initialized = True

    def register(self, experiment_class: Type[BaseExperiment]):
        """
        Register an experiment class.

        Args:
            experiment_class: Experiment class (subclass of BaseExperiment)

        Raises:
            ValueError: If experiment name already registered
        """
        # Create temporary instance to get name
        temp_instance = experiment_class()
        name = temp_instance.get_name()

        if name in self._experiments:
            raise ValueError(f"Experiment '{name}' already registered")

        self._experiments[name] = experiment_class

    def create(self, name: str) -> BaseExperiment:
        """
        Create an experiment instance by name.

        Args:
            name: Experiment name

        Returns:
            BaseExperiment: New experiment instance

        Raises:
            ValueError: If experiment not found
        """
        if name not in self._experiments:
            raise ValueError(f"Experiment '{name}' not found")

        return self._experiments[name]()

    def get_all_names(self) -> List[str]:
        """
        Get list of all registered experiment names.

        Returns:
            list: Experiment names
        """
        return list(self._experiments.keys())

    def is_registered(self, name: str) -> bool:
        """
        Check if experiment is registered.

        Args:
            name: Experiment name

        Returns:
            bool: True if registered
        """
        return name in self._experiments

    def clear(self):
        """Clear all registrations (for testing)."""
        self._experiments.clear()


# Decorator for auto-registration
def register_experiment(cls):
    """
    Decorator to automatically register experiment classes.

    Usage:
        @register_experiment
        class MyExperiment(BaseExperiment):
            pass
    """
    registry = ExperimentRegistry()
    registry.register(cls)
    return cls


# Global registry instance
_registry = ExperimentRegistry()


def get_registry() -> ExperimentRegistry:
    """Get the global experiment registry."""
    return _registry
