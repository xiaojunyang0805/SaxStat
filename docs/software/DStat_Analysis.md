# DStat Potentiostat GUI Architecture Analysis

**Analysis Date:** 2025-10-12
**Purpose:** Extract architectural patterns and design principles for SaxStat GUI v1 development
**Source:** dstat-interface-mrbox reference implementation

---

## Executive Summary

The DStat interface is a mature PyGTK-based GUI for potentiostat control with well-defined separation of concerns. Key strengths include modular experiment design, process-based hardware communication, and flexible parameter management. This analysis identifies reusable architectural patterns applicable to SaxStat development.

---

## 1. Overall Architecture

### 1.1 Module Organization

```
dstat_interface_mrbox/
├── main.py                 # Application entry & orchestration
├── dstat_comm.py          # Hardware communication layer
├── params.py              # Parameter management
├── plot.py                # Plotting subsystem
├── analysis.py            # Data analysis
├── errors.py              # Custom exceptions
├── parameter_test.py      # Input validation
├── db.py                  # Database integration
└── interface/
    ├── exp_window.py      # Experiment container manager
    ├── exp_int.py         # Individual experiment UIs
    ├── save.py            # Data export functionality
    ├── adc_pot.py         # Hardware configuration UI
    └── *.glade            # GTK UI definitions (XML)
```

**Key Insight:** Clear separation between UI layer (interface/), business logic (main.py), hardware communication (dstat_comm.py), and data handling (plot.py, save.py, analysis.py).

### 1.2 Application Flow

1. **Initialization** (main.py::Main.__init__)
   - Load GTK UI from .glade files
   - Initialize all subsystem modules
   - Setup serial port detection
   - Load last session parameters

2. **Connection Phase**
   - User selects serial port
   - Version handshake with hardware
   - Start OCP (Open Circuit Potential) monitoring
   - Load hardware settings

3. **Experiment Configuration**
   - Select experiment type via dropdown
   - Switch parameter UI dynamically
   - Validate parameters in real-time

4. **Experiment Execution**
   - Stop OCP monitoring
   - Spawn multiprocessing subprocess for hardware communication
   - Stream data through pipes to GUI
   - Update plot in real-time via GTK timeouts

5. **Post-Experiment**
   - Run analysis routines
   - Display results in UI
   - Optionally autosave data/plots
   - Resume OCP monitoring

### 1.3 GUI Framework (PyGTK)

**Technology Stack:**
- PyGTK 2.0 (GTK+ 2.x bindings)
- Glade for declarative UI design
- Matplotlib for plotting (GTKAgg backend)
- GObject for event handling

**Pattern:** Model-View separation where Glade files define layout (View) and Python classes provide logic (Controller).

---

## 2. Key Modules Analysis

### 2.1 main.py - Application Orchestrator

**Class:** `Main` (1060 lines)

**Responsibilities:**
- Central hub coordinating all subsystems
- Manages application state (connected, running experiment, etc.)
- Handles GTK signal callbacks
- Orchestrates experiment lifecycle
- Database integration (optional)
- Plugin API via ZeroMQ (for uDrop integration)

**Key Design Elements:**

```python
# Experiment type enumeration
EXPERIMENT_TYPES = pd.Series(['CA', 'LSV', 'CV', 'SWV', 'DPV', 'ACV', 'PD', 'POT', 'OC'])

# Column mapping for different experiment data structures
COLUMN_MAPPING = OrderedDict([
    (EXPERIMENT_TYPES.CA, ['current_amps']),
    (EXPERIMENT_TYPES.LSV, ['voltage_volts', 'current_amps']),
    (EXPERIMENT_TYPES.SWV, ['voltage_volts', 'current_amps',
                            'forward_current_amps', 'reverse_current_amps']),
    # ... etc
])
```

**State Management:**
- `self.connected`: Boolean for serial connection
- `self.active_experiment_id`: UUID for current run
- `self.completed_experiment_ids`: OrderedDict of past experiments
- `self.completed_experiment_data`: pandas DataFrames of results
- `self.current_exp`: Active experiment object

