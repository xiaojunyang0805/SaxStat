# SaxStat Development Log

Quick reference log for tracking development progress.

---

## 2025-10-12 - Initial Project Setup

**Duration:** ~2 hours | **Status:** ✅ Complete

### Completed
- ✅ Created project work plan (WORK_PLAN.md)
- ✅ Reorganized folder structure (hardware/, firmware/, software/, docs/, examples/)
- ✅ Removed old duplicate folders (7 folders cleaned up)
- ✅ Initialized git repository with .gitignore and .gitattributes
- ✅ Created README.md and requirements.txt
- ✅ Made initial commit (d5bc61b) - 74 files, 45k+ lines
- ✅ Created GitHub repository: https://github.com/xiaojunyang0805/SaxStat
- ✅ Pushed to GitHub successfully

### Key Decisions
- **Private content excluded:** SaxStat_private docs/, gerbers_private/
- **Public content:** Schematics, BOM, 3D models, firmware, software
- **Repository visibility:** Public

### Issues Resolved
- GitHub CLI not available → Used GitHub API with token
- Line ending warnings → Created .gitattributes

### Stats
- Files: 74 | Lines: 45,215 | Commit: 1 | Time: 2h

---

## 2025-10-12 - DStat Analysis & GUI v1 Setup

**Duration:** ~1 hour | **Status:** ✅ Complete

### Completed
- ✅ Reorganized software structure (v0 archived, v1 created)
- ✅ Cloned DStat reference project to private/Reference/
- ✅ Analyzed DStat architecture (1,066 line analysis document)
- ✅ Identified 8 experiment types (CV, LSV, CA, SWV, DPV, PD, POT, OC)
- ✅ Documented key design patterns and architectural insights

### Key Decisions
- **v0 preserved:** Original GUI kept as reference for firmware protocol
- **v1 structure:** Modular folders (gui/, experiments/, communication/, data/, plotting/, config/)
- **Modernization:** PyQt6, asyncio, pydantic, pyqtgraph for v1
- **DStat insights:** Registry pattern, process isolation, property-based parameters

### Analysis Highlights
- **Document:** `docs/software/DStat_Analysis.md` (35KB)
- **Architecture:** Modular design with clean separation of concerns
- **Patterns:** Strategy, Registry, Template Method
- **Experiments:** 8 types with parameter validation
- **Communication:** Process-isolated hardware interface

### Stats
- DStat analyzed: 1,066 lines of documentation | Analysis: 35KB | v1 folders: 7

---

## 2025-10-12 - SaxStat GUI v1 Architecture Design

**Duration:** ~30 min | **Status:** ✅ Complete

### Completed
- ✅ Created SaxStat v1 architecture document (782 lines, 66KB)
- ✅ Designed modular component system (6 core components)
- ✅ Defined 5-phase implementation plan (9 weeks)
- ✅ Created 700+ lines of implementation examples
- ✅ Specified communication protocol and data flow

### Key Decisions
- **Stack:** PyQt5, asyncio, pydantic, pyqtgraph, pandas
- **Patterns:** MVC, Template Method, Registry, Strategy, Observer
- **Structure:** 32 files across 7 folders
- **First target:** CV matching v0 functionality

### Architecture Highlights
- **Document:** `docs/software/SaxStat_v1_Architecture.md` (66KB)
- **Components:** BaseExperiment, SerialManager, DataManager, PlotManager, ConfigManager
- **Protocol:** Based on v0 firmware (START, STOP, CALIBRATE)
- **Async I/O:** Modern threading model vs DStat's multiprocessing

### Stats
- Architecture doc: 782 lines | Implementation examples: 700+ lines | Ready to code!

---

## 2025-10-12 - Phase 1: Core Architecture - File Structure

**Duration:** ~20 min | **Status:** ✅ Complete

### Completed
- ✅ Created 15 Python file templates (1,142 lines)
- ✅ Implemented BaseExperiment abstract class (268 lines)
- ✅ Implemented SerialManager with async I/O (220 lines)
- ✅ Implemented DataManager with pandas (197 lines)
- ✅ Implemented PlotManager with pyqtgraph (186 lines)
- ✅ Implemented ConfigManager with JSON (196 lines)
- ✅ Set up all __init__.py files and module structure

