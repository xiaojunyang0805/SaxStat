# SaxStat - Open Source Potentiostat

**An open-source, ESP32-based potentiostat for electrochemical analysis**

![Project Status](https://img.shields.io/badge/status-concluded-orange)
![Hardware](https://img.shields.io/badge/hardware-v0.3-blue)
![Software](https://img.shields.io/badge/software-v1.2-brightgreen)
![License](https://img.shields.io/badge/license-MIT-green)

> **Project Status:** This project has been concluded as a principle-exploration hobby project. The hardware has a known negative-voltage limitation (see [Known Limitation](#known-limitation)) that would require a PCB redesign to resolve. The software (GUI v1.2) and firmware (v03) are functional within the documented voltage range.

---

## Overview

SaxStat is a versatile, low-cost potentiostat designed for electrochemical testing and research. Built around the ESP32 microcontroller and high-precision ADC/DAC components, it provides professional-grade measurements suitable for cyclic voltammetry and other electrochemical techniques.

**Current Status:** Project concluded. Prototype v03 hardware manufactured and functional within -0.2V to +1.5V range. GUI v1.2 software with 7 experiment types, 4 analysis tools, and comprehensive data management features. See [Known Limitation](#known-limitation) for voltage range details.

## Features

### Hardware (Prototype v03)
- **Microcontroller:** ESP32-DevKitC-V4
- **DAC:** AD5761 (16-bit, voltage output)
- **ADC:** ADS1115 (16-bit, differential input)
- **Power Supply:** USB-powered with ICL7660 bipolar supply
- **Voltage Range:** -0.2V to +1.5V (limited by analog switch body diode; see [Known Limitation](#known-limitation))
- **Current Measurement:** Via transimpedance amplifier (TIA)
- **Gain Selection:** Two modes via TS5A3160 analog switches (GPIO 33/25)
  - 10⁴ V/A (10kΩ TIA) — ±500 µA range
  - 10⁶ V/A (1MΩ TIA) — ±100 nA range
- **USB Communication:** 115200 baud serial interface

### Software (v1.2 - Production Ready)
- **GUI Framework:** PyQt5 with modern styling
- **Real-time Plotting:** pyqtgraph with high performance
- **Data Processing:** pandas for efficient data handling
- **Export Formats:** CSV, JSON, Excel (formatted)

**Supported Techniques (7 total):**
  - ✅ Cyclic Voltammetry (CV)
  - ✅ Linear Sweep Voltammetry (LSV)
  - ✅ Chronoamperometry (CA)
  - ✅ Square Wave Voltammetry (SWV)
  - ✅ Differential Pulse Voltammetry (DPV)
  - ✅ Normal Pulse Voltammetry (NPV)
  - ✅ Potentiometry (POT)

**Data Analysis Tools (4 total):**
  - ✅ Peak Detection (automatic with configurable parameters)
  - ✅ Baseline Correction (polynomial, spline, linear)
  - ✅ Integration (charge calculation with multiple methods)
  - ✅ Smoothing Filters (Savitzky-Golay, moving average, Gaussian)

**Productivity Features:**
  - ✅ Autosave with configurable formats and patterns
  - ✅ Parameter presets (save/load/delete per experiment)
  - ✅ Plot overlays (compare up to 5 experiments with legend)
  - ✅ Hardware calibration dialog
  - ✅ Gain selection (10⁴/10⁶ V/A) with GUI toggle
  - ✅ Experiment history (automatic storage)

## Project Structure

```
SaxStat/
├── hardware/              # PCB design files
│   ├── schematics/        # Schematic PDFs and EasyEDA project
│   ├── bom/               # Bill of Materials
│   └── gerbers_private/   # Manufacturing files (private)
├── firmware/              # ESP32 firmware (Arduino)
│   ├── prototype_v01/     # First prototype firmware
│   ├── prototype_v02/     # Second prototype firmware
│   └── prototype_v03/     # Current prototype firmware (production)
├── software/              # Python GUI application
│   ├── saxstat_gui_v0/    # Legacy v0 GUI
│   └── saxstat_gui_v1/    # v1.2 Production GUI (modular architecture)
│       ├── experiments/   # 7 experiment implementations
│       ├── gui/           # PyQt5 UI components
│       ├── data/          # Data management with pandas
│       ├── plotting/      # Real-time plotting
│       ├── config/        # Configuration management
│       ├── communication/ # Serial communication
│       └── analysis/      # Data analysis tools
├── docs/                  # Documentation
│   ├── software/          # Software architecture and DStat analysis
│   └── datasheets/        # Component datasheets
└── WORK_PLAN.md           # Detailed development roadmap (v2.5)
```

## Getting Started

### Hardware Requirements
- SaxStat PCB (prototype v03 or compatible)
- ESP32-DevKitC-V4 module
- USB cable for power and communication
- Electrochemical cell and electrodes

### Software Requirements
- **Option A (Recommended):** Use the standalone executable — no Python needed
- **Option B (Development):** Python 3.8+ with packages from `software/saxstat_gui_v1/requirements.txt`

### Installation

#### Option A: Standalone Executable (Recommended)

1. **Download** `SaxStat.exe` from `software/dist/` (or the [Releases](https://github.com/xiaojunyang0805/SaxStat/releases) page)
2. **Upload firmware to ESP32:**
   - Open `firmware/prototype_v03/SaxStat_V03_GUI_Test_02/SaxStat_V03_GUI_Test_02.ino` in Arduino IDE
   - Select ESP32 Dev Module as board
   - Upload to your ESP32
3. **Run** `SaxStat.exe` — no installation required

#### Option B: Run from Source

1. **Clone the repository:**
```bash
git clone https://github.com/xiaojunyang0805/SaxStat.git
cd SaxStat
```

2. **Install Python dependencies:**
```bash
cd software/saxstat_gui_v1
pip install -r requirements.txt
```

3. **Upload firmware to ESP32:** (same as Option A step 2)

4. **Run the GUI:**
```bash
cd software
python -m saxstat_gui_v1.main
```

### Quick Start Guide

1. **Connect Hardware:** Connect your SaxStat device via USB
2. **Launch GUI:** Run `python -m saxstat_gui_v1.main` from software directory
3. **Select Port:** Choose COM port and click "Connect"
4. **Choose Experiment:** Select from 7 experiment types (CV, LSV, CA, SWV, DPV, NPV, POT)
5. **Configure Parameters:** Set experiment parameters or load a preset
6. **Select Gain:** Choose 10⁴ V/A (±500 µA) or 10⁶ V/A (±100 nA) in the Gain Selection panel
7. **Calibrate (Optional):** Settings → Calibration to configure hardware parameters
8. **Run Experiment:** Click "Start Experiment"
9. **Analyze Data:** Use Analysis → Data Analysis Tools for peak detection, baseline correction, etc.
10. **Save Results:** Data auto-saves if enabled, or manually save with File → Save Data
11. **Compare Runs:** Use View → Compare Experiments to overlay multiple runs

## Hardware Design

### Key Components
- **AD5761:** 16-bit DAC for precise voltage control
- **ADS1115:** 16-bit ADC for current measurement
- **LMC6484:** Quad op-amp for signal conditioning
- **ICL7660:** Charge pump for bipolar supply generation
- **ADR510/ADR525:** Precision voltage references

### Schematic
Schematic files are available in `hardware/schematics/`. The design uses EasyEDA and can be opened with the provided `.eprj` file.

**Note:** PCB Gerber files are not included in the public repository. Contact the author if you need manufacturing files.

## Software Architecture (v1.2)

The GUI v1.2 is built using PyQt5 with a professional modular architecture:

**Core Components:**
- **Experiment Framework:** BaseExperiment class with template method pattern
- **Experiment Registry:** Auto-registration system for experiment types
- **Serial Communication:** Thread-safe async I/O with SerialManager
- **Data Management:** pandas-based DataManager with history storage
- **Plot Manager:** High-performance real-time plotting with pyqtgraph
- **Configuration:** JSON-based ConfigManager with presets support
- **Analysis Tools:** scipy-based peak detection, baseline correction, integration, smoothing

**Key Features:**
- Modular experiment design - easy to add new techniques
- Type-safe parameter validation with schemas
- Real-time plotting without blocking
- Professional Excel export with formatted sheets
- Autosave with configurable patterns and formats
- Parameter presets per experiment type
- Experiment history with comparison overlays
- Hardware calibration management

See `docs/software/SaxStat_v1_Architecture.md` for v1.2 architecture details.

## Known Limitation

**Negative Voltage Range Restricted (Body Diode Clamping)**

The TS5A3160 analog switches (U5/U6) used for TIA gain selection have internal body diodes that clamp to the GND rail. When the TIA output goes below approximately -0.25V (which happens when VRAMP is negative), these body diodes forward-bias and inject exponentially increasing parasitic current into the measurement — indistinguishable from real electrochemical current.

**Impact:** Usable voltage range is limited to **-0.2V to +1.5V** (originally designed for ±1.5V).

**Root cause:** The TS5A3160 is a single-supply switch (+5V/GND). Replacing it with a bipolar-supply switch (e.g., ADG1419, ±5V) would fix the issue, but requires a PCB redesign.

For the full technical analysis, see [`docs/hardware/Body_Diode_Clamping_Issue.md`](docs/hardware/Body_Diode_Clamping_Issue.md).

## Development Status

### v1.2 — Final Release (Project Concluded)

**Completed:**
- [x] Hardware prototype v03 design and fabrication
- [x] ESP32 firmware for all experiment types
- [x] 7 experiment types (CV, LSV, CA, SWV, DPV, NPV, POT)
- [x] 4 data analysis tools (peaks, baseline, integration, smoothing)
- [x] Professional Excel export with formatted sheets
- [x] Autosave with preferences dialog
- [x] Parameter presets (per-experiment save/load/delete)
- [x] Plot overlays (compare up to 5 experiments)
- [x] Hardware calibration dialog
- [x] Gain selection (10⁴/10⁶ V/A) with firmware GPIO control and GUI toggle
- [x] Real-time plotting (dual plots)
- [x] Thread-safe serial communication
- [x] Configuration management with JSON
- [x] Experiment history storage
- [x] Standalone executable (`SaxStat.exe` via PyInstaller)
- [x] Body diode clamping issue documented and voltage-limited as workaround

**Not pursued (project concluded):**
- Hardware validation testing across all 7 experiments
- Unit test suite
- Full negative voltage range (requires PCB redesign with bipolar-supply switches)

## Documentation

- **Work Plan:** See `WORK_PLAN.md` (v2.5) for detailed development roadmap
- **v1.2 GUI:** See `software/saxstat_gui_v1/README.md` for architecture and implementation
- **Software Analysis:** See `docs/software/DStat_Analysis.md` for reference project analysis
- **Architecture:** See `docs/software/SaxStat_v1_Architecture.md` for design decisions
- **Hardware Docs:** See `hardware/schematics/` for PCB design files
- **User Guide:** In-app help via Help → About, comprehensive docs coming in v1.2

## Contributing

This project is no longer under active development, but the code is available under the MIT license. Feel free to fork and adapt for your own use.

## References & Acknowledgments

This project was inspired by and references the following open-source potentiostats:

1. **DStat** - Wheeler Microfluidics Laboratory, University of Toronto
   - Ainla, A., et al. (2015). "DStat: A Versatile, Open-Source Potentiostat for Electroanalysis and Integration." *PLOS ONE*.
   - Project: http://microfluidics.utoronto.ca/dstat
   - Repository: https://microfluidics.utoronto.ca/gitlab/dstat/dstat-interface

2. **CheapStat** - Earlier open-source potentiostat design

3. **PassStat** - Open-source potentiostat for electrochemical sensing

### Key Literature
- Bard, A. J., & Faulkner, L. R. *Electrochemical Methods: Fundamentals and Applications*

## License

This project is licensed under the [MIT License](LICENSE).

## Contact

For questions, issues, or collaboration inquiries:
- **GitHub Issues:** [Create an issue](https://github.com/xiaojunyang0805/SaxStat/issues)
- **Email:** xiaojunyang0805@gmail.com

## Citation

If you use SaxStat in your research, please cite:

```
Yang, X. (2025). SaxStat: An Open-Source ESP32-Based Potentiostat for Electrochemical Analysis.
GitHub repository: https://github.com/xiaojunyang0805/SaxStat
```

---

**Disclaimer:** This is a research prototype. Users are responsible for validating measurements for their specific applications.

**Last Updated:** 2026-03-23 (Project Concluded)