**GTK Event Loop Integration:**
```python
# Real-time data collection (GTK idle callbacks)
self.experiment_proc = (
    gobject.idle_add(self.experiment_running_data),
    gobject.idle_add(self.experiment_running_proc)
)

# Plot updates (GTK timeout - 200ms)
self.plot_proc = gobject.timeout_add(200, self.experiment_running_plot)
```

**SaxStat Takeaway:** Adopt central orchestrator pattern with clear state management. Consider modern async patterns (asyncio) instead of GTK callbacks for cleaner code.

### 2.2 dstat_comm.py - Hardware Communication

**Architecture:** Multiprocessing-based isolation

**Key Classes:**

1. **SerialConnection** - Process manager
   - Creates 3 bidirectional pipes: proc_pipe, ctrl_pipe, data_pipe
   - Spawns `_serial_process` in separate process
   - Provides parent-side pipe interfaces

2. **Experiment Base Class** - Command generation
   - Each experiment type subclasses Experiment
   - `__init__`: Generates command strings for hardware
   - `run()`: Executes commands via serial
   - `serial_handler()`: Processes incoming data
   - `data_handler()`: Converts raw bytes to meaningful units
   - `data_postprocessing()`: Optional post-processing hook

3. **Process Communication Flow:**
   ```
   GUI Process                    Serial Process
   -----------                    --------------
   send(exp_obj) ----proc_pipe--> exp_obj.run()
   recv() <------data_pipe------- send(data_tuple)
   recv() <------proc_pipe------- send("DONE")
   send('a') -----ctrl_pipe-----> ABORT
   ```

**Experiment Subclasses:**
- `Chronoamp` - Step potentials over time
- `LSVExp` - Linear sweep voltammetry
- `CVExp` - Cyclic voltammetry
- `SWVExp` - Square wave voltammetry
- `DPVExp` - Differential pulse voltammetry
- `PDExp` - Photodiode/PMT measurements
- `PotExp` - Potentiometry
- `OCPExp` - Open circuit potential monitoring
- `CALExp` - Calibration

**Data Structure Pattern:**
```python
self.data = {
    'data': [scan0, scan1, ...],  # List of scans
}
# Each scan is a tuple of lists:
scan = ([time0, time1, ...], [current0, current1, ...])

# For multi-measurement (SWV, DPV):
scan = ([voltage...], [diff_current...], [forward...], [reverse...])
```

**SaxStat Takeaway:**
- Multiprocessing isolation protects GUI from hardware hangs
- Pipe-based communication is simple and effective
- Base class with subclass pattern allows clean experiment extension
- Consider: USB/CDC for SaxStat may need different serialization (JSON over serial?)

### 2.3 params.py - Parameter Management

**Simple but Effective Pattern:**

```python
def get_params(window):
    """Collects parameters from all UI components"""
    parameters = {}
    parameters['experiment_index'] = window.expcombobox.get_active()
    parameters.update(window.adc_pot.params)  # Hardware config
    parameters.update(window.exp_window.get_params(selection))  # Experiment params
    parameters.update(window.analysis_opt_window.params)  # Analysis options
    parameters.update(window.db_window.persistent_params)  # Metadata
    return parameters

def save_params(window, path):
    """Serializes to YAML"""
    params = get_params(window)
    yaml.dump(params, open(path, 'w'))

def set_params(window, params):
    """Distributes parameters to UI components"""
    window.adc_pot.params = params
    window.exp_window.set_params(params['experiment_index'], params)
    window.analysis_opt_window.params = params
```

**SaxStat Takeaway:**
- Aggregation pattern: collect from all subsystems into single dict
- Use modern serialization (JSON recommended over YAML)
- Property-based setters/getters in UI components for validation
- Consider pydantic models for type safety and validation

### 2.4 exp_window.py & exp_int.py - Experiment Interface

**Two-Level Pattern:**

**Level 1: exp_window.py** - Container Manager
```python
class Experiments:
    def __init__(self, builder):
        # Registry of all experiment types
        self.classes = {
            'cae': (0, exp.Chronoamp()),
            'lsv': (1, exp.LSV()),
            'cve': (2, exp.CV()),
            # ... etc
        }
        # Bidirectional lookup
        self.select_to_key = {value[0]: key for key, value in self.classes.items()}

    def set_exp(self, selection):
        """Show selected experiment UI, hide others"""
        for key in self.containers:
            self.containers[key].hide()
        self.containers[selection].show()
```

