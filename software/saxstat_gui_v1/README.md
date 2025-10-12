# SaxStat GUI v1

Modern PyQt5-based GUI for the SaxStat portable potentiostat.

## Status
✅ **Functional** - Core features complete, ready for hardware testing

## Features

- **Modular Architecture:** Clean separation of concerns with dedicated modules for experiments, communication, data management, plotting, and configuration
- **Multi-Experiment Support:** Plugin-based experiment system with automatic registration
- **Real-time Plotting:** High-performance plotting with pyqtgraph
- **Data Export:** CSV, Excel, and JSON export formats
- **Configuration Management:** Persistent settings with JSON storage
- **Hardware Communication:** Thread-safe serial communication with ESP32

## Current Experiments

- **Cyclic Voltammetry (CV):** Full implementation matching v0 firmware protocol

## Quick Start

### Requirements

```bash
pip install -r requirements.txt
```

Required packages:
- PyQt5 >= 5.15.0
- pyserial >= 3.5
- numpy >= 1.21.0
- pyqtgraph >= 0.12.0
- pandas >= 1.3.0

### Running the GUI

```bash
python run.py
```

Or from parent directory:
```bash
python -m saxstat_gui_v1.main
```

## Usage

1. **Select Experiment:** Choose experiment type from dropdown (currently only CV)
2. **Connect Hardware:** Select serial port and click "Connect"
3. **Configure Parameters:** Adjust experiment parameters (start voltage, end voltage, scan rate, cycles)
4. **Start Experiment:** Click "Configure Experiment" then "Start Experiment"
5. **View Results:** Real-time plot displays during experiment
6. **Save Data:** Export data to CSV, Excel, or JSON after completion

## Architecture

```
saxstat_gui_v1/
├── gui/                    # PyQt5 UI components
│   ├── main_window.py      # Main application window (512 lines)
│   └── parameter_panel.py  # Dynamic parameter input panel (177 lines)
├── experiments/            # Experiment implementations
│   ├── base_experiment.py  # Abstract base class (268 lines)
│   ├── experiment_registry.py  # Registry pattern (116 lines)
│   └── cyclic_voltammetry.py   # CV implementation (293 lines)
├── communication/          # Hardware communication
│   └── serial_manager.py   # Thread-safe serial I/O (220 lines)
├── data/                   # Data management
│   └── data_manager.py     # Data collection and export (197 lines)
├── plotting/               # Plotting functionality
│   └── plot_manager.py     # Real-time plotting (186 lines)
├── config/                 # Configuration management
│   └── config_manager.py   # JSON-based settings (196 lines)
└── utils/                  # Utility functions
```

## Hardware Protocol

Compatible with prototype_v03 firmware:

**Commands:**
- `START:<start_v>:<end_v>:<scan_rate>:<cycles>` - Start CV experiment
- `STOP` - Stop current experiment
- `CALIBRATE` - Run calibration routine

**Data Format:**
- ADC values: 0-32767 (ADS1115 16-bit)
- Completion message: "CV complete."

**Hardware Specs:**
- Voltage range: -1.5V to +1.5V
- DAC: AD5761 (16-bit)
- ADC: ADS1115 (16-bit)
- TIA: 10kΩ resistor
- Reference: 1.0V

## Configuration

Configuration stored in `~/.saxstat/config.json`:

- Serial port settings (baudrate, timeout, last port)
- UI preferences (window size, theme)
- Experiment defaults (autosave, save directory)
- Calibration values (offset current, TIA resistance, Vref)

## Adding New Experiments

1. Create new file in `experiments/` directory
2. Inherit from `BaseExperiment`
3. Implement required methods:
   - `get_name()` - Return experiment name
   - `get_parameters()` - Define parameter schema
   - `validate_parameters()` - Validate parameter values
   - `generate_command()` - Create firmware command
   - `process_data_point()` - Parse and process data
   - `get_plot_config()` - Configure plot axes
4. Add `@register_experiment` decorator
5. Import in `experiments/__init__.py`

See `cyclic_voltammetry.py` for complete example.

## Development Status

**Phase 4: Multi-Experiment GUI** - ✅ Core functionality complete

- ✅ Experiment registry pattern
- ✅ Parameter panel with dynamic UI generation
- ✅ Main window with full component integration
- ✅ Serial communication with hardware
- ✅ Real-time plotting
- ✅ Data export (CSV, Excel, JSON)
- ✅ Configuration persistence
- 🔄 Hardware testing pending
- 🔄 Additional experiments pending (LSV, CA, SWV, DPV)

## Differences from v0

- **Modern Framework:** PyQt5 vs direct tkinter
- **Modular Design:** Separated concerns vs monolithic
- **Thread-safe Communication:** Background serial thread
- **Plugin System:** Registry pattern for experiments
- **Enhanced Plotting:** pyqtgraph vs matplotlib
- **Type Safety:** Pydantic-style validation
- **Configuration:** Persistent JSON settings

## Testing

To test without hardware:
1. Run `python run.py`
2. Select "Cyclic Voltammetry" experiment
3. Configure parameters
4. Serial connection will fail (expected)
5. UI and parameter validation can be tested

To test with hardware:
1. Connect prototype_v03 board via USB
2. Select correct COM port
3. Click "Connect"
4. Configure CV parameters
5. Click "Start Experiment"
6. Monitor real-time plot
7. Save data after completion

## Known Issues

- Excel export requires `openpyxl` package (install separately if needed)
- Calibration dialog not yet implemented (menu item shows "coming soon")
- Plot zoom/pan controls use default pyqtgraph mouse gestures

## References

- **v0 GUI:** `../saxstat_gui_v0/` - Original working implementation
- **DStat Analysis:** `../../docs/software/DStat_Analysis.md` - Reference architecture study
- **Architecture Doc:** `../../docs/software/SaxStat_v1_Architecture.md` - Design document
- **Firmware Protocol:** Based on prototype_v03 firmware

**Created:** 2025-10-12 | **Status:** Functional, ready for testing
