# SaxStat GUI v0 (Legacy)

**Original GUI based on SaxStat_GUI_V03.py**

## Status
- ✅ **Working** - Tested with prototype_v03 hardware
- 📦 **Archived** - Reference only, no further development
- 🔒 **Preserved** - Keep as reference for v1 development

## Features
- Cyclic Voltammetry (CV) support
- Real-time plotting (voltage-time and current-voltage)
- Serial communication with ESP32 (115200 baud)
- CSV data export
- Offset current calibration

## Files
- `SaxStat_GUI_V03.py` - Main GUI application
- `data_processing.py` - Data processing functions
- `gui_setup.py` - GUI setup utilities
- `plotting.py` - Plotting functions
- `serial_comm.py` - Serial communication
- `requirements.txt` - Python dependencies

## Hardware Compatibility
- **Firmware:** `firmware/prototype_v03/SaxStat_V03_GUI_Test/`
- **Protocol:** Custom serial protocol (115200 baud)
- **Commands:** START, STOP, CALIBRATE

## Usage Reference
This version remains as a reference for:
- Understanding firmware communication protocol
- Serial command structure
- Data processing algorithms
- GUI layout and user interaction patterns

## Note
**Do not modify this version.** All new development should be in `saxstat_gui_v1/`.

**Created:** 2025-10-12