**Level 2: exp_int.py** - Individual Experiment UIs

**Base Class Pattern:**
```python
class ExpInterface(object):
    """Generic experiment interface with property-based params"""
    def __init__(self, glade_path):
        self.builder = gtk.Builder()
        self.builder.add_from_file(glade_path)
        self.entry = {}  # Dict of GTK entry widgets
        self._params = None

    @property
    def params(self):
        """Getter: read from UI widgets"""
        if self._params is None:
            self._fill_params()
        self._get_params()
        return self._params

    @params.setter
    def params(self, params):
        """Setter: write to UI widgets"""
        if self._params is None:
            self._fill_params()
        for key in self._params:
            try:
                self._params[key] = params[key]
            except KeyError:
                pass  # Ignore missing keys
        self._set_params()

    def _get_params(self):
        """Override to read from specific widgets"""
        for i in self.entry:
            self._params[i] = self.entry[i].get_text()

    def _set_params(self):
        """Override to write to specific widgets"""
        for i in self.entry:
            self.entry[i].set_text(self._params[i])
```

**Specialized Implementations:**
- **Simple experiments** (LSV, CV, DPV, SWV, POT): Just define self.entry mappings
- **Complex experiments** (CA): Override to handle TreeView for multi-step sequences
- **PD**: Additional boolean parameters and spinbuttons

**SaxSat Takeaway:**
- Registry pattern for experiment types is extensible
- Property-based parameter access provides clean API
- Glade file per experiment allows designers to work independently
- Consider: Qt Designer files (.ui) if using PyQt/PySide

### 2.5 plot.py - Plotting Functionality

**Class Hierarchy:**
```python
PlotBox          # Base plotting class
└── FT_Box       # Specialized for FFT plots
```

**Architecture:**
```python
class PlotBox:
    def __init__(self, container):
        self.figure = Figure()  # matplotlib Figure
        self.axe1 = self.figure.add_subplot(111)
        self.canvas = FigureCanvas(self.figure)  # GTK integration
        self.toolbar = NavigationToolbar(self.canvas, self.win)
        # Reparent into provided GTK container
        self.vbox.reparent(container)

    def clearall(self):
        """Remove all plot lines"""

    def addline(self):
        """Add new line to plot"""

    def updateline(self, Experiment, line_number):
        """Update specific line with experiment data"""
        divisor = len(data) // 2000 + 1  # Downsample for performance
        self.axe1.lines[line_number].set_ydata(y_data[::divisor])
        self.axe1.lines[line_number].set_xdata(x_data[::divisor])

    def changetype(self, Experiment):
        """Configure plot for experiment type"""
        self.axe1.set_xlabel(Experiment.xlabel)
        self.axe1.set_ylabel(Experiment.ylabel)
        self.axe1.set_xlim(Experiment.xmin, Experiment.xmax)

    def redraw(self):
        """Autoscale and refresh"""
        self.axe1.relim()
        self.axe1.autoscale(True, axis='y')
        self.figure.canvas.draw()
```

**Performance Optimization:**
- Downsampling: Only plot every Nth point for large datasets (>2000 points)
- Incremental updates: Only redraw changed data, not entire plot
- Auto-scaling on Y-axis only (X-axis fixed by experiment parameters)

**SaxStat Takeaway:**
- Matplotlib provides publication-quality plots
- Downsampling crucial for real-time performance
- Consider: pyqtgraph for even faster real-time plotting

### 2.6 save.py - Data Export

**Functions:**
- `manSave()`: Interactive file dialog for manual save
- `autoSave()`: Automatic save with naming convention
- `save_text()`: Export data to space-separated text
- `save_plot()`: Export plots to PDF/PNG
- `man_param_save/load()`: Parameter file management