### Key Features
- **BaseExperiment:** Template method pattern, state machine, Qt signals
- **SerialManager:** Thread-safe serial comm, auto-reconnect
- **DataManager:** CSV/Excel/JSON export, metadata, statistics
- **PlotManager:** Real-time plotting, auto-scaling, image export
- **ConfigManager:** Persistent settings, calibration storage

### Stats
- Files: 15 | Lines: 1,142 | Modules: 7 (gui, experiments, communication, data, plotting, config, utils)

---

## 2025-10-12 - Phase 2 & 3: Experiment Support & Data Management

**Duration:** ~1 hour | **Status:** ✅ Core functionality complete

### Completed
- ✅ Created experiment registry pattern (116 lines)
- ✅ Updated CyclicVoltammetry with auto-registration decorator
- ✅ Implemented ParameterPanel widget (177 lines)
- ✅ Fully implemented MainWindow (512 lines)
- ✅ Connected all components (serial, data, plot, config, experiments)
- ✅ Added experiment selection, serial connection, parameter input
- ✅ Implemented start/stop/save controls
- ✅ Created menu bar with File, Settings, Help menus

### Key Features
- **Experiment Registry:** Singleton pattern with auto-registration decorator
- **ParameterPanel:** Dynamic UI generation from experiment parameter schema
- **MainWindow:** Complete orchestration of all components
  - Experiment selection combo box
  - Serial port connection with auto-refresh
  - Dynamic parameter inputs based on selected experiment
  - Real-time plotting with pyqtgraph
  - Data export (CSV, Excel, JSON)
  - Plot export (PNG, JPEG)
  - Configuration persistence
  - Experiment state management

### Architecture Highlights
- Signal-based communication between components
- Type-safe parameter validation
- Automatic UI state management based on experiment state
- Configuration auto-save for window geometry and last selections

### Stats
- New files: 3 (experiment_registry.py, parameter_panel.py, run.py)
- Modified files: 6 (cyclic_voltammetry.py, main_window.py, experiments/__init__.py, gui/__init__.py, README.md, DEV.md)
- Lines added: ~800 lines of core functionality + 180 lines of documentation
- **GUI v1 is now functional!** Ready for hardware testing

### Application Features
- Experiment selection dropdown (auto-populated from registry)
- Serial port connection with auto-refresh
- Dynamic parameter inputs (adapts to selected experiment)
- Real-time plotting with pyqtgraph
- Start/Stop/Save experiment controls
- Data export: CSV, Excel, JSON
- Plot export: PNG, JPEG
- Configuration persistence (~/.saxstat/config.json)
- Menu bar: File, Settings, Help
- Status bar with real-time messages

### Technical Implementation
- **Signal-based architecture:** Qt signals connect all components
- **Auto UI generation:** Parameters → widgets automatically
- **Plugin system:** `@register_experiment` decorator for new experiments
- **Thread-safe serial:** Background thread for hardware communication
- **Type-safe validation:** Parameter schemas enforce types/ranges
- **State machine:** Experiment state controls UI state

### Ready to Test
Run with: `python run.py` from saxstat_gui_v1/ directory
- Without hardware: UI and parameter validation testable
- With hardware: Full CV experiment workflow (connect → configure → start → plot → save)

---

## 2025-10-12 - Phase 2.4: Additional Experiment Techniques

**Duration:** ~30 min | **Status:** ✅ Complete

### Completed
- ✅ Implemented Linear Sweep Voltammetry (LSV) experiment (280 lines)
- ✅ Implemented Chronoamperometry (CA) experiment (285 lines)
- ✅ Updated experiments/__init__.py to export new experiments
- ✅ Created test_experiments.py for validation testing

### LSV Implementation
- **Parameters:** start_voltage, end_voltage, scan_rate, offset_current
- **Command:** `START:<start>:<end>:<rate>:1` (single sweep)
- **Data processing:** Linear voltage sweep, same as CV but no cycling
- **Plot:** Applied Voltage (V) vs Current (µA)
- **Line count:** 280 lines with full validation

### CA Implementation
- **Parameters:** potential, duration, sample_interval, offset_current
- **Command:** Implemented as CV with start=end for v03 compatibility
- **Data processing:** Constant potential, measures current vs time
- **Plot:** Time (s) vs Current (µA) - Different axis from voltammetry!
- **Line count:** 285 lines with full validation
- **Note:** Can use dedicated `CA:<potential>:<duration>` if firmware supports

