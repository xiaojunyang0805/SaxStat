# SaxStat GUI v1 Development Work Plan

**Project:** SaxStat Portable Potentiostat
**Current Status:** Prototype v03 hardware complete, GUI v1 with 7 experiments complete, ready for hardware testing
**Reference:** DStat Potentiostat (University of Toronto - Wheeler Microfluidics Lab)
**Last Updated:** 2025-10-12

---

## Overview

This work plan outlines the complete development roadmap for SaxStat GUI v1, based on architectural analysis of the DStat reference project. The plan progresses from core architecture through advanced features, emphasizing modularity, extensibility, and reliability.

**Current Achievement:** Phase 1-3 complete, Phase 5.1 complete (7 experiments), Phase 4 in progress (~90% of v1.2)

---

## Phase 1: Core Architecture ✅ COMPLETED

**Duration:** Weeks 1-2 | **Status:** ✅ Complete

### 1.1 Project Organization ✅
- [x] Reorganize folder structure (hardware/, firmware/, software/, docs/, examples/)
- [x] Initialize git repository with comprehensive .gitignore
- [x] Create .gitattributes for line endings
- [x] Push to GitHub: https://github.com/xiaojunyang0805/SaxStat
- [x] Separate v0 (legacy) from v1 (new modular GUI)

### 1.2 Qt5 Project Structure ✅
- [x] Setup saxstat_gui_v1/ with modular architecture
- [x] Create main application entry point (main.py, run.py)
- [x] Implement main window with serial port selection
- [x] Add experiment selection dropdown
- [x] Build menu system (File, Settings, Help)

### 1.3 Hardware Communication ✅
- [x] Implement SerialManager with thread-safe async I/O (220 lines)
- [x] Background read thread for non-blocking serial communication
- [x] Qt signals for connected/disconnected/data_received/error events
- [x] Auto-reconnect functionality
- [x] Compatible with prototype v03 firmware protocol

### 1.4 Experiment Framework ✅
- [x] Define BaseExperiment abstract class (268 lines)
- [x] Template method pattern for experiment lifecycle
- [x] State machine (IDLE, RUNNING, COMPLETED, ERROR)
- [x] Qt signals for state_changed/data_received/progress/error
- [x] Abstract methods: get_name(), get_parameters(), validate_parameters(), generate_command(), process_data_point()

### 1.5 Real-time Plotting ✅
- [x] Implement PlotManager with pyqtgraph (186 lines)
- [x] High-performance real-time plotting
- [x] Auto-scaling and grid display
- [x] Plot export to PNG/JPEG
- [x] Dynamic axis labels based on experiment type

**Deliverables:**
- ✅ Functional GUI skeleton with all core components
- ✅ Main window with experiment selection and controls
- ✅ Thread-safe serial communication
- ✅ Real-time plotting framework
- ✅ Base experiment class ready for implementations

---

## Phase 2: Experiment Support ✅ COMPLETE

**Duration:** Weeks 3-4 | **Status:** ✅ Complete (CV, LSV, CA)

### 2.1 Experiment Registry Pattern ✅
- [x] Create ExperimentRegistry singleton (116 lines)
- [x] Auto-registration decorator `@register_experiment`
- [x] Dynamic experiment creation by name
- [x] List all available experiments

### 2.2 Parameter UI System ✅
- [x] Implement ParameterPanel widget (177 lines)
- [x] Dynamic widget generation from experiment parameter schema
- [x] Type-specific inputs (QSpinBox, QDoubleSpinBox, QLineEdit)
- [x] Min/max validation
- [x] Unit display
- [x] Configure button with validation feedback

### 2.3 Cyclic Voltammetry (CV) ✅
- [x] Implement CyclicVoltammetry experiment (293 lines)
- [x] Parameter schema (start_voltage, end_voltage, scan_rate, cycles, offset_current)
- [x] Firmware command generation: `START:<v1>:<v2>:<rate>:<cycles>`
- [x] Data processing: ADC → current calculation with TIA equation
- [x] Skip initial transient points (first 50)
- [x] Plot configuration: Applied Voltage (V) vs Current (µA)
- [x] Compatible with v0 firmware protocol

### 2.4 Additional Techniques ✅ COMPLETE
- [x] **Linear Sweep Voltammetry (LSV)** - Complete (280 lines)
  - Similar to CV but single sweep
  - Parameters: start, stop, scan_rate
  - Plot: Voltage vs Current