**Export Format:**
```
# TIME 2025-10-12T14:30:00.000000
# DSTAT COMMANDS
#  EA2 3 1 EG1 0 ER1 32768 1000 0
# ANALYSIS
#  min:
#    Scan 0 -- -1.23e-6
#  max:
#    Scan 0 -- 2.45e-6
#  mean:
#    Scan 0 -- 5.67e-7
0.000     -1.23e-6
0.100     -1.19e-6
0.200     -1.15e-6
...
```

**File Naming Pattern:**
```python
# Handles duplicates by appending numbers
name = "experiment"
num = 0
while os.path.exists(f"{name}{num}-data.txt"):
    num += 1
# Saves multiple data types: "experiment0-data.txt", "experiment0-ft.txt"
```

**SaxStat Takeaway:**
- Header with metadata (timestamp, commands, analysis)
- Human-readable space-separated format
- Also export pandas DataFrame to CSV for modern workflows
- Consider HDF5 for large datasets

---

## 3. Experiment Types & Structure

### 3.1 Supported Techniques

| Code | Technique | Key Parameters | Data Columns |
|------|-----------|----------------|--------------|
| CA | Chronoamperometry | potential[], time[] | time, current |
| LSV | Linear Sweep Voltammetry | start, stop, slope | voltage, current |
| CV | Cyclic Voltammetry | v1, v2, scans, slope | voltage, current |
| SWV | Square Wave Voltammetry | start, stop, step, pulse, freq | voltage, current, forward, reverse |
| DPV | Differential Pulse Voltammetry | start, stop, step, pulse, period, width | voltage, current, forward, reverse |
| PD | Photodiode/PMT | time, voltage, sync_freq | time, current |
| POT | Potentiometry | time | time, voltage |
| OC | Offset Calibration | time, gain | offset values |

### 3.2 Experiment Definition Pattern

Each experiment type defined by:

1. **Parameter Schema** - Required inputs
2. **Command Generation** - Hardware instruction strings
3. **Data Structure** - Number and type of measurement columns
4. **Plot Configuration** - Axis labels, ranges
5. **Validation Rules** - Parameter bounds checking

**Example: Cyclic Voltammetry**
```python
class CVExp(Experiment):
    def __init__(self, parameters):
        super(CVExp, self).__init__(parameters)

        # Define data structure
        self.datatype = "CVData"
        self.xlabel = "Voltage (mV)"
        self.ylabel = "Current (A)"
        self.datalength = 2 * self.parameters['scans']
        self.databytes = 6  # uint16 + int32

        # Set plot ranges
        self.xmin = int(self.parameters['v1'])
        self.xmax = int(self.parameters['v2'])

        # Generate hardware commands
        self.commands += "E"
        self.commands[2] += "C"  # CV mode
        self.commands[2] += str(self.parameters['clean_s']) + " "
        self.commands[2] += str(self.parameters['dep_s']) + " "
        # ... build complete command string
```

### 3.3 Common Parameter Groups

**Cleaning/Deposition (for stripping voltammetry):**
- `clean_mV`: Cleaning potential
- `clean_s`: Cleaning duration
- `dep_mV`: Deposition potential
- `dep_s`: Deposition duration

**Waveform (for voltammetric techniques):**
- `start/stop`: Voltage range
- `slope`: Scan rate (mV/s)
- `step`: Step height (SWV/DPV)
- `pulse`: Pulse height (SWV/DPV)
- `freq/period`: Timing parameters

**Hardware Configuration (global):**
- `gain`: TIA gain setting (0-7)
- `adc_rate`: ADC sampling rate
- `adc_pga`: Programmable gain amplifier
- `buffer_true`: Input buffer enable

### 3.4 Parameter Validation Strategy

**Two-Layer Approach:**

1. **Pre-execution validation** (parameter_test.py)
   ```python
   def cv_test(params):
       if params['clean_mV'] > 1499 or params['clean_mV'] < -1500:
           raise InputError(params['clean_mV'],
                          "Clean potential exceeds hardware limits.")
       if params['v1'] == params['v2']:
           raise InputError(params['v1'],
                          "Vertex 1 cannot equal Vertex 2.")
       # ... more validation
   ```