### Key Features
- **Auto-registration:** Both experiments use `@register_experiment` decorator
- **Parameter validation:** Min/max ranges, type checking, logical validation
- **Firmware compatibility:** Commands compatible with prototype v03
- **Plot configuration:** CA uses time axis, LSV/CV use voltage axis
- **TIA equation:** Same current calculation for all techniques

### Architecture Notes
- LSV: Similar to CV but performs single sweep
- CA: Different plot type (time-based instead of voltage-based)
- Both inherit from BaseExperiment with template method pattern
- Registry automatically detects and registers both experiments

### Stats
- New files: 3 (linear_sweep.py, chronoamperometry.py, test_experiments.py)
- Modified files: 1 (experiments/__init__.py)
- Lines added: ~630 lines (280 LSV + 285 CA + 65 test script)
- **Total experiments: 3** (CV, LSV, CA)

---

## 2025-10-12 - Phase 5.1: Advanced Experiment Techniques

**Duration:** ~45 min | **Status:** ✅ Complete

### Completed
- ✅ Implemented Square Wave Voltammetry (SWV) experiment (357 lines)
- ✅ Implemented Differential Pulse Voltammetry (DPV) experiment (389 lines)
- ✅ Implemented Normal Pulse Voltammetry (NPV) experiment (397 lines)
- ✅ Implemented Potentiometry (POT) experiment (267 lines)
- ✅ Updated experiments/__init__.py to export all Phase 5 experiments

### SWV Implementation
- **Parameters:** start_voltage, end_voltage, step_height, pulse_amplitude, frequency
- **Command:** `SWV:<start>:<end>:<step>:<pulse>:<freq>`
- **Data processing:** Forward/reverse pulse measurements with differential current
- **Plot:** Applied Voltage (V) vs Differential Current (µA)
- **Line count:** 357 lines with full validation
- **Key feature:** Enhanced sensitivity for trace analysis (sub-micromolar)

### DPV Implementation
- **Parameters:** start_voltage, end_voltage, step_height, pulse_amplitude, pulse_period, pulse_width
- **Command:** `DPV:<start>:<end>:<step>:<pulse>:<period>:<width>`
- **Data processing:** Baseline/pulse current measurements with differential calculation
- **Plot:** Applied Voltage (V) vs Differential Current (µA)
- **Line count:** 389 lines with full validation
- **Key feature:** Excellent sensitivity for trace analysis (nanomolar range)

### NPV Implementation
- **Parameters:** baseline_potential, start_voltage, end_voltage, step_height, pulse_period, pulse_width
- **Command:** `NPV:<baseline>:<start>:<end>:<step>:<period>:<width>`
- **Data processing:** Current measured at end of each pulse from baseline
- **Plot:** Pulse Voltage (V) vs Current (µA)
- **Line count:** 397 lines with full validation
- **Key feature:** Excellent discrimination against charging current

### POT Implementation
- **Parameters:** duration, sample_interval, offset_voltage
- **Command:** `POT:<duration>:<interval>`
- **Data processing:** Open-circuit potential monitoring over time
- **Plot:** Time (s) vs Potential (V) - Different from current-based techniques!
- **Line count:** 267 lines with full validation
- **Key applications:** pH measurements, battery monitoring, corrosion studies

### Key Features
- **Auto-registration:** All experiments use `@register_experiment` decorator
- **Parameter validation:** Min/max ranges, type checking, logical validation
- **Firmware compatibility:** Commands compatible with prototype v03
- **Plot configuration:** Each experiment defines appropriate axis labels
- **Differential techniques:** SWV, DPV calculate differential currents for enhanced sensitivity
- **Time-based plots:** CA and POT use time axis instead of voltage axis

### Architecture Notes
- SWV: Staircase + square wave modulation, forward/reverse pulse tracking
- DPV: Staircase + periodic pulses, baseline/pulse differential
- NPV: Pulses from constant baseline, measured at end of pulse
- POT: Open-circuit measurement, no current flow
- All inherit from BaseExperiment with template method pattern
- Registry automatically detects and registers all experiments

### Stats
- New files: 4 (square_wave.py, differential_pulse.py, normal_pulse.py, potentiometry.py)
- Modified files: 1 (experiments/__init__.py)
- Lines added: ~1,410 lines (357 SWV + 389 DPV + 397 NPV + 267 POT)
- **Total experiments: 7** (CV, LSV, CA, SWV, DPV, NPV, POT)