- [x] **Chronoamperometry (CA)** - Complete (285 lines)
  - Step potential over time
  - Parameters: potential, duration
  - Plot: Time vs Current

### 2.5 Hardware Testing ✅ READY, 🔄 NEEDS VALIDATION
- [x] GUI fully functional for testing
- [ ] Test CV with prototype v03 hardware
- [ ] Verify parameter ranges
- [ ] Validate data acquisition accuracy
- [ ] Test plot update performance
- [ ] Check error handling

**Deliverables:**
- ✅ CV experiment fully implemented and integrated
- ✅ Experiment registry system working
- ✅ Dynamic parameter UI system
- ✅ LSV, CA experiments complete
- 🔄 Hardware validation results

---

## Phase 3: Data Management ✅ COMPLETE

**Duration:** Weeks 5-6 | **Status:** ✅ Complete

### 3.1 Data Storage ✅
- [x] Implement DataManager with pandas (197 lines)
- [x] DataFrame-based data collection
- [x] Add metadata storage (experiment type, parameters, timestamp)
- [x] Clear and reset functionality

### 3.2 Data Export ✅
- [x] **CSV Export** - Basic with metadata as comments
  - Timestamp and parameters in header
  - Column names
  - Human-readable format

- [x] **Excel Export** - Framework ready
  - Multi-sheet support (data + metadata + analysis)
  - Requires openpyxl package

- [x] **JSON Export** - Structured format
  - Complete experiment data with nested structure
  - Includes metadata and parameters

### 3.3 Configuration Management ✅
- [x] Implement ConfigManager with JSON (196 lines)
- [x] Persistent settings in ~/.saxstat/config.json
- [x] Default values with merge-on-load
- [x] Hierarchical configuration:
  - Serial settings (baudrate, timeout, last_port)
  - UI preferences (window size, theme)
  - Experiment defaults (autosave, save_directory, last_experiment)
  - Calibration data (offset_current, tia_resistance, vref)

### 3.4 Parameter Save/Load ✅
- [x] Configuration save/load on application start/exit
- [x] Remember last used port
- [x] Restore window geometry
- [x] Recall last experiment type
- [ ] **Experiment parameter presets** (future enhancement)
  - Save/load specific experiment configurations
  - Default parameter sets per experiment type

### 3.5 Autosave Feature 🔄 FRAMEWORK READY
- [x] Autosave configuration option in config
- [ ] Implement automatic data save after experiment completion
- [ ] Configurable save directory
- [ ] Auto-naming with timestamp

**Deliverables:**
- ✅ Pandas-based data storage
- ✅ Three export formats (CSV, Excel framework, JSON)
- ✅ JSON configuration system
- ✅ Basic parameter persistence
- 🔄 Autosave (framework ready)

---

## Phase 4: Polish & Testing 🔄 IN PROGRESS

**Duration:** Weeks 7-8 | **Status:** 🔄 60% Complete

### 4.1 Error Handling & User Feedback ✅ MOSTLY DONE
- [x] Serial error handling with user messages
- [x] Parameter validation error dialogs
- [x] Experiment error signals
- [x] Status bar real-time updates
- [ ] Progress indicators for long operations
- [ ] Connection timeout handling
- [ ] Graceful handling of USB disconnection

### 4.2 Plot Export ✅ COMPLETE
- [x] PNG export
- [x] JPEG export
- [x] Menu action for save plot
- [ ] **PDF export** (future enhancement)
- [ ] **SVG export** for publications (future)

### 4.3 User Documentation 🔄 PARTIAL
- [x] README.md for v1 GUI (comprehensive)
- [x] Usage instructions
- [x] Architecture description
- [x] Development status
- [ ] **User Guide:**
  - [ ] Installation instructions
  - [ ] Getting started tutorial
  - [ ] Experiment-specific guides
  - [ ] Troubleshooting section
  - [ ] Calibration procedures
- [ ] **Screenshots and examples**

### 4.4 Comprehensive Testing 🔄 READY TO START
- [x] GUI functional testing (manual)
- [ ] **Hardware Testing:**
  - [ ] Basic CV functionality
  - [ ] Parameter range validation
  - [ ] Data acquisition accuracy
  - [ ] Long-term stability (1+ hour experiments)
  - [ ] Edge cases (USB disconnect, invalid params, etc.)
- [ ] **Unit Tests:**
  - [ ] Parameter validation
  - [ ] Data processing logic
  - [ ] Configuration management
- [ ] **Integration Tests:**
  - [ ] Experiment lifecycle
  - [ ] Serial communication
  - [ ] Data export formats