2. **UI-level validation** (in exp_int.py)
   ```python
   def on_add_button_clicked(self, widget):
       try:
           potential = int(self.entry['potential'].get_text())
           if potential > 1499 or potential < -1500:
               raise ValueError("Potential out of range")
           self.model.append([potential, time])
       except ValueError as err:
           self.statusbar.push(0, str(err))
   ```

**SaxStat Takeaway:**
- Define validation schemas per experiment type
- Validate early (UI) and late (pre-execution)
- Use pydantic for Pythonic validation with clear error messages

---

## 4. Design Patterns

### 4.1 Experiment Implementation Pattern

**Strategy Pattern with Template Method:**

```python
class Experiment(object):
    """Template for all experiments"""

    def __init__(self, parameters):
        # Common initialization: gain tables, data structure
        self.parameters = parameters
        self.data = {'data': [([], [])]}
        self.commands = []

    def run(self, ser, ctrl_pipe, data_pipe):
        """Template method - same for all experiments"""
        try:
            for command in self.commands:
                self.serial.write(command)
                self.serial_handler()
            self.data_postprocessing()
        except SerialException:
            return "SERIAL_ERROR"
        return "DONE"

    def serial_handler(self):
        """Hook: can override for custom parsing"""
        for line in self.serial:
            if line.startswith('B'):
                data = self.data_handler(self.serial.read(self.databytes))
                self.data_pipe.send(data)

    def data_handler(self, data_input):
        """Hook: override to parse specific data format"""
        voltage, current = struct.unpack('<Hl', data_input)
        return (scan, (voltage, current))

    def data_postprocessing(self):
        """Hook: override for post-processing"""
        pass
```

**Concrete Implementation:**
```python
class CVExp(Experiment):
    def __init__(self, parameters):
        super(CVExp, self).__init__(parameters)
        # Set experiment-specific attributes
        self.datatype = "CVData"
        self.databytes = 6
        # Generate CV-specific commands
        self.commands.append("EC ...")
```

**Benefits:**
- Common lifecycle in base class
- Experiment-specific logic in subclasses
- Easy to add new techniques
- Hardware communication isolated from GUI

### 4.2 Communication Protocol Structure

**ASCII Command Protocol:**

```
Format: <CMD><PARAMS>\n

Examples:
EA2 3 1        # ADC config: buffer=2, rate=3, pga=1
EG1 0          # Gain config: gain=1, short=off
EC10 20 ...    # CV command: clean=10s, dep=20s, ...
```

**Binary Data Protocol:**

```
Response Format:
B<BINARY_DATA>  # 'B' prefix, then N bytes

Examples:
- CA/LSV/CV: 6 bytes (uint16 + int32)
- SWV/DPV: 10 bytes (uint16 + 2x int32)
- Time-based: 8 bytes (2x uint16 + int32)
```

**Control Flow:**
```
GUI                         Hardware
---                         --------
'!' (handshake)      --->
                     <---   'C' (ready)
'V' (version)        --->
                     <---   'V1.2' (response)
'EA2 3 1'            --->
                     <---   'no' (command done)
'EC...'              --->
                     <---   'B' + data bytes (streaming)
                     <---   'B' + data bytes
                     <---   'S' (scan done)
                     <---   'no' (experiment done)
'a' (abort)          --->
                     <---   'no' (aborted)
```

**SaxStat Takeaway:**
- ASCII commands are human-readable and debuggable
- Binary data is efficient for high-speed streaming
- Consider: JSON for commands (more structured, self-documenting)
- USB-CDC can handle higher throughput than traditional UART

### 4.3 Data Flow Architecture

