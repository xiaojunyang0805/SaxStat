# SaxStat - Open Source Potentiostat

**An open-source, ESP32-based potentiostat for electrochemical analysis**

![Project Status](https://img.shields.io/badge/status-prototype-yellow)
![Hardware](https://img.shields.io/badge/hardware-v0.3-blue)
![Software](https://img.shields.io/badge/software-v0.3-blue)
![License](https://img.shields.io/badge/license-TBD-lightgrey)

---

## Overview

SaxStat is a versatile, low-cost potentiostat designed for electrochemical testing and research. Built around the ESP32 microcontroller and high-precision ADC/DAC components, it provides professional-grade measurements suitable for cyclic voltammetry and other electrochemical techniques.

**Current Status:** Prototype v03 hardware manufactured and functional. GUI software supports basic cyclic voltammetry with ongoing development for additional techniques.

## Features

### Hardware (Prototype v03)
- **Microcontroller:** ESP32-DevKitC-V4
- **DAC:** AD5761 (16-bit, voltage output)
- **ADC:** ADS1115 (16-bit, differential input)
- **Power Supply:** USB-powered with ICL7660 bipolar supply
- **Voltage Range:** -1.5V to +1.5V
- **Current Measurement:** Via transimpedance amplifier (TIA)
- **USB Communication:** 115200 baud serial interface

### Software
- **GUI Framework:** PyQt5
- **Real-time Plotting:** pyqtgraph
- **Supported Techniques:**
  - Cyclic Voltammetry (CV) ✓
  - Linear Sweep Voltammetry (LSV) - Planned
  - Chronoamperometry (CA) - Planned
  - Square Wave Voltammetry (SWV) - Planned
  - Differential Pulse Voltammetry (DPV) - Planned

## Project Structure

```
SaxStat/
├── hardware/              # PCB design files
│   ├── schematics/        # Schematic PDFs and EasyEDA project
│   ├── bom/               # Bill of Materials
│   └── 3d_models/         # 3D STEP models
├── firmware/              # ESP32 firmware (Arduino)
│   ├── prototype_v01/     # First prototype firmware
│   ├── prototype_v02/     # Second prototype firmware
│   └── prototype_v03/     # Current prototype firmware
├── software/              # Python GUI application
│   ├── saxstat_gui/       # Main application
│   ├── experiments/       # Experiment modules
│   └── utils/             # Utilities
├── docs/                  # Documentation
│   ├── hardware/          # Hardware documentation
│   ├── software/          # Software documentation
│   ├── user_guide/        # User guides
│   └── datasheets/        # Component datasheets
└── examples/              # Example test data
    └── test_data/         # Sample measurements
```

## Getting Started

### Hardware Requirements
- SaxStat PCB (prototype v03 or compatible)
- ESP32-DevKitC-V4 module
- USB cable for power and communication
- Electrochemical cell and electrodes

### Software Requirements
- Python 3.8 or higher
- Required Python packages (see `software/saxstat_gui/requirements.txt`)

### Installation

1. **Clone the repository:**
```bash
git clone https://github.com/yourusername/SaxStat.git
cd SaxStat
```

2. **Install Python dependencies:**
```bash
cd software/saxstat_gui
pip install -r requirements.txt
```

3. **Upload firmware to ESP32:**
   - Open `firmware/prototype_v03/SaxStat_V03_GUI_Test/SaxStat_V03_GUI_Test.ino` in Arduino IDE
   - Select ESP32 Dev Module as board
   - Upload to your ESP32

4. **Run the GUI:**
```bash
python SaxStat_GUI_V03.py
```

### Quick Start Guide

1. Connect your SaxStat device via USB
2. Launch the GUI application
3. Select the correct COM port and click "Connect"
4. (Optional) Click "Calibrate Offset" to measure baseline current
5. Set your experiment parameters (start/end voltage, scan rate, cycles)
6. Click "Start CV" to begin measurement
7. Save your data using "Save Data" button

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

## Software Architecture

The GUI is built using PyQt5 with a modular architecture to support multiple electrochemical techniques:

- **Serial Communication:** Manages USB connection to ESP32
- **Experiment Modules:** Individual classes for each technique (CV, LSV, etc.)
- **Data Processing:** Real-time data acquisition and processing
- **Plotting:** Live visualization using pyqtgraph
- **Export:** CSV format with experiment metadata

See `WORK_PLAN.md` for detailed development roadmap.

## Development Status

### Completed ✓
- [x] Hardware prototype v03 design and fabrication
- [x] ESP32 firmware for cyclic voltammetry
- [x] PyQt5 GUI with basic CV support
- [x] Real-time plotting (voltage-time and current-voltage)
- [x] Serial communication protocol
- [x] Data export to CSV
- [x] Offset current calibration

### In Progress 🔄
- [ ] Multi-experiment framework (LSV, CA, SWV, DPV)
- [ ] Enhanced data export (JSON, Excel)
- [ ] Advanced plotting features
- [ ] Configuration management
- [ ] Comprehensive documentation

### Planned 📋
- [ ] Automated peak detection
- [ ] Batch experiment processing
- [ ] Remote control API
- [ ] Mobile app integration

## Documentation

- **Work Plan:** See `WORK_PLAN.md` for detailed development plan
- **Folder Structure:** See `FOLDER_STRUCTURE.md` for project organization
- **Hardware Docs:** Coming soon in `docs/hardware/`
- **Software API:** Coming soon in `docs/software/`
- **User Guide:** Coming soon in `docs/user_guide/`

## Contributing

Contributions are welcome! This project is in active development. Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

See `CONTRIBUTING.md` (coming soon) for detailed guidelines.

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

**To Be Determined** - License will be added soon. Currently for research and educational use only.

## Contact

For questions, issues, or collaboration inquiries:
- **GitHub Issues:** [Create an issue](https://github.com/yourusername/SaxStat/issues)
- **Email:** xiaojunyang0805@gmail.com

## Citation

If you use SaxStat in your research, please cite:

```
[Citation format to be added]
```

---

**Disclaimer:** This is a research prototype. Users are responsible for validating measurements for their specific applications.

**Last Updated:** 2025-10-12