### 4.5 Packaging for Distribution 🔄 PLANNED
- [ ] PyInstaller executable (Windows)
- [ ] Application icon
- [ ] Installer script
- [ ] Dependency bundling
- [ ] Cross-platform builds (Linux, macOS)

**Deliverables:**
- ✅ Error handling framework
- ✅ Plot export
- 🔄 User documentation (partial)
- 🔄 Testing suite
- 🔄 Packaged executable

---

## Phase 5: Advanced Features 🔄 IN PROGRESS

**Duration:** Future releases | **Status:** 🔄 Phase 5.1 Complete (15%)

### 5.1 Additional Experiment Techniques ✅ COMPLETE
- [x] **Square Wave Voltammetry (SWV)** - Complete (357 lines)
  - Forward/reverse current measurements
  - Differential current calculation
  - Sensitivity for trace analysis (sub-micromolar)
  - Parameters: start, end, step_height, pulse_amplitude, frequency
  - Command: `SWV:<start>:<end>:<step>:<pulse>:<freq>`

- [x] **Differential Pulse Voltammetry (DPV)** - Complete (389 lines)
  - Pulse waveform generation
  - Baseline/pulse differential measurement
  - Excellent sensitivity (nanomolar range)
  - Parameters: start, end, step_height, pulse_amplitude, pulse_period, pulse_width
  - Command: `DPV:<start>:<end>:<step>:<pulse>:<period>:<width>`

- [x] **Normal Pulse Voltammetry (NPV)** - Complete (397 lines)
  - Pulses from constant baseline potential
  - Excellent discrimination against charging current
  - Parameters: baseline_potential, start, end, step_height, pulse_period, pulse_width
  - Command: `NPV:<baseline>:<start>:<end>:<step>:<period>:<width>`

- [x] **Potentiometry (POT)** - Complete (267 lines)
  - Open circuit potential monitoring
  - Time-based voltage measurement
  - Applications: pH, battery monitoring, corrosion
  - Parameters: duration, sample_interval, offset_voltage
  - Command: `POT:<duration>:<interval>`

- [ ] **Chronocoulometry (CC)** - Future
  - Charge integration over time

### 5.2 Data Analysis Tools ✅ COMPLETE
- [x] **Peak Detection:**
  - Automatic peak finding (scipy.signal.find_peaks)
  - Peak annotation on plots (red/blue markers)
  - Peak current and potential extraction
  - Configurable prominence, width, height, distance
  - 196 lines implemented

- [x] **Baseline Correction:**
  - Polynomial fitting
  - Spline interpolation
  - Linear baseline (endpoints or start/end segments)
  - Background subtraction
  - Orange dashed line visualization overlay
  - 197 lines implemented

- [x] **Integration:**
  - Charge calculation from current (Q = ∫I dt)
  - Trapezoidal and Simpson's rule
  - Range-based integration
  - Peak area calculation
  - Cumulative charge tracking
  - 173 lines implemented

- [x] **Smoothing Filters:**
  - Savitzky-Golay filter (peak-preserving)
  - Moving average
  - Exponential moving average
  - Gaussian smoothing
  - Green line visualization overlay
  - 186 lines implemented

- [x] **Analysis Panel UI:**
  - Method selection dropdowns
  - Parameter controls
  - Results text display
  - Interactive visualization overlays
  - 267 lines implemented

### 5.3 Method Builder
- [ ] **Sequential Experiments:**
  - Queue multiple experiments
  - Run automatically in sequence
  - Shared parameter inheritance

- [ ] **Method Editor:**
  - Drag-and-drop experiment sequence
  - Parameter templates
  - Conditional branching

- [ ] **Batch Processing:**
  - Multiple samples with same method
  - Auto-increment sample names
  - Summary report generation

### 5.4 Database Integration (Optional)
- [ ] SQLite database for experiment history
- [ ] Search and filter past experiments
- [ ] Experiment comparison tools
- [ ] Export database to CSV/Excel

### 5.5 Remote Control API (Optional)
- [ ] REST API for programmatic control
- [ ] Python API for scripting
- [ ] Remote monitoring dashboard
- [ ] Integration with lab automation systems

### 5.6 Advanced Plotting
- [ ] **Plot Overlays:**
  - Compare multiple experiments on same axes
  - Different line colors/styles
  - Shared or independent scales

- [ ] **Multi-Panel Layouts:**
  - Split view (2 plots)
  - Grid view (4+ plots)
  - Synchronized zooming/panning