```
                    ┌─────────────────────────────────────┐
                    │       Hardware (DStat PCB)          │
                    │   Executes experiment, sends data   │
                    └─────────────────┬───────────────────┘
                                      │ Serial (USB-CDC)
                    ┌─────────────────▼───────────────────┐
                    │    _serial_process (subprocess)      │
                    │  - Reads serial port                 │
                    │  - Parses protocol                   │
                    │  - Runs experiment.run()             │
                    └──────┬────────────┬──────────────────┘
                           │            │
                 data_pipe │            │ proc_pipe (status)
                           │            │
                    ┌──────▼────────────▼──────────────────┐
                    │      Main GUI Process                │
                    │  - experiment_running_data()         │
                    │  - experiment_running_proc()         │
                    │  - Populates current_exp.data        │
                    └──────┬────────────────────────────────┘
                           │
                           │ GTK timeout (200ms)
                           │
                    ┌──────▼────────────────────────────────┐
                    │    experiment_running_plot()         │
                    │  - Reads from current_exp.data       │
                    │  - Updates matplotlib plot           │
                    └────────────────────────────────────────┘
                           │
                           │ On completion
                           │
                    ┌──────▼────────────────────────────────┐
                    │      experiment_done()               │
                    │  - Run analysis                      │
                    │  - Update displays                   │
                    │  - Autosave if enabled               │
                    │  - Store in completed_experiment_data│
                    └────────────────────────────────────────┘
```

**Key Points:**
- Process isolation prevents GUI hangs
- Multiprocessing.Pipe for IPC
- Real-time streaming via data_pipe
- Status/control via proc_pipe/ctrl_pipe
- pandas.DataFrame as final data format

### 4.4 Configuration Management

**Hierarchical Configuration:**

1. **Application-Level** (saved in last_params.yml)
   - Window geometry
   - Last used experiment type
   - Autosave directory

2. **Hardware-Level** (stored in EEPROM on device)
   - Gain calibration offsets
   - TCS (light sensor) thresholds
   - Factory settings

3. **Experiment-Level** (per experiment type)
   - Voltammetry parameters
   - ADC settings
   - Analysis options

4. **Session-Level** (runtime only)
   - Current serial connection
   - Active experiment ID
   - Temporary metadata

**Loading Order:**
```python
def __init__(self):
    # 1. Initialize with defaults
    self.params_loaded = False

def on_serial_connect_clicked(self):
    # 2. Read hardware settings from device
    comm.read_settings()

    # 3. Load last session params
    if not self.params_loaded:
        try:
            params.load_params(self, 'last_params.yml')
        except IOError:
            pass  # No previous session

def quit(self):
    # Save session state
    params.save_params(self, 'last_params.yml')
```

---

## 5. Key Takeaways for SaxStat

### 5.1 Reusable Architectural Patterns

#### Pattern 1: Central Orchestrator
**What:** Single Main class coordinates all subsystems
**Why:** Simplifies state management, single source of truth
**Apply to SaxStat:**
- Create SaxStatApp class as central controller
- Manage connection state, experiment lifecycle
- Coordinate between UI, hardware, plotting, and storage

#### Pattern 2: Process-Based Hardware Isolation
**What:** Separate process for serial communication
**Why:** Prevents hardware issues from freezing GUI
**Apply to SaxStat:**
- Use asyncio instead of multiprocessing for modern async I/O
- Still isolate hardware communication from UI thread
- Consider: QThread if using PyQt

#### Pattern 3: Experiment Registry
**What:** Dict-based registry of experiment types
**Why:** Easy to add new techniques without changing core code
**Apply to SaxStat:**
```python
class ExperimentRegistry:
    def __init__(self):
        self._experiments = {}

    def register(self, name, experiment_class):
        self._experiments[name] = experiment_class

    def create(self, name, params):
        return self._experiments[name](params)

# Usage:
registry = ExperimentRegistry()
registry.register('cv', CyclicVoltammetry)
registry.register('lsv', LinearSweep)
```

#### Pattern 4: Property-Based Parameter Interface
**What:** Use @property for parameter access
**Why:** Validation, logging, and transformation in one place
**Apply to SaxStat:**
```python
class ExperimentUI:
    @property
    def params(self):
        """Collect and validate parameters"""
        params = self._collect_from_widgets()
        self._validate(params)
        return params

    @params.setter
    def params(self, values):
        """Distribute to widgets"""
        self._populate_widgets(values)
```

#### Pattern 5: Incremental Plot Updates
**What:** Only redraw changed data, downsample for performance
**Why:** Enables real-time plotting of high-rate data
**Apply to SaxStat:**
- Use pyqtgraph for even better real-time performance
- Implement circular buffer for fixed-window display
- Downsample intelligently (min/max/avg per bin)