### Phase 5.1 Status
- ✅ Square Wave Voltammetry (SWV) complete
- ✅ Differential Pulse Voltammetry (DPV) complete
- ✅ Normal Pulse Voltammetry (NPV) complete
- ✅ Potentiometry (POT) complete

---

## 2025-10-12 - GUI UX Improvements: Dual Plots & Modern Styling

**Duration:** ~1.5 hours | **Status:** ✅ Complete

### Completed
- ✅ Added dual plot system (Applied Voltage + Main Data plots side-by-side)
- ✅ Implemented clean blue & gray color scheme with light backgrounds
- ✅ Changed all fonts to Arial for professional appearance
- ✅ Made all text darker for better readability (#212121)
- ✅ Fixed graph axis labels (Time (s), Voltage (V), Current (µA))
- ✅ Aligned all section frames with consistent borders
- ✅ Moved Configure button inside Experiment Parameters frame
- ✅ Fixed metaclass conflict in BaseExperiment (QObject + ABCMeta)
- ✅ Created requirements.txt with all dependencies
- ✅ Successfully tested GUI with all 7 experiments

### Dual Plot System
- **Left Plot:** Applied Voltage vs Time
  - Shows the voltage waveform being applied
  - Helpful for visualizing CV triangular wave, LSV ramp, SWV/DPV pulses
  - Axis labels: Time (s) and Voltage (V)
- **Right Plot:** Main experiment data
  - Current vs Voltage (for CV, LSV, SWV, DPV, NPV)
  - Current vs Time (for CA)
  - Voltage vs Time (for POT)
  - Dynamic labels based on experiment type

### Modern Styling
- **Color Scheme:**
  - Light blue background (#E3F2FD) for all GroupBoxes
  - Medium blue (#64B5F6) for borders and buttons
  - Darker blue (#1976D2, #1565C0) for titles and highlights
  - Near-black (#212121) for all body text
  - Gray for disabled elements (#BDBDBD, #757575)
- **Typography:**
  - Arial font throughout entire application
  - 10pt for body text, 12pt for axis labels, 13pt for titles
  - Bold for buttons and section headers
- **Layout:**
  - 2px solid borders on all GroupBoxes
  - 6px border radius for rounded corners
  - Consistent padding and margins
  - Configure button moved inside parameter frame

### Technical Fixes
- **Metaclass Conflict:** Created QABCMeta combining type(QObject) and ABCMeta
- **Initialization Order:** Moved _setup_statusbar() before _setup_ui() to prevent attribute error
- **Plot Text Styling:** Updated PlotManager.set_labels() to apply darker colors
- **Dependencies:** Installed PyQt5, pyqtgraph, pandas, pyserial, openpyxl, matplotlib

### Stats
- Modified files: 3 (main_window.py, parameter_panel.py, plot_manager.py)
- Lines modified: ~200 lines of styling and layout improvements
- New files: 2 (requirements.txt, base_experiment.py metaclass fix)
- **GUI now has professional, clean appearance with dual plot visualization**

---

## 2025-10-12 - Phase 5.2: Data Analysis Tools

**Duration:** ~2 hours | **Status:** ✅ Complete

### Completed
- ✅ Created analysis module directory structure
- ✅ Implemented Peak Detection algorithm (scipy-based, 196 lines)
- ✅ Implemented Baseline Correction methods (197 lines)
- ✅ Implemented Integration/Charge calculation (173 lines)
- ✅ Implemented Smoothing filters (186 lines)
- ✅ Created Analysis Panel UI widget (267 lines)
- ✅ Integrated analysis tools with main window (visualization overlays)
- ✅ Updated requirements.txt with numpy and scipy dependencies
- ✅ Fixed main.py import paths for proper module execution
- ✅ Successfully tested all analysis tools with GUI

### Peak Detection Implementation
- **Algorithm:** scipy.signal.find_peaks for automatic detection
- **Features:** Configurable prominence, width, height, distance
- **Visualization:** Red markers for anodic peaks, blue for cathodic peaks
- **Output:** Peak positions, values, properties, peak separation
- **Line count:** 196 lines

### Baseline Correction Implementation
- **Methods:** Polynomial, Spline, Linear, Endpoints
- **Features:** Multiple fitting algorithms with configurable parameters
- **Visualization:** Orange dashed line overlay for baseline
- **Output:** Baseline curve and corrected data
- **Line count:** 197 lines

### Integration Implementation
- **Methods:** Trapezoidal rule, Simpson's rule
- **Features:** Range-based integration, cumulative charge, peak area
- **Applications:** Charge calculation (Q = ∫I dt), coulometric analysis
- **Output:** Total charge, average/peak current, statistics
- **Line count:** 173 lines

### Smoothing Implementation
- **Methods:** Savitzky-Golay, Moving Average, Exponential MA, Gaussian
- **Features:** Noise reduction with configurable parameters
- **Visualization:** Green line overlay for smoothed data
- **Output:** Smoothed data with noise reduction percentage
- **Line count:** 186 lines

### Analysis Panel UI
- **Controls:** Method selection dropdowns, parameter spinboxes, action buttons
- **Results Display:** Scrollable text area with detailed analysis results
- **Integration:** Real-time data updates from main experiment window
- **Visualization:** Interactive overlays on main plot (peaks, baseline, smoothing)
- **Line count:** 267 lines

### Key Features
- **Auto-enable:** Analysis tools enable when sufficient data available (>10 points)
- **Visual feedback:** Peak markers, baseline curves, smoothed overlays on plots
- **Results persistence:** Text results accumulate until cleared
- **Modular design:** Each analysis tool is independent and reusable
- **Type hints:** Full typing support for all analysis functions

### Architecture Notes
- Analysis module: 4 independent tool classes (PeakDetector, BaselineCorrector, DataIntegrator, DataSmoother)
- UI integration: AnalysisPanel emits signals processed by MainWindow
- Visualization: PyQtGraph overlays (ScatterPlotItem for peaks, PlotCurve for baseline/smoothing)
- Data flow: Experiment data → PlotManager → AnalysisPanel → Analysis tools → Visualization overlays
- Clear workflow: New experiment start clears previous analysis overlays

### Technical Fixes
- **Import paths:** Fixed main.py to use saxstat_gui_v1.gui.main_window
- **Dependencies:** Added numpy>=1.21.0 and scipy>=1.7.0 to requirements.txt
- **GUI initialization:** Analysis panel integrated below control buttons in left panel

### Stats
- New files: 5 (peak_detection.py, baseline_correction.py, integration.py, smoothing.py, analysis_panel.py)
- Modified files: 3 (main_window.py, requirements.txt, main.py)
- Lines added: ~1,019 lines (752 analysis + 267 UI)
- **Total analysis tools: 4** (Peak Detection, Baseline Correction, Integration, Smoothing)

### Phase 5.2 Status
- ✅ Peak Detection complete with visual markers
- ✅ Baseline Correction complete with curve overlay
- ✅ Integration complete with charge calculations
- ✅ Smoothing complete with filtered data overlay
- ✅ Analysis Panel UI complete with all controls
- ✅ GUI integration complete with interactive visualizations

### UX Improvement
- **Issue:** Analysis tools panel caused layout issues when window resized
- **Fix:** Moved analysis tools from left panel to "Analysis" menu
- **Implementation:**
  - Added "Analysis" menu to top menu bar (keyboard shortcut: Ctrl+A)
  - Analysis panel opens as non-modal dialog (450x600 minimum size)
  - Dialog created once and reused (prevents widget reparenting issues)
  - Can stay open while running experiments
- **Result:** Cleaner main window, better usability, no layout conflicts

### Font Styling Fix
- **Issue:** Plot titles not rendering in Arial font (axis labels worked but titles didn't)
- **Root Cause:** PyQtGraph's `setTitle()` doesn't accept CSS-style dictionaries like `setLabel()` does
- **Investigation:** Multiple iterations to understand pyqtgraph font rendering:
  1. First tried QFont objects → Only tick numbers changed
  2. Then tried CSS-style dictionaries → Labels changed but not titles
  3. Found that titles need HTML formatting instead
- **Solution:** Use HTML span tags with inline styles for titles:
  ```python
  title_html = f'<span style="color: #212121; font-size: 13pt; font-family: Arial; font-weight: bold;">{title}</span>'
  self.plot_item.setTitle(title_html)
  ```
- **Files Modified:**
  - `plot_manager.py:90-93` - Changed setTitle() to use HTML formatting
  - All plot titles now render consistently in Arial font
- **Result:** All text in graph panels (titles, axis labels, tick numbers) now displays in Arial

### Work Plan v2.4 Reorganization - Clear Version Picture
- **Decision:** Move all completed features to v1.1 for accurate progress tracking
- **v1.1 Status: 57% Complete (8/14 tasks done)**
  - ✅ Complete: 7 experiments (CV, LSV, CA, SWV, DPV, NPV, POT)
  - ✅ Complete: 4 analysis tools (peak detection, baseline, integration, smoothing)
  - 🔄 Remaining: 6 tasks (autosave, presets, Excel, overlays, calibration, packaging)
- **v1.2 Focus (Testing & Workflow):**
  - 7 tasks: Progress indicators, unit tests, method builder
  - Hardware validation, comprehensive docs, publication examples
- **Priority Order for v1.1:**
  1. Autosave (critical - data loss prevention)
  2. Parameter presets (productivity)
  3. Excel export (already have openpyxl)
  4. Plot overlays (experiment comparison)
  5. Calibration dialog (accuracy)
  6. Package executable (distribution)
- **Rationale:**
  - Honest progress tracking: 57% of v1.1 already done!
  - Clear remaining scope: 6 focused tasks
  - Logical priority: Critical features first, packaging last
- **Updated:** WORK_PLAN.md version 2.4

---

## Next Session - Remaining Tasks

**Per WORK_PLAN.md v2.0:**

### Phase 2: Experiment Support
- ✅ **Complete** (100%) - All basic techniques implemented (CV, LSV, CA)
- [ ] Hardware testing with prototype v03 for all Phase 2 experiments

### Phase 3: Data Management
- ✅ **Complete** (100%) - CSV/JSON/Excel export, configuration persistence
- [ ] Test all export formats with real hardware data
- [ ] Implement autosave functionality
- [ ] Add experiment parameter presets

### Phase 4: Polish & Testing (In Progress - 65% Complete)
- ✅ Error handling framework
- ✅ Plot export (PNG/JPEG)
- [ ] Complete user documentation
- [ ] Hardware testing suite for all 7 experiments
- [ ] Unit tests for validation
- [ ] Package executable with PyInstaller

### Phase 5: Advanced Features (In Progress - 30% Complete)
- ✅ **Phase 5.1 Complete** - Additional experiment techniques (SWV, DPV, NPV, POT)
- ✅ **Phase 5.2 Complete** - Data analysis tools (peak detection, baseline correction, integration, smoothing)
- [ ] **Phase 5.3** - Method builder for sequential experiments
- [ ] **Phase 5.4** - Database integration (optional)
- [ ] **Phase 5.5** - Remote control API (optional)
- [ ] **Phase 5.6** - Advanced plotting (overlays, multiple datasets)
- [ ] **Phase 5.7** - Calibration dialog and features

---

## 2026-02-20 - Gain Selection (10⁴ / 10⁶ V/A) Firmware & GUI

**Duration:** ~1 hour | **Status:** ✅ Complete

### Completed
- ✅ Firmware: Added `#define GAIN1_PIN 33`, `GAIN2_PIN 25` with `pinMode`/`digitalWrite`
- ✅ Firmware: Both MODE_ handlers (main loop + acquisition loop) now toggle GPIO pins
- ✅ Firmware: Default on boot = LOW (10kΩ, ±500 µA)
- ✅ GUI: Added "Gain Selection" QGroupBox with two QRadioButtons in left panel
- ✅ GUI: Sends `MODE_0`/`MODE_1` via serial on toggle and on connect
- ✅ GUI: Updates experiment `tia_resistance` (10000 or 1000000) dynamically
- ✅ GUI: Persists gain selection in config across sessions
- ✅ Base experiment: Added `set_tia_resistance()` method (inherited by all 6 experiments)
- ✅ README: Documented gain selection in hardware specs, features, quick start
- ✅ README: Fixed citation and GitHub Issues URL placeholder
- ✅ Rebuilt `SaxStat.exe` with PyInstaller (includes gain selection)
- ✅ Pushed to GitHub (commit ea86221)

### Key Decisions
- **Option A chosen:** Always calculate in µA — no unit switching between modes
- **No changes to individual experiment files** — all inherit `set_tia_resistance()` from base
- **Gain synced on every serial connect** — ensures hardware matches GUI state

### Hardware Details
- **Pin mapping:** GAIN1 → GPIO 33, GAIN2 → GPIO 25
- **Switch IC:** TS5A3160 (U5, U6) — LOW = NC (10kΩ), HIGH = NO (1MΩ)
- **U5 and U6 always switch together** (same gain for both channels)

### Stats
- Modified files: 4 (firmware .ino, base_experiment.py, main_window.py, README.md)
- Lines: +104, -13

---

**Format Notes:**
- Each session: Date, duration, status
- Completed: Bullet list of tasks
- Key decisions: Important choices made
- Issues: Problems encountered and solutions
- Stats: Quick metrics
- Keep it compact and scannable

---

## Session Summary (2025-10-12)

**Total Duration:** ~10 hours | **WORK_PLAN v2.0 Status:** Phase 1 ✅ | Phase 2 ✅ | Phase 3 ✅ | Phase 4 🔄 (70%) | Phase 5 🔄 (30%)

### Achievements Per WORK_PLAN v2.0
- ✅ **Phase 1: Core Architecture** - Complete (100%)
  - Project organization and GitHub setup
  - Qt5 project structure with modular design
  - Hardware communication (SerialManager, threading)
  - Experiment framework (BaseExperiment, state machine)
  - Real-time plotting (PlotManager with pyqtgraph)

- ✅ **Phase 2: Experiment Support** - Complete (100%)
  - ✅ Experiment registry pattern with auto-registration
  - ✅ Parameter UI system (ParameterPanel)
  - ✅ Cyclic Voltammetry (CV) fully implemented (293 lines)
  - ✅ Linear Sweep Voltammetry (LSV) implemented (280 lines)
  - ✅ Chronoamperometry (CA) implemented (285 lines)
  - 🔄 Hardware testing pending (all 3 experiments ready)

- ✅ **Phase 3: Data Management** - Complete (100%)
  - ✅ Pandas-based data storage (DataManager)
  - ✅ CSV/JSON export implemented
  - ✅ Excel export framework ready
  - ✅ Configuration management (JSON-based)
  - ✅ Parameter persistence (last port, experiment, window size)

- 🔄 **Phase 4: Polish & Testing** - In Progress (70%)
  - ✅ Error handling framework
  - ✅ Plot export (PNG/JPEG)
  - ✅ GUI UX improvements (dual plots, modern styling)
  - ✅ Professional typography (Arial font)
  - 🔄 User documentation (partial)
  - 🔄 Testing suite (test script created)
  - 🔄 Packaging (planned)

- 🔄 **Phase 5: Advanced Features** - In Progress (30%)
  - ✅ **Phase 5.1 Complete** - Additional experiment techniques (SWV, DPV, NPV, POT)
  - ✅ **Phase 5.2 Complete** - Data analysis tools (Peak Detection, Baseline Correction, Integration, Smoothing)
  - 🔄 Phase 5.3-5.7 planned

### Deliverables
- **Documentation:** 3 major docs (DStat Analysis, Architecture, Work Plan v2.1) ~180KB
- **Code:** 31 Python modules, ~5,200 lines functional GUI
- **Experiments:** 7 techniques (CV, LSV, CA, SWV, DPV, NPV, POT) with full parameter validation
- **Analysis Tools:** 4 post-processing tools (Peak Detection, Baseline Correction, Integration, Smoothing)
- **GUI Features:** Dual plots, modern styling, Arial typography, professional UX, interactive analysis overlays
- **Dependencies:** requirements.txt with PyQt5, pyqtgraph, pandas, numpy, scipy, pyserial
- **GitHub:** https://github.com/xiaojunyang0805/SaxStat
- **Status:** Professional GUI v1 with 7 experiments, 4 analysis tools, dual plot visualization, ready for hardware testing

### Current Completion
- **MVP (v1.2) Progress:** ~95% (core + 7 experiments + 4 analysis tools + UX done, hardware testing/docs remain)
- **Phase 1:** Complete ✅
- **Phase 2:** Complete ✅ (CV, LSV, CA all implemented)
- **Phase 3:** Complete ✅
- **Phase 4:** 70% (error handling ✅, GUI UX ✅, docs/testing pending)
- **Phase 5:** 30% (Phase 5.1 ✅, Phase 5.2 ✅, remaining phases planned)

**Last Updated:** 2025-10-12
