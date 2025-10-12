# SaxStat GUI Improvement Work Plan

**Project:** SaxStat Potentiostat PCB for Electrochemistry Testing
**Current Status:** Prototype v03 hardware complete, GUI functional for basic CV only
**Reference Project:** DStat (University of Toronto - Wheeler Microfluidics Lab)
**Date:** 2025-10-12

---

## Overview

This work plan outlines the roadmap for organizing the SaxStat project and enhancing the GUI software by leveraging the open-source DStat project as a reference. The current GUI (`D:\2025_SaxStat\prototype_v03\GUI_V03`) supports basic cyclic voltammetry and needs expansion to support multiple electrochemical techniques.

---

## Phase 1: Project Organization & Setup

### 1.1 Organize Folder Structure
**Goal:** Restructure project for better organization and GitHub readiness

**Proposed Structure:**
```
SaxStat/
├── hardware/              # PCB design files
│   ├── design_files/      # EasyEDA source files
│   ├── gerbers/           # Manufacturing files
│   ├── bom/               # Bill of materials
│   └── 3d_models/         # 3D models and enclosures
├── firmware/              # ESP32 firmware
│   ├── src/               # Source code
│   ├── lib/               # Libraries
│   └── platformio.ini     # Build configuration
├── software/              # GUI applications
│   ├── saxstat_gui/       # Main GUI application
│   ├── experiments/       # Experiment modules
│   ├── utils/             # Utility functions
│   └── requirements.txt   # Python dependencies
├── docs/                  # Documentation
│   ├── user_guide/        # User documentation
│   ├── hardware/          # Hardware documentation
│   ├── datasheets/        # Component datasheets
│   └── test_reports/      # Testing and calibration
├── reference/             # Reference designs
│   ├── DStat/             # DStat reference project
│   └── papers/            # Research papers
├── examples/              # Example data
│   └── test_data/         # Sample electrochemical data
├── .gitignore
├── README.md
└── LICENSE
```

**Current folders to reorganize:**
- `3D model/` → `hardware/3d_models/`
- `EasyEDA_file/` → `hardware/design_files/`
- `JLC parts/` → `hardware/bom/`
- `prototype_v03/GUI_V03/` → `software/saxstat_gui/`
- `Electrochemical Test/` → `examples/test_data/`
- `docs/` → Keep but organize better
- `SaxStat_private docs/` → Exclude from public GitHub

### 1.2 Initialize Git Repository
**Goal:** Set up version control with proper configuration

**Tasks:**
- [ ] Initialize git repository
- [ ] Create comprehensive `.gitignore`:
  - Python bytecode (`*.pyc`, `__pycache__/`)
  - Virtual environments (`venv/`, `.venv/`)
  - IDE files (`.idea/`, `.vscode/`)
  - Build artifacts (`build/`, `dist/`, `*.spec`)
  - Private documentation (`*_private*/`)
  - Temporary files (`*.tmp`, `*.bak`)
  - OS files (`.DS_Store`, `Thumbs.db`)
- [ ] Create initial commit with organized structure
- [ ] Set up `.gitattributes` for line endings

---

## Phase 2: DStat Analysis & Learning

### 2.1 Clone and Study DStat
**Goal:** Understand DStat architecture and implementation

**DStat Resources:**
- **GitLab:** https://microfluidics.utoronto.ca/gitlab/dstat/dstat-interface
- **GitHub Fork:** https://github.com/wheeler-microfluidics/dstat-interface-mrbox
- **Paper:** "DStat: A Versatile, Open-Source Potentiostat for Electroanalysis and Integration" (PLOS ONE, 2015)

**Tasks:**
- [ ] Clone DStat interface repository
- [ ] Review project structure and architecture
- [ ] Document key design patterns
- [ ] Identify reusable components

### 2.2 Analyze DStat Features
**Goal:** Extract relevant features for SaxStat implementation

**Key Features to Study:**

1. **Experiment Types:**
   - Cyclic Voltammetry (CV) ✓ (already implemented)
   - Linear Sweep Voltammetry (LSV)
   - Square Wave Voltammetry (SWV)
   - Differential Pulse Voltammetry (DPV)
   - Normal Pulse Voltammetry (NPV)
   - Chronoamperometry (CA)
   - Chronocoulometry (CC)

2. **Architecture Components:**
   - Parameter management system
   - Experiment class hierarchy
   - Data acquisition pipeline
   - Real-time plotting engine
   - Serial communication protocol
   - File I/O and data formats
   - Error handling and validation

3. **UI/UX Patterns:**
   - Parameter input forms
   - Experiment selection
   - Plot management
   - Status indicators
   - Data export workflow

**Deliverable:** Create `docs/DStat_Analysis.md` with findings

---

## Phase 3: GUI Architecture Design

### 3.1 Design Modular Architecture
**Goal:** Create scalable, maintainable GUI framework

**Core Components:**