- [ ] **Data Cursors:**
  - Show values at specific points
  - Delta measurements between two cursors
  - Export cursor data

- [ ] **3D Plots:**
  - Surface plots for multi-scan CV
  - Contour plots for time-series data

### 5.7 Calibration Features
- [ ] **Calibration Dialog:**
  - Guided calibration procedure
  - Offset current determination
  - TIA resistance measurement
  - Reference voltage verification

- [ ] **Calibration History:**
  - Track calibration over time
  - Drift analysis
  - Recalibration alerts

**Deliverables:**
- ✅ Phase 5.1: 4 advanced experiment types (SWV, DPV, NPV, POT)
- ✅ Phase 5.2: Data analysis suite (Peak Detection, Baseline Correction, Integration, Smoothing)
- 🔄 Phase 5.3: Method builder for automation
- 🔄 Phase 5.4: Optional database integration
- 🔄 Phase 5.5: Remote control API
- 🔄 Phase 5.6: Enhanced plotting capabilities
- 🔄 Phase 5.7: Calibration features

---

## Implementation Priorities

### Must Have (v1.0 Release)
1. ✅ Core GUI framework with Qt5
2. ✅ Serial communication with prototype v03
3. ✅ CV experiment fully functional
4. ✅ Real-time plotting
5. ✅ Data export (CSV, JSON)
6. ✅ Configuration persistence
7. 🔄 Hardware testing and validation
8. 🔄 User documentation

### Should Have (v1.1 - Polish & Production Ready)
1. ✅ LSV experiment
2. ✅ CA experiment
3. ✅ SWV and DPV experiments
4. ✅ NPV and POT experiments (7 experiments total)
5. ✅ Peak detection
6. ✅ Baseline correction
7. ✅ Integration/charge calculation
8. ✅ Smoothing filters
9. Excel export with openpyxl
10. Autosave functionality
11. Experiment parameter presets
12. Plot overlays (compare multiple experiments)
13. Calibration dialog
14. Package executable (PyInstaller)

**Remaining for v1.1:** 6 tasks (items 9-14)

### Nice to Have (v1.2 - Testing & Workflow Automation)
1. Progress indicators
2. Unit test suite
3. Method builder basics
4. Hardware testing suite (all 7 experiments)
5. Comprehensive user documentation
6. Publication-ready examples

### Future (v2.0+)
1. Database integration
2. Remote control API
3. Advanced analysis tools
4. 3D plotting
5. Lab automation integration

---

## Technical Stack

### Current Implementation
- **GUI Framework:** PyQt5
- **Plotting:** pyqtgraph (real-time), matplotlib (optional)
- **Data:** pandas DataFrames
- **Serial:** pyserial with threading
- **Config:** JSON with custom manager
- **Export:** CSV, JSON, Excel (openpyxl)

### Considered Alternatives
- **GUI:** PySide6, PyQt6 (future migration)
- **Async:** asyncio + aioserial (considered, not needed yet)
- **Validation:** pydantic (planned for parameter schemas)
- **Testing:** pytest, pytest-qt (planned)
- **Packaging:** PyInstaller, cx_Freeze

---

## Reference Resources

### DStat Project
- **Analysis Document:** `docs/software/DStat_Analysis.md` (1,066 lines)
- **GitLab:** https://microfluidics.utoronto.ca/gitlab/dstat/dstat-interface
- **GitHub Fork:** https://github.com/wheeler-microfluidics/dstat-interface-mrbox
- **Publication:** Ainla et al., "DStat: A Versatile, Open-Source Potentiostat," PLOS ONE, 2015

### SaxStat Documentation
- **Architecture:** `docs/software/SaxStat_v1_Architecture.md` (782 lines)
- **Development Log:** `DEV.md` (compact session summaries)
- **Work Plan:** `WORK_PLAN.md` (this document)
- **v1 README:** `software/saxstat_gui_v1/README.md`

### Technical References
- Bard & Faulkner, "Electrochemical Methods"
- PyQt5 Documentation: https://www.riverbankcomputing.com/static/Docs/PyQt5/
- pyqtgraph Documentation: https://pyqtgraph.readthedocs.io/
- pandas Documentation: https://pandas.pydata.org/docs/

---

## Timeline Summary

