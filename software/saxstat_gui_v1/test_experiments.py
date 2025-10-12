#!/usr/bin/env python3
"""
Quick test script for experiment parameter validation

Tests CV, LSV, and CA experiments without hardware.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from saxstat_gui_v1.experiments import (
    get_registry,
    CyclicVoltammetry,
    LinearSweepVoltammetry,
    Chronoamperometry
)


def test_experiment(exp_class, test_params):
    """Test an experiment class with given parameters."""
    print(f"\n{'='*60}")
    print(f"Testing: {exp_class.__name__}")
    print(f"{'='*60}")

    # Create experiment instance
    exp = exp_class()
    print(f"Name: {exp.get_name()}")

    # Display parameter schema
    print(f"\nParameter Schema:")
    schema = exp.get_parameters()
    for param_name, param_def in schema.items():
        print(f"  {param_name}:")
        print(f"    type: {param_def['type'].__name__}")
        print(f"    default: {param_def['default']}")
        if 'min' in param_def:
            print(f"    range: [{param_def['min']}, {param_def['max']}]")
        print(f"    unit: {param_def.get('unit', 'N/A')}")
        print(f"    description: {param_def.get('description', 'N/A')}")

    # Test parameter validation
    print(f"\nTesting Parameters:")
    for desc, params in test_params:
        print(f"\n  Test: {desc}")
        print(f"  Params: {params}")
        try:
            if exp.validate_parameters(params):
                print(f"  ✅ Validation passed")
                # Test command generation
                exp.configure(params)
                cmd = exp.generate_command(params)
                print(f"  Command: {cmd}")
        except ValueError as e:
            print(f"  ❌ Validation failed: {e}")

    # Test plot configuration
    print(f"\nPlot Configuration:")
    plot_config = exp.get_plot_config()
    for key, value in plot_config.items():
        print(f"  {key}: {value}")


def main():
    """Run all experiment tests."""
    print("SaxStat Experiment Parameter Validation Test")
    print("=" * 60)

    # Check registry
    registry = get_registry()
    exp_names = registry.get_all_names()
    print(f"\nRegistered Experiments: {exp_names}")

    # Test CV
    cv_tests = [
        ("Valid CV parameters", {
            'start_voltage': -0.5,
            'end_voltage': 0.5,
            'scan_rate': 0.05,
            'cycles': 3,
            'offset_current': 0.0
        }),
        ("Out of range voltage", {
            'start_voltage': -2.0,  # Out of range!
            'end_voltage': 0.5,
            'scan_rate': 0.05,
            'cycles': 3
        }),
        ("Equal start/end voltages", {
            'start_voltage': 0.5,
            'end_voltage': 0.5,  # Should fail!
            'scan_rate': 0.05,
            'cycles': 3
        }),
    ]
    test_experiment(CyclicVoltammetry, cv_tests)

    # Test LSV
    lsv_tests = [
        ("Valid LSV parameters", {
            'start_voltage': -0.5,
            'end_voltage': 0.5,
            'scan_rate': 0.1,
            'offset_current': 0.0
        }),
        ("High scan rate", {
            'start_voltage': 0.0,
            'end_voltage': 1.0,
            'scan_rate': 0.2,
        }),
        ("Missing parameter", {
            'start_voltage': -0.5,
            # Missing end_voltage!
            'scan_rate': 0.05,
        }),
    ]
    test_experiment(LinearSweepVoltammetry, lsv_tests)

    # Test CA
    ca_tests = [
        ("Valid CA parameters", {
            'potential': 0.3,
            'duration': 30.0,
            'sample_interval': 0.1,
            'offset_current': 0.0
        }),
        ("Long duration CA", {
            'potential': -0.5,
            'duration': 120.0,
            'sample_interval': 1.0,
        }),
        ("Invalid sample interval", {
            'potential': 0.0,
            'duration': 10.0,
            'sample_interval': 15.0,  # Larger than duration!
        }),
    ]
    test_experiment(Chronoamperometry, ca_tests)

    print(f"\n{'='*60}")
    print("Test Complete!")
    print(f"{'='*60}\n")


if __name__ == '__main__':
    main()