### 5.2 Modular Design Principles

**Separation of Concerns:**
```
UI Layer         → Qt/GTK widgets, event handlers
Business Logic   → Experiment classes, validation
Hardware Layer   → Serial communication, protocol
Data Layer       → Pandas DataFrames, HDF5 storage
Plotting Layer   → Matplotlib/pyqtgraph
```

**Dependency Injection:**
```python
# Don't hardcode dependencies
class Experiment:
    def __init__(self, hardware, plotter, storage):
        self.hardware = hardware
        self.plotter = plotter
        self.storage = storage
```

**Interface Segregation:**
```python
# Define clear interfaces
class HardwareInterface:
    def connect(self, port):
        raise NotImplementedError

    def run_experiment(self, commands):
        raise NotImplementedError

    def disconnect(self):
        raise NotImplementedError
```

### 5.3 Multi-Experiment Support Strategy

**Three Approaches (from simplest to most complex):**

1. **Single Experiment Mode** (MVP)
   - Only one technique at a time
   - Easier to implement and test
   - Sufficient for initial SaxStat release

2. **Sequential Experiments**
   - Queue multiple experiments
   - Run one after another
   - Save results separately

3. **Method Builder** (future)
   - Chain experiments into methods
   - Share parameters between steps
   - Single dataset with multiple phases

**Recommended for SaxStat v1:** Start with approach #1, design API to allow #2 later.

### 5.4 Parameter Management Best Practices

**Use Pydantic for Type Safety:**
```python
from pydantic import BaseModel, validator

class CVParams(BaseModel):
    v1: int  # mV
    v2: int  # mV
    start: int  # mV
    scans: int
    slope: int  # mV/s

    @validator('v1', 'v2', 'start')
    def voltage_in_range(cls, v):
        if not -1500 <= v <= 1499:
            raise ValueError('Voltage out of range')
        return v

    @validator('scans')
    def positive_scans(cls, v):
        if v < 1:
            raise ValueError('Must have at least one scan')
        return v
```

**Benefit:** Automatic validation, clear error messages, IDE autocomplete

**Configuration File Format:**
- Use JSON (not YAML) for better tooling support
- Separate user settings from hardware calibration
- Version configuration schema for backwards compatibility

```json
{
  "config_version": "1.0",
  "last_experiment": "cv",
  "experiments": {
    "cv": {
      "v1": -500,
      "v2": 500,
      "scans": 3,
      "slope": 100
    }
  }
}
```

### 5.5 Architecture Differences: DStat vs SaxStat

| Aspect | DStat | SaxStat Recommendation |
|--------|-------|------------------------|
| **GUI Framework** | PyGTK 2.0 (legacy) | PyQt6 or PySide6 (modern, cross-platform) |
| **Async Model** | Multiprocessing + GTK callbacks | asyncio + Qt signals/slots |
| **UI Design** | Glade XML files | Qt Designer .ui files |
| **Plotting** | Matplotlib (GTKAgg) | pyqtgraph (faster) or Matplotlib (Qt5Agg) |
| **Data Format** | Text files + optional DB | Pandas → CSV/HDF5 primary, text export optional |
| **Configuration** | YAML | JSON with JSON Schema validation |
| **Hardware Protocol** | ASCII commands + binary data | JSON commands + binary data (structured) |
| **Validation** | Manual try/except blocks | Pydantic models with declarative validation |
| **Plugin System** | ZeroMQ | gRPC or REST API (if needed) |

### 5.6 Modern Python Patterns to Adopt

**Async Hardware Communication:**
```python
import asyncio
import aioserial

class SaxStatHardware:
    async def connect(self, port):
        self.serial = aioserial.AioSerial(port, 115200)

    async def run_experiment(self, experiment):
        await self.serial.write_async(experiment.commands)
        async for data in self.read_stream():
            yield data

    async def read_stream(self):
        while True:
            line = await self.serial.readline_async()
            if line.startswith(b'B'):
                yield self.parse_data(line)
```