1. **Experiment Module System**
   ```python
   # Base class for all experiments
   class BaseExperiment:
       - get_parameters()
       - validate_parameters()
       - generate_command()
       - process_data()
       - get_plots()

   # Specific experiments inherit
   class CyclicVoltammetry(BaseExperiment)
   class LinearSweep(BaseExperiment)
   class Chronoamperometry(BaseExperiment)
   ```

2. **Communication Layer**
   ```python
   class SerialManager:
       - connect()
       - disconnect()
       - send_command()
       - read_data()
       - handle_errors()
   ```

3. **Data Management**
   ```python
   class DataManager:
       - add_data_point()
       - get_data()
       - export_data()
       - load_data()
   ```

4. **Plot Manager**
   ```python
   class PlotManager:
       - create_plot()
       - update_plot()
       - export_plot()
       - overlay_plots()
   ```

**Deliverable:** Create `docs/Architecture_Design.md`

### 3.2 Define File Structure
**Goal:** Organize code for maintainability

```
software/saxstat_gui/
├── main.py                    # Application entry point
├── gui/
│   ├── main_window.py         # Main GUI window
│   ├── parameter_panel.py     # Parameter input panel
│   ├── plot_panel.py          # Plotting panel
│   └── status_bar.py          # Status display
├── experiments/
│   ├── base_experiment.py     # Base class
│   ├── cyclic_voltammetry.py  # CV experiment
│   ├── linear_sweep.py        # LSV experiment
│   ├── chronoamperometry.py   # CA experiment
│   └── square_wave.py         # SWV experiment
├── communication/
│   ├── serial_manager.py      # Serial communication
│   └── protocol.py            # Command protocol
├── data/
│   ├── data_manager.py        # Data handling
│   ├── processors.py          # Data processing
│   └── exporters.py           # Export formats
├── plotting/
│   ├── plot_manager.py        # Plot management
│   └── plot_widgets.py        # Custom plot widgets
├── config/
│   ├── settings.py            # Application settings
│   └── calibration.py         # Calibration data
└── utils/
    ├── validators.py          # Input validation
    └── helpers.py             # Helper functions
```

---

## Phase 4: GUI Implementation

### 4.1 Implement Multi-Experiment Framework
**Goal:** Extend GUI to support multiple electrochemical techniques

**Priority Order:**
1. **Linear Sweep Voltammetry (LSV)** - Similar to CV, good starting point
2. **Chronoamperometry (CA)** - Different plot type (current vs time)
3. **Square Wave Voltammetry (SWV)** - More complex waveform
4. **Differential Pulse Voltammetry (DPV)** - Advanced technique

**For Each Experiment:**
- [ ] Create experiment class
- [ ] Design parameter input UI
- [ ] Implement firmware command generation
- [ ] Add data processing logic
- [ ] Create appropriate plots
- [ ] Write unit tests

### 4.2 Enhance Data Export
**Goal:** Provide flexible data export options

**Features:**
- [ ] **CSV Export** (existing, enhance with metadata)
- [ ] **JSON Export** (structured data with full parameters)
- [ ] **Excel Export** (multiple sheets: data, parameters, plots)
- [ ] **Batch Export** (export multiple experiments)
- [ ] **Custom Templates** (user-defined export formats)

**Metadata to Include:**
- Experiment type and parameters
- Timestamp and duration
- Hardware configuration (TIA resistance, Vref, etc.)
- Calibration data
- Software version
- User notes

### 4.3 Advanced Plotting Features
**Goal:** Professional-grade data visualization

**Features:**
- [ ] **Plot Overlay:** Compare multiple experiments on same axes
- [ ] **Zoom/Pan Controls:** Interactive plot navigation
- [ ] **Plot Export:** Save as PNG, SVG, PDF
- [ ] **Customization:**
  - Axis labels and units
  - Line colors and styles
  - Grid options
  - Legend positioning
- [ ] **Multiple View Modes:**
  - Single plot
  - Split view (2 plots)
  - Grid view (4+ plots)
- [ ] **Data Cursors:** Show values at specific points
- [ ] **Peak Detection:** Automatic peak finding and annotation

### 4.4 Configuration Management
**Goal:** Persistent settings and easy experiment setup

**Features:**
- [ ] **Save/Load Experiment Parameters:**
  - Save current settings as preset
  - Load previous experiment configurations
  - Default parameter sets
- [ ] **User Preferences:**
  - Default COM port
  - Plot appearance settings
  - Export format preferences
  - Data save location
- [ ] **Calibration Data Storage:**
  - Offset current calibration
  - TIA resistance values
  - Reference voltage settings
  - Device-specific calibrations
- [ ] **Configuration File Format:** JSON-based for easy editing

---

## Phase 5: Documentation & Testing

### 5.1 Write Documentation
**Goal:** Comprehensive user and developer documentation

**User Documentation:**
- [ ] `README.md` - Project overview, quick start
- [ ] `docs/user_guide/installation.md` - Setup instructions
- [ ] `docs/user_guide/getting_started.md` - First experiment tutorial
- [ ] `docs/user_guide/experiments.md` - Guide for each experiment type
- [ ] `docs/user_guide/troubleshooting.md` - Common issues and solutions
- [ ] `docs/user_guide/calibration.md` - Calibration procedures