| Phase | Duration | Status | Completion |
|-------|----------|--------|------------|
| Phase 1: Core Architecture | Weeks 1-2 | ✅ Complete | 100% |
| Phase 2: Experiment Support | Weeks 3-4 | ✅ Complete | 100% (CV, LSV, CA) |
| Phase 3: Data Management | Weeks 5-6 | ✅ Complete | 100% |
| Phase 4: Polish & Testing | Weeks 7-8 | 🔄 In Progress | 70% |
| Phase 5: Advanced Features | Future | 🔄 In Progress | 30% (5.1 & 5.2 complete) |

**Total Time Invested:** ~10 hours (rapid prototyping)
**Estimated Remaining (v1.0):** 1 week (hardware testing, docs)
**Estimated Total (v1.2):** 4-6 weeks from start (all 7 experiments + 4 analysis tools)

---

## Success Criteria

### v1.0 MVP Release
- [ ] CV experiment tested and validated with hardware
- [ ] Data export working reliably
- [ ] Configuration persistence working
- [ ] User documentation complete
- [ ] No critical bugs
- [ ] Ready for daily lab use

### v1.1 Production Ready Release
**Completed (8/14 tasks - 57%):**
- [x] LSV and CA experiments functional
- [x] 7 experiment types supported (CV, LSV, CA, SWV, DPV, NPV, POT)
- [x] Data analysis tools (peak detection, baseline, integration, smoothing)

**Remaining (6/14 tasks - 43%):**
- [ ] Excel export implemented
- [ ] Autosave working
- [ ] Experiment parameter presets
- [ ] Plot overlays for experiment comparison
- [ ] Calibration dialog
- [ ] Standalone executable available

### v1.2 Testing & Workflow Release
- [ ] Progress indicators
- [ ] Unit test suite
- [ ] Method builder basics
- [ ] All experiments tested with hardware
- [ ] Comprehensive user documentation
- [ ] Publication-ready examples

### v2.0 Advanced Release
- [x] Data analysis tools functional (Phase 5.2 complete)
- [ ] Method builder operational
- [ ] Database integration
- [ ] Remote control API
- [ ] Used in multiple labs

---

## Development Notes

### Design Principles
1. **Modularity:** Each component has single responsibility
2. **Extensibility:** Easy to add new experiment types
3. **Reliability:** Robust error handling and validation
4. **Usability:** Clear UI with helpful feedback
5. **Performance:** Real-time plotting without lag

### Code Quality
- Type hints throughout
- Comprehensive docstrings
- Clear module separation
- Qt signals for loose coupling
- Configuration-driven behavior

### Testing Strategy
- Unit tests for validation logic
- Integration tests with mock hardware
- GUI tests with pytest-qt
- Hardware validation tests
- Performance benchmarking

---

## Notes for Next Session

**Immediate Priorities (v1.1 - 6 Remaining Tasks):**

**Priority Order:**
1. **Autosave functionality** (critical - prevents data loss)
2. **Experiment parameter presets** (high productivity boost)
3. **Excel export implementation** (openpyxl already in requirements)
4. **Plot overlays** (compare multiple experiments)
5. **Calibration dialog** (hardware accuracy)
6. **Package executable** (PyInstaller - do last)

**Next Phase (v1.2 - Testing & Workflow):**
1. Progress indicators for long experiments
2. Unit test suite (pytest, pytest-qt)
3. Method builder basics (sequential experiments)
4. Test all 7 experiments with actual prototype v03 hardware
5. Test Phase 5.2 analysis tools with real experimental data
6. Complete user documentation (installation, tutorials, troubleshooting)
7. Publication-ready examples

**Known Issues:**
- Excel export requires openpyxl (optional dependency)
- Calibration dialog not yet implemented (placeholder)
- Plot zoom/pan uses default pyqtgraph gestures (no custom controls)
- Autosave framework ready but not activated

**Future Considerations:**
- Consider migrating to PyQt6/PySide6 for long-term support
- Evaluate pydantic for parameter validation
- Plan for database integration architecture
- Design plugin system for custom experiments

---

**Document Version:** 2.4
**Last Updated:** 2025-10-12
**Status:** Phase 1-3 Complete, Phase 4 In Progress (70%), Phase 5.1-5.2 Complete (30% of Phase 5)

**Version Status:**
- **v1.0:** Core CV functionality (✅ COMPLETE)
- **v1.1:** Production Ready (🔄 57% - 8/14 tasks done, 6 remaining)
  - ✅ Complete: 7 experiments + 4 analysis tools
  - 🔄 Remaining: Autosave, presets, Excel export, overlays, calibration, packaging
- **v1.2:** Testing & Workflow (📋 PLANNED - 7 tasks)
  - Focus: Progress indicators, unit tests, method builder, hardware validation, documentation