**Type Hints Everywhere:**
```python
from typing import Dict, List, Optional
import pandas as pd

def run_experiment(
    params: Dict[str, Any],
    hardware: HardwareInterface
) -> pd.DataFrame:
    """Run experiment and return results as DataFrame"""
    results = hardware.execute(params)
    return pd.DataFrame(results)
```

**Dataclasses for Experiment Results:**
```python
from dataclasses import dataclass
from datetime import datetime

@dataclass
class ExperimentResult:
    id: str
    timestamp: datetime
    technique: str
    parameters: Dict[str, Any]
    data: pd.DataFrame
    metadata: Dict[str, Any]
```

---

## 6. Implementation Roadmap for SaxStat v1

### Phase 1: Core Architecture (Weeks 1-2)
- [ ] Setup Qt6 project structure
- [ ] Create main window with serial port selection
- [ ] Implement asyncio hardware communication layer
- [ ] Define experiment base class with CV example
- [ ] Basic real-time plotting with pyqtgraph

### Phase 2: Experiment Support (Weeks 3-4)
- [ ] Implement parameter UI for CV
- [ ] Add LSV and CA techniques
- [ ] Implement parameter validation with pydantic
- [ ] Add experiment registry pattern
- [ ] Test with SaxStat hardware

### Phase 3: Data Management (Weeks 5-6)
- [ ] Implement pandas-based data storage
- [ ] Add CSV export functionality
- [ ] Create configuration file system (JSON)
- [ ] Add parameter save/load
- [ ] Implement autosave feature

### Phase 4: Polish & Testing (Weeks 7-8)
- [ ] Add error handling and user feedback
- [ ] Implement plot export (PNG/PDF)
- [ ] Create user documentation
- [ ] Comprehensive testing with real experiments
- [ ] Package for distribution

### Phase 5: Advanced Features (Future)
- [ ] Additional techniques (SWV, DPV, etc.)
- [ ] Data analysis tools (peak detection, integration)
- [ ] Method builder for sequential experiments
- [ ] Database integration (optional)
- [ ] Remote control API (optional)

---

## 7. Code Quality Recommendations

**From DStat Analysis:**

**Good Practices to Keep:**
- Clear module separation
- Extensive logging
- Parameter validation at multiple levels
- Version handshake with hardware
- Graceful error handling

**Areas for Improvement (in SaxStat):**
- Replace global variables with dependency injection
- Add comprehensive unit tests
- Use type hints throughout
- Implement proper state machine for connection/experiment lifecycle
- Add progress indicators for long operations
- Better separation of GUI and business logic (use Model-View-Controller)

**Testing Strategy:**
```python
# Unit tests for validation
def test_cv_validation():
    params = CVParams(v1=-500, v2=500, scans=3, slope=100)
    assert params.v1 == -500

# Integration tests with mock hardware
async def test_cv_execution():
    hardware = MockHardware()
    result = await run_cv_experiment(hardware, params)
    assert result.data.shape[0] > 0

# GUI tests with pytest-qt
def test_parameter_ui(qtbot):
    widget = CVParameterWidget()
    qtbot.addWidget(widget)
    widget.v1_spinbox.setValue(-500)
    assert widget.params.v1 == -500
```

---

## 8. Conclusion

The DStat interface demonstrates a mature, well-architected potentiostat control system with clear separation of concerns and extensible design patterns. Key strengths include:

1. **Process isolation** for hardware communication reliability
2. **Registry pattern** for easy addition of new techniques
3. **Property-based parameters** for clean validation
4. **Real-time plotting** with performance optimization
5. **Flexible data export** with human-readable formats

For SaxStat v1, we should:
- Adopt the core architectural patterns (orchestrator, registry, property-based params)
- Modernize the technology stack (Qt6, asyncio, pydantic)
- Start simple with single-experiment mode
- Design APIs to allow future expansion
- Prioritize reliability, user feedback, and data integrity

**Next Steps:**
1. Create Qt6 project skeleton following this architecture
2. Define SaxStat-specific hardware protocol
3. Implement CV as first reference experiment
4. Iteratively add features based on user feedback

---

**Document Version:** 1.0
**Author:** Claude (Code Analysis Agent)
**Date:** 2025-10-12