**Developer Documentation:**
- [ ] `docs/hardware/schematic_guide.md` - Hardware description
- [ ] `docs/hardware/firmware_protocol.md` - Serial communication protocol
- [ ] `docs/software/architecture.md` - Software architecture
- [ ] `docs/software/api_reference.md` - Code API documentation
- [ ] `docs/software/contributing.md` - Contribution guidelines

**Media:**
- [ ] Screenshots of GUI for each experiment type
- [ ] Workflow diagrams
- [ ] Example data plots

### 5.2 Hardware Testing
**Goal:** Validate software with prototype_v03 hardware

**Test Cases:**
- [ ] **Basic Functionality:**
  - Serial connection/disconnection
  - Parameter validation
  - Command transmission
  - Data reception
- [ ] **Each Experiment Type:**
  - Parameter range testing
  - Data acquisition accuracy
  - Plot update performance
  - Error handling
- [ ] **Long-term Stability:**
  - Extended experiments (1+ hour)
  - Multiple consecutive runs
  - Memory leak testing
- [ ] **Edge Cases:**
  - USB disconnection during experiment
  - Invalid parameter combinations
  - Buffer overflow scenarios
  - Rapid start/stop cycles

**Test Documentation:**
- [ ] Create test procedures
- [ ] Record test results
- [ ] Document known issues

---

## Phase 6: GitHub Deployment

### 6.1 Prepare for Public Release
**Goal:** Clean and organize for open-source release

**Tasks:**
- [ ] Review all code for sensitive information
- [ ] Ensure private documentation is excluded
- [ ] Add LICENSE file (choose appropriate: MIT, GPL, Apache)
- [ ] Create comprehensive README with:
  - Project description
  - Features list
  - Hardware requirements
  - Installation instructions
  - Quick start guide
  - Screenshots
  - Acknowledgments (DStat, references)
- [ ] Add CONTRIBUTING.md guidelines
- [ ] Create issue templates
- [ ] Set up GitHub Actions (optional):
  - Automated testing
  - Build executables
  - Documentation generation

### 6.2 Push to GitHub
**Goal:** Publish organized project

**Steps:**
- [ ] Create GitHub repository
- [ ] Add remote origin
- [ ] Push main branch
- [ ] Create release tags for versions
- [ ] Set up GitHub Pages for documentation (optional)
- [ ] Add topics/tags for discoverability:
  - potentiostat
  - electrochemistry
  - cyclic-voltammetry
  - open-hardware
  - pyqt5

---

## Current Status

### What's Working:
- ✓ Prototype v03 hardware manufactured and functional
- ✓ Basic CV GUI working (`D:\2025_SaxStat\prototype_v03\GUI_V03`)
- ✓ Serial communication with ESP32
- ✓ Real-time plotting (V-t and I-V plots)
- ✓ CSV data export
- ✓ Offset current calibration

### What Needs Improvement:
- ❌ Only supports Cyclic Voltammetry
- ❌ Limited data export options
- ❌ No experiment parameter save/load
- ❌ Basic plotting features only
- ❌ Project structure not organized for collaboration
- ❌ Documentation incomplete

---

## Reference Resources

### DStat Project
- **Main Site:** http://microfluidics.utoronto.ca/dstat
- **GitLab:** https://microfluidics.utoronto.ca/gitlab/dstat/dstat-interface
- **GitHub Fork:** https://github.com/wheeler-microfluidics/dstat-interface-mrbox
- **Publication:** Ainla et al., "DStat: A Versatile, Open-Source Potentiostat for Electroanalysis and Integration," PLOS ONE, 2015

### Related Projects
- **CheapStat:** Earlier open-source potentiostat
- **PassStat:** Another open-source alternative
- **PSoC-Stat:** PSoC-based potentiostat

### Technical References
- Bard & Faulkner, "Electrochemical Methods"
- Application notes on potentiostat design
- PyQt5 documentation
- Python serial communication guides

---

## Timeline Estimate

**Phase 1 (Organization):** 1-2 days
**Phase 2 (DStat Analysis):** 2-3 days
**Phase 3 (Architecture Design):** 2-3 days
**Phase 4 (Implementation):** 2-3 weeks
**Phase 5 (Documentation & Testing):** 1 week
**Phase 6 (GitHub Deployment):** 1-2 days

**Total Estimated Time:** 4-6 weeks

---

## Next Steps

1. Review and approve this work plan
2. Begin Phase 1: Organize folder structure
3. Initialize git repository
4. Clone and study DStat project
5. Design modular architecture
6. Start implementing LSV as first new experiment type

---

## Notes

- Keep `SaxStat_private docs/` excluded from public repository
- Ensure firmware protocol is well-documented for hardware-software integration
- Consider creating standalone executable with PyInstaller for end users
- Plan for backward compatibility if protocol changes
- Document hardware differences between prototype versions

---

**Last Updated:** 2025-10-12
