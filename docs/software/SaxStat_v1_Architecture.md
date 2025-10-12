# SaxStat GUI v1 Architecture Design

**Document Version:** 1.0
**Date:** 2025-10-12
**Target Platform:** Windows (primary), Linux/macOS (future)
**Python Version:** 3.9+
**Hardware:** ESP32-based potentiostat (prototype v03)

---

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [Core Components Design](#2-core-components-design)
3. [Experiment System](#3-experiment-system)
4. [Communication Protocol](#4-communication-protocol)
5. [File Structure](#5-file-structure)
6. [Data Flow & State Management](#6-data-flow--state-management)
7. [Implementation Plan](#7-implementation-plan)
8. [Testing Strategy](#8-testing-strategy)

---

## 1. Architecture Overview

### 1.1 Technology Stack

**Core Framework:**
- **PyQt5**: Modern cross-platform GUI framework
- **asyncio**: Asynchronous I/O for serial communication
- **pydantic**: Data validation and settings management
- **pyqtgraph**: High-performance real-time plotting
- **pandas**: Data manipulation and storage
- **pyserial**: Serial communication (with asyncio wrapper)

**Additional Libraries:**
- **numpy**: Numerical operations
- **typing**: Type hints for code clarity
- **json**: Configuration and data serialization
- **logging**: Comprehensive logging system

### 1.2 Architectural Patterns

**Primary Patterns:**
1. **Model-View-Controller (MVC)**: Separation of data, UI, and logic
2. **Template Method**: Base experiment class with extensible hooks
3. **Registry**: Pluggable experiment type registration
4. **Strategy**: Swappable validation and processing strategies
5. **Observer**: Signal/slot for event-driven updates

**Key Design Principles:**
- **Single Responsibility**: Each module has one clear purpose
- **Dependency Injection**: Loose coupling between components
- **Interface Segregation**: Well-defined component interfaces
- **Open/Closed**: Open for extension, closed for modification

### 1.3 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        SaxStatApp (Main)                        │
│                   Central Orchestrator & State                  │
└───┬─────────────┬──────────────┬──────────────┬────────────────┘
    │             │              │              │
    ▼             ▼              ▼              ▼
┌─────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────┐
│   GUI   │  │Serial    │  │  Data    │  │Configuration │
│ Manager │  │Manager   │  │ Manager  │  │   Manager    │
└────┬────┘  └────┬─────┘  └────┬─────┘  └──────┬───────┘
     │            │             │                │
     ▼            ▼             ▼                ▼
┌─────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────┐
│Plot     │  │Experiment│  │Processors│  │  Settings    │
│Manager  │  │Registry  │  │Exporters │  │  Storage     │
└─────────┘  └──────────┘  └──────────┘  └──────────────┘
```

### 1.4 Module Responsibilities

| Module | Responsibility | Key Classes |
|--------|---------------|-------------|
| **gui/** | User interface, widgets, layouts | MainWindow, ParameterPanel, PlotPanel |
| **experiments/** | Experiment definitions, parameter schemas | BaseExperiment, CV, LSV, CA |
| **communication/** | Serial I/O, protocol handling | SerialManager, ProtocolHandler |
| **data/** | Data acquisition, storage, export | DataManager, DataProcessor, Exporter |
| **plotting/** | Real-time visualization | PlotManager, CVPlotWidget |
| **config/** | Settings, calibration, persistence | ConfigManager, CalibrationData |
| **utils/** | Validation, helpers, logging | ParamValidator, Logger |

---

## 2. Core Components Design

### 2.1 Base Experiment Class

**Location:** `experiments/base_experiment.py`

**Purpose:** Template for all electrochemical techniques using Template Method pattern

**Class Design:**

```python
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Tuple
from pydantic import BaseModel
from enum import Enum

class ExperimentStatus(Enum):
    """Experiment lifecycle states"""
    IDLE = "idle"
    CONFIGURING = "configuring"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    ERROR = "error"
    ABORTED = "aborted"

class BaseExperiment(ABC):
    """
    Abstract base class for all experiments.

    Template Method Pattern: Defines experiment lifecycle skeleton.
    Subclasses implement technique-specific behavior.
    """

    def __init__(self, params: BaseModel):
        """
        Initialize experiment with validated parameters.

        Args:
            params: Pydantic model with validated parameters
        """
        self.params = params
        self.status = ExperimentStatus.IDLE
        self.data = {'voltage': [], 'current': [], 'time': []}
        self.metadata = {}
        self._observers = []

    # Template method (final - don't override)
    async def execute(self, serial_manager, data_manager) -> bool:
        """
        Main execution flow (template method).

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            self.status = ExperimentStatus.CONFIGURING
            self._notify_status_change()

            # Hook: Validate experiment-specific constraints
            if not self.validate():
                raise ValueError("Experiment validation failed")

            # Hook: Generate hardware commands
            commands = self.generate_commands()

            # Hook: Setup data structures
            self.setup_data_structures()

            self.status = ExperimentStatus.RUNNING
            self._notify_status_change()

            # Send commands and collect data
            await serial_manager.send_commands(commands)

            async for data_point in serial_manager.read_stream():
                if self.status == ExperimentStatus.ABORTED:
                    break

                # Hook: Process incoming data
                processed = self.process_data_point(data_point)

                # Store in data manager
                data_manager.append(processed)

                # Hook: Check completion condition
                if self.is_complete():
                    break

            # Hook: Post-processing
            self.post_process()

            self.status = ExperimentStatus.COMPLETED
            self._notify_status_change()
            return True

        except Exception as e:
            self.status = ExperimentStatus.ERROR
            self.metadata['error'] = str(e)
            self._notify_status_change()
            return False

    # Abstract methods (must implement in subclasses)

    @abstractmethod
    def validate(self) -> bool:
        """Validate experiment-specific parameters."""
        pass

    @abstractmethod
    def generate_commands(self) -> List[str]:
        """Generate hardware command strings."""
        pass

    @abstractmethod
    def process_data_point(self, raw_data: Dict[str, Any]) -> Dict[str, float]:
        """Convert raw data to meaningful units."""
        pass

    # Hook methods (can override in subclasses)

    def setup_data_structures(self) -> None:
        """Setup experiment-specific data containers."""
        pass

    def is_complete(self) -> bool:
        """Check if experiment should terminate."""
        return False

    def post_process(self) -> None:
        """Post-processing after data collection."""
        pass

    # Property methods

    @property
    @abstractmethod
    def technique_name(self) -> str:
        """Human-readable technique name."""
        pass

    @property
    @abstractmethod
    def data_columns(self) -> List[str]:
        """Column names for data export."""
        pass

    @property
    @abstractmethod
    def plot_config(self) -> Dict[str, Any]:
        """Plot configuration (axis labels, ranges)."""
        pass

    # Observer pattern for status updates

    def add_observer(self, callback):
        """Register callback for status changes."""
        self._observers.append(callback)

    def _notify_status_change(self):
        """Notify all observers of status change."""
        for callback in self._observers:
            callback(self.status)

    # Control methods

    def abort(self):
        """Request experiment abort."""
        self.status = ExperimentStatus.ABORTED
        self._notify_status_change()
```

### 2.2 Serial Communication Manager

**Location:** `communication/serial_manager.py`

**Purpose:** Async serial I/O with error handling and reconnection

**Class Design:**

```python
import asyncio
import serial
from typing import AsyncIterator, Dict, Any, Optional
from enum import Enum
import logging

class ConnectionStatus(Enum):
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    ERROR = "error"

class SerialManager:
    """
    Manages asynchronous serial communication with hardware.

    Features:
    - Async I/O using asyncio + threading
    - Auto-reconnection on disconnect
    - Command queue with timeout
    - Stream-based data reading
    """

    def __init__(self, baudrate: int = 115200, timeout: float = 0.1):
        self.baudrate = baudrate
        self.timeout = timeout
        self.serial_port: Optional[serial.Serial] = None
        self.status = ConnectionStatus.DISCONNECTED
        self._read_queue = asyncio.Queue()
        self._write_lock = asyncio.Lock()
        self._read_task: Optional[asyncio.Task] = None
        self.logger = logging.getLogger(__name__)

    async def connect(self, port: str) -> bool:
        """
        Connect to serial port.

        Args:
            port: COM port name (e.g., 'COM3')

        Returns:
            bool: True if successful
        """
        try:
            self.status = ConnectionStatus.CONNECTING

            # Configure serial port
            self.serial_port = serial.Serial(
                port=port,
                baudrate=self.baudrate,
                timeout=self.timeout,
                write_timeout=1.0
            )

            # Clear buffers
            self.serial_port.reset_input_buffer()
            self.serial_port.reset_output_buffer()

            # Start background reader task
            self._read_task = asyncio.create_task(self._background_reader())

            # Test connection with handshake
            await self.send_command("TEST")

            self.status = ConnectionStatus.CONNECTED
            self.logger.info(f"Connected to {port}")
            return True

        except Exception as e:
            self.status = ConnectionStatus.ERROR
            self.logger.error(f"Connection failed: {e}")
            return False

    async def disconnect(self):
        """Close serial connection gracefully."""
        if self._read_task:
            self._read_task.cancel()
            try:
                await self._read_task
            except asyncio.CancelledError:
                pass

        if self.serial_port and self.serial_port.is_open:
            self.serial_port.close()

        self.status = ConnectionStatus.DISCONNECTED
        self.logger.info("Disconnected")

    async def send_command(self, command: str, timeout: float = 2.0) -> bool:
        """
        Send command to hardware.

        Args:
            command: Command string (without newline)
            timeout: Response timeout in seconds

        Returns:
            bool: True if acknowledged
        """
        async with self._write_lock:
            try:
                cmd_bytes = f"{command}\n".encode('utf-8')
                await asyncio.get_event_loop().run_in_executor(
                    None, self.serial_port.write, cmd_bytes
                )
                self.logger.debug(f"Sent: {command}")

                # Wait for acknowledgment (with timeout)
                ack = await asyncio.wait_for(
                    self._read_queue.get(),
                    timeout=timeout
                )

                return "ERROR" not in ack

            except asyncio.TimeoutError:
                self.logger.error(f"Command timeout: {command}")
                return False
            except Exception as e:
                self.logger.error(f"Send error: {e}")
                return False

    async def send_commands(self, commands: List[str]) -> bool:
        """Send multiple commands sequentially."""
        for cmd in commands:
            if not await self.send_command(cmd):
                return False
        return True

    async def read_stream(self) -> AsyncIterator[Dict[str, Any]]:
        """
        Stream data from hardware.

        Yields:
            Dict with parsed data point
        """
        while self.status == ConnectionStatus.CONNECTED:
            try:
                # Get line from queue (with timeout)
                line = await asyncio.wait_for(
                    self._read_queue.get(),
                    timeout=1.0
                )

                # Parse line to data point
                data_point = self._parse_data_line(line)
                if data_point:
                    yield data_point

            except asyncio.TimeoutError:
                continue
            except Exception as e:
                self.logger.error(f"Stream error: {e}")
                break

    async def _background_reader(self):
        """Background task to read serial data."""
        while self.serial_port and self.serial_port.is_open:
            try:
                # Read line (blocking in executor)
                line = await asyncio.get_event_loop().run_in_executor(
                    None, self.serial_port.readline
                )

                if line:
                    decoded = line.decode('utf-8', errors='ignore').strip()
                    if decoded:
                        await self._read_queue.put(decoded)

                await asyncio.sleep(0)  # Yield control

            except Exception as e:
                self.logger.error(f"Reader error: {e}")
                self.status = ConnectionStatus.ERROR
                break

    def _parse_data_line(self, line: str) -> Optional[Dict[str, Any]]:
        """
        Parse hardware response line.

        Format examples:
        - "ADC:12345" -> ADC value
        - "STATUS:COMPLETE" -> status message
        - "12345" -> raw ADC value (v0 protocol)

        Returns:
            Parsed data dict or None if not data
        """
        if line.startswith("ADC:"):
            try:
                value = float(line.split(":")[1])
                return {'type': 'adc', 'value': value}
            except (ValueError, IndexError):
                return None

        elif line.startswith("STATUS:"):
            status = line.split(":")[1]
            return {'type': 'status', 'value': status}

        else:
            # Try parsing as raw ADC value (v0 protocol)
            try:
                value = float(line)
                if 0 <= value <= 32767:
                    return {'type': 'adc', 'value': value}
            except ValueError:
                pass

        return None

    @property
    def is_connected(self) -> bool:
        """Check if connected."""
        return self.status == ConnectionStatus.CONNECTED
```

### 2.3 Parameter Validation with Pydantic

**Location:** `experiments/parameters.py`

**Purpose:** Type-safe parameter definitions with automatic validation

**Example Schema:**

```python
from pydantic import BaseModel, validator, Field
from typing import Optional

class CVParameters(BaseModel):
    """Cyclic Voltammetry parameters with validation."""

    # Voltage range
    start_voltage: float = Field(
        default=-0.5,
        ge=-1.5,
        le=1.5,
        description="Starting potential (V)"
    )

    end_voltage: float = Field(
        default=0.5,
        ge=-1.5,
        le=1.5,
        description="Vertex potential (V)"
    )

    # Scan parameters
    scan_rate: float = Field(
        default=0.1,
        gt=0.0,
        le=1.0,
        description="Scan rate (V/s)"
    )

    cycles: int = Field(
        default=2,
        ge=1,
        le=100,
        description="Number of cycles"
    )

    # Hardware settings
    settling_time: float = Field(
        default=0.1,
        ge=0.0,
        le=10.0,
        description="Initial settling time (s)"
    )

    current_mode: int = Field(
        default=0,
        ge=0,
        le=1,
        description="0: ±500µA (10kΩ), 1: ±100nA (1MΩ)"
    )

    offset_current: Optional[float] = Field(
        default=0.0,
        description="Offset correction (µA)"
    )

    @validator('end_voltage')
    def voltages_different(cls, v, values):
        """Ensure start and end voltages are different."""
        if 'start_voltage' in values and abs(v - values['start_voltage']) < 0.01:
            raise ValueError('Start and end voltages must differ by at least 10mV')
        return v

    @validator('scan_rate')
    def scan_rate_reasonable(cls, v, values):
        """Validate scan rate for voltage range."""
        if 'start_voltage' in values and 'end_voltage' in values:
            voltage_range = abs(values['end_voltage'] - values['start_voltage'])
            min_time = voltage_range / v
            if min_time < 0.5:
                raise ValueError(
                    f'Scan rate too fast for voltage range. '
                    f'Minimum cycle time: {min_time:.2f}s'
                )
        return v

    class Config:
        """Pydantic configuration."""
        validate_assignment = True  # Validate on attribute change
        extra = 'forbid'  # Disallow extra fields

    def to_firmware_command(self) -> str:
        """
        Generate firmware command string.

        Returns:
            Command string (e.g., "START:-0.5:0.5:0.1:2")
        """
        return f"START:{self.start_voltage}:{self.end_voltage}:{self.scan_rate}:{self.cycles}"
```

### 2.4 Data Manager

**Location:** `data/data_manager.py`

**Purpose:** Centralized data acquisition, storage, and export

**Class Design:**

```python
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional
from datetime import datetime
import json

class DataManager:
    """
    Manages experiment data lifecycle.

    Features:
    - Real-time data buffering
    - Pandas DataFrame storage
    - Multiple export formats
    - Data processing pipeline
    """

    def __init__(self, experiment_name: str):
        self.experiment_name = experiment_name
        self.buffer: Dict[str, List[float]] = {
            'time': [],
            'voltage': [],
            'current': []
        }
        self.metadata: Dict[str, Any] = {
            'timestamp': datetime.now().isoformat(),
            'experiment': experiment_name
        }
        self._df: Optional[pd.DataFrame] = None
        self._start_time: Optional[float] = None

    def start_acquisition(self):
        """Initialize acquisition."""
        self.clear()
        self._start_time = datetime.now().timestamp()

    def append(self, data_point: Dict[str, float]):
        """
        Add data point to buffer.

        Args:
            data_point: Dict with 'voltage', 'current', etc.
        """
        # Calculate elapsed time
        elapsed = datetime.now().timestamp() - self._start_time
        self.buffer['time'].append(elapsed)

        for key, value in data_point.items():
            if key in self.buffer:
                self.buffer[key].append(value)

    def get_latest(self, n: int = 1) -> Dict[str, List[float]]:
        """Get last N data points."""
        return {
            key: values[-n:] for key, values in self.buffer.items()
        }

    def get_all(self) -> Dict[str, List[float]]:
        """Get all buffered data."""
        return self.buffer.copy()

    def to_dataframe(self) -> pd.DataFrame:
        """
        Convert buffer to pandas DataFrame.

        Returns:
            DataFrame with all data
        """
        if self._df is None or len(self.buffer['time']) > len(self._df):
            self._df = pd.DataFrame(self.buffer)
        return self._df

    def clear(self):
        """Clear all data."""
        for key in self.buffer:
            self.buffer[key].clear()
        self._df = None

    def export_csv(self, filepath: str, params: BaseModel):
        """
        Export to CSV with metadata header.

        Args:
            filepath: Output file path
            params: Experiment parameters
        """
        df = self.to_dataframe()

        with open(filepath, 'w') as f:
            # Write metadata header
            f.write(f"# SaxStat Experiment Data\n")
            f.write(f"# Timestamp: {self.metadata['timestamp']}\n")
            f.write(f"# Experiment: {self.experiment_name}\n")
            f.write(f"#\n")
            f.write(f"# Parameters:\n")
            for key, value in params.dict().items():
                f.write(f"#   {key}: {value}\n")
            f.write(f"#\n")

            # Write data
            df.to_csv(f, index=False)

    def export_json(self, filepath: str, params: BaseModel):
        """Export to JSON format."""
        data = {
            'metadata': self.metadata,
            'parameters': params.dict(),
            'data': self.to_dataframe().to_dict(orient='list')
        }

        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)

    @property
    def point_count(self) -> int:
        """Number of data points collected."""
        return len(self.buffer['time'])
```

### 2.5 Plot Manager

**Location:** `plotting/plot_manager.py`

**Purpose:** Real-time plot updates with performance optimization

**Class Design:**

```python
import pyqtgraph as pg
from PyQt5.QtCore import QTimer
from typing import Dict, Optional
import numpy as np

class PlotManager:
    """
    Manages real-time plotting with performance optimization.

    Features:
    - Adaptive downsampling for large datasets
    - Dual plot support (CV and time-series)
    - Auto-scaling and range adjustment
    """

    def __init__(self, cv_widget: pg.PlotWidget, time_widget: pg.PlotWidget):
        self.cv_widget = cv_widget
        self.time_widget = time_widget

        # Setup CV plot (voltage vs current)
        self.cv_widget.setLabel('left', 'Current', units='µA')
        self.cv_widget.setLabel('bottom', 'Applied Voltage', units='V')
        self.cv_widget.showGrid(x=True, y=True)
        self.cv_widget.setBackground('w')
        self.cv_curve = self.cv_widget.plot(pen=pg.mkPen('b', width=2))

        # Setup time-series plot (voltage vs time)
        self.time_widget.setLabel('left', 'Voltage', units='V')
        self.time_widget.setLabel('bottom', 'Time', units='s')
        self.time_widget.showGrid(x=True, y=True)
        self.time_widget.setBackground('w')
        self.time_curve = self.time_widget.plot(pen=pg.mkPen('r', width=2))

        # Update timer
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self._update_plots)
        self.update_interval_ms = 50  # 20 FPS

        self.data_manager: Optional[DataManager] = None
        self._downsample_threshold = 5000  # Points before downsampling

    def set_data_manager(self, data_manager: DataManager):
        """Connect to data manager."""
        self.data_manager = data_manager

    def start_updates(self):
        """Start periodic plot updates."""
        self.update_timer.start(self.update_interval_ms)

    def stop_updates(self):
        """Stop plot updates."""
        self.update_timer.stop()

    def _update_plots(self):
        """Update both plots from data manager."""
        if not self.data_manager:
            return

        data = self.data_manager.get_all()

        if len(data['time']) < 2:
            return

        # Downsample if needed
        time, voltage, current = self._downsample(
            data['time'],
            data['voltage'],
            data['current']
        )

        # Update CV plot (voltage vs current)
        self.cv_curve.setData(voltage, current)

        # Update time-series plot
        self.time_curve.setData(time, voltage)

        # Auto-range Y-axis (keep X fixed after initial setup)
        if len(time) > 10:
            self.cv_widget.enableAutoRange(axis='y', enable=True)
            self.time_widget.enableAutoRange(axis='y', enable=True)

    def _downsample(self, time, voltage, current):
        """
        Intelligently downsample data for plotting.

        Strategy:
        - If < threshold: plot all points
        - If > threshold: use min/max/avg decimation

        Returns:
            Tuple of (time, voltage, current) arrays
        """
        n_points = len(time)

        if n_points < self._downsample_threshold:
            return time, voltage, current

        # Calculate decimation factor
        factor = n_points // self._downsample_threshold

        # Downsample using striding (simple but effective)
        time_ds = time[::factor]
        voltage_ds = voltage[::factor]
        current_ds = current[::factor]

        return time_ds, voltage_ds, current_ds

    def clear(self):
        """Clear all plots."""
        self.cv_curve.setData([], [])
        self.time_curve.setData([], [])

    def export_image(self, filepath: str, plot_type: str = 'cv'):
        """
        Export plot to image.

        Args:
            filepath: Output file path
            plot_type: 'cv' or 'time'
        """
        widget = self.cv_widget if plot_type == 'cv' else self.time_widget
        exporter = pg.exporters.ImageExporter(widget.plotItem)
        exporter.export(filepath)
```

### 2.6 Configuration System

**Location:** `config/config_manager.py`

**Purpose:** Persistent settings and calibration data

**Class Design:**

```python
import json
from pathlib import Path
from typing import Dict, Any, Optional
from pydantic import BaseModel

class AppConfig(BaseModel):
    """Application-level configuration."""
    last_port: Optional[str] = None
    last_experiment: str = "cv"
    autosave_enabled: bool = True
    autosave_directory: str = "./data"
    window_geometry: Optional[Dict[str, int]] = None

class CalibrationData(BaseModel):
    """Hardware calibration data."""
    offset_current_mode0: float = 0.0  # 10kΩ mode
    offset_current_mode1: float = 0.0  # 1MΩ mode
    calibration_date: Optional[str] = None

class ConfigManager:
    """
    Manages application configuration and calibration.

    Features:
    - JSON-based storage
    - Automatic save on change
    - Default values
    """

    def __init__(self, config_dir: str = "./config"):
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(parents=True, exist_ok=True)

        self.config_file = self.config_dir / "app_config.json"
        self.calibration_file = self.config_dir / "calibration.json"

        self.app_config = self._load_config()
        self.calibration = self._load_calibration()

    def _load_config(self) -> AppConfig:
        """Load application config from file."""
        if self.config_file.exists():
            try:
                with open(self.config_file) as f:
                    data = json.load(f)
                return AppConfig(**data)
            except Exception:
                pass
        return AppConfig()

    def _load_calibration(self) -> CalibrationData:
        """Load calibration data from file."""
        if self.calibration_file.exists():
            try:
                with open(self.calibration_file) as f:
                    data = json.load(f)
                return CalibrationData(**data)
            except Exception:
                pass
        return CalibrationData()

    def save_config(self):
        """Save application config to file."""
        with open(self.config_file, 'w') as f:
            json.dump(self.app_config.dict(), f, indent=2)

    def save_calibration(self):
        """Save calibration data to file."""
        with open(self.calibration_file, 'w') as f:
            json.dump(self.calibration.dict(), f, indent=2)

    def get_last_experiment_params(self, experiment_type: str) -> Optional[Dict[str, Any]]:
        """Get last used parameters for experiment type."""
        params_file = self.config_dir / f"last_params_{experiment_type}.json"
        if params_file.exists():
            try:
                with open(params_file) as f:
                    return json.load(f)
            except Exception:
                pass
        return None

    def save_experiment_params(self, experiment_type: str, params: BaseModel):
        """Save experiment parameters for future sessions."""
        params_file = self.config_dir / f"last_params_{experiment_type}.json"
        with open(params_file, 'w') as f:
            json.dump(params.dict(), f, indent=2)
```

---

## 3. Experiment System

### 3.1 Experiment Registry

**Location:** `experiments/registry.py`

**Purpose:** Plugin-style registration for experiment types

**Implementation:**

```python
from typing import Dict, Type, Callable
from .base_experiment import BaseExperiment
from pydantic import BaseModel

class ExperimentRegistry:
    """
    Central registry for experiment types.

    Features:
    - Dynamic registration
    - Lookup by name or code
    - Parameter schema association
    """

    def __init__(self):
        self._experiments: Dict[str, Type[BaseExperiment]] = {}
        self._parameters: Dict[str, Type[BaseModel]] = {}
        self._metadata: Dict[str, Dict[str, str]] = {}

    def register(
        self,
        name: str,
        experiment_class: Type[BaseExperiment],
        parameter_class: Type[BaseModel],
        display_name: str,
        description: str
    ):
        """
        Register new experiment type.

        Args:
            name: Internal name (e.g., 'cv')
            experiment_class: Experiment implementation class
            parameter_class: Pydantic parameter model
            display_name: UI display name (e.g., 'Cyclic Voltammetry')
            description: Short description
        """
        self._experiments[name] = experiment_class
        self._parameters[name] = parameter_class
        self._metadata[name] = {
            'display_name': display_name,
            'description': description
        }

    def create_experiment(self, name: str, params: BaseModel) -> BaseExperiment:
        """
        Create experiment instance.

        Args:
            name: Experiment name
            params: Validated parameters

        Returns:
            Experiment instance
        """
        if name not in self._experiments:
            raise ValueError(f"Unknown experiment: {name}")

        return self._experiments[name](params)

    def get_parameter_class(self, name: str) -> Type[BaseModel]:
        """Get parameter schema for experiment."""
        return self._parameters.get(name)

    def list_experiments(self) -> Dict[str, Dict[str, str]]:
        """Get all registered experiments."""
        return self._metadata.copy()

    @property
    def experiment_names(self) -> list:
        """List of registered experiment names."""
        return list(self._experiments.keys())

# Global registry instance
registry = ExperimentRegistry()

def register_experiment(name: str, display_name: str, description: str):
    """
    Decorator for registering experiments.

    Usage:
        @register_experiment('cv', 'Cyclic Voltammetry', 'Voltage sweep...')
        class CVExperiment(BaseExperiment):
            ...
    """
    def decorator(experiment_class: Type[BaseExperiment]):
        # Find associated parameter class (by convention)
        param_class_name = f"{experiment_class.__name__.replace('Experiment', '')}Parameters"
        # This would need proper import - simplified here
        param_class = BaseModel  # Placeholder

        registry.register(
            name,
            experiment_class,
            param_class,
            display_name,
            description
        )
        return experiment_class
    return decorator
```

### 3.2 Cyclic Voltammetry Implementation

**Location:** `experiments/cyclic_voltammetry.py`

**Full CV Implementation:**

```python
from .base_experiment import BaseExperiment
from .parameters import CVParameters
from typing import Dict, Any, List
import time

class CVExperiment(BaseExperiment):
    """
    Cyclic Voltammetry experiment implementation.

    Technique:
    - Linear voltage sweep between two vertex potentials
    - Multiple cycles
    - Measures current vs voltage
    """

    def __init__(self, params: CVParameters):
        super().__init__(params)
        self.params: CVParameters = params  # Type hint for IDE
        self._cycle_count = 0
        self._expected_points = 0

    @property
    def technique_name(self) -> str:
        return "Cyclic Voltammetry"

    @property
    def data_columns(self) -> List[str]:
        return ['time', 'voltage', 'current', 'cycle']

    @property
    def plot_config(self) -> Dict[str, Any]:
        return {
            'x_label': 'Applied Voltage (V)',
            'y_label': 'Current (µA)',
            'x_range': (self.params.start_voltage, self.params.end_voltage),
            'title': f'Cyclic Voltammogram ({self.params.cycles} cycles)'
        }

    def validate(self) -> bool:
        """
        Validate CV-specific constraints.
        Already validated by Pydantic, but can add runtime checks.
        """
        # Check voltage range makes sense
        voltage_diff = abs(self.params.end_voltage - self.params.start_voltage)
        if voltage_diff < 0.01:
            return False

        # Estimate total points
        voltage_range = voltage_diff * 2  # Forward + reverse
        cycle_time = voltage_range / self.params.scan_rate
        total_time = cycle_time * self.params.cycles

        # Assuming ~100 points per second
        self._expected_points = int(total_time * 100)

        return True

    def generate_commands(self) -> List[str]:
        """
        Generate firmware commands for CV.

        Protocol (v03):
        - START:start_v:end_v:scan_rate:cycles
        - MODE_0 or MODE_1 for current range
        """
        commands = []

        # Set current range mode
        commands.append(f"MODE_{self.params.current_mode}")

        # CV parameters
        commands.append(self.params.to_firmware_command())

        return commands

    def setup_data_structures(self):
        """Setup CV-specific data storage."""
        self.data['cycle'] = []
        self._cycle_count = 0

    def process_data_point(self, raw_data: Dict[str, Any]) -> Dict[str, float]:
        """
        Convert raw ADC value to current.

        Args:
            raw_data: {'type': 'adc', 'value': 12345}

        Returns:
            {'voltage': V, 'current': I}
        """
        if raw_data['type'] != 'adc':
            return {}

        adc_value = raw_data['value']

        # Calculate applied voltage based on elapsed time and waveform
        elapsed = time.time() - self._start_time if hasattr(self, '_start_time') else 0
        applied_voltage = self._calculate_voltage_at_time(elapsed)

        # Convert ADC to voltage (ADS1115: 16-bit, ±4.096V range)
        v_out = (adc_value / 32767.0) * 4.096

        # Calculate current using Ohm's law
        # I = (V_ref - V_out - V_applied) / R_TIA
        v_ref = 1.0  # Reference voltage

        # Select resistance based on mode
        if self.params.current_mode == 0:
            r_tia = 10000.0  # 10 kΩ
            current_ua = ((2 * v_ref - v_out - applied_voltage) / r_tia) * 1e6
        else:
            r_tia = 1000000.0  # 1 MΩ
            current_na = ((2 * v_ref - v_out - applied_voltage) / r_tia) * 1e9
            current_ua = current_na / 1000.0  # Convert to µA for consistency

        # Apply offset correction
        current_ua -= self.params.offset_current

        # Track cycle number
        cycle = int(elapsed / self._cycle_time) if hasattr(self, '_cycle_time') else 0

        return {
            'voltage': applied_voltage,
            'current': current_ua,
            'cycle': cycle
        }

    def _calculate_voltage_at_time(self, elapsed: float) -> float:
        """
        Calculate applied voltage based on CV waveform.

        Waveform: Triangle wave between start_voltage and end_voltage
        """
        voltage_range = abs(self.params.end_voltage - self.params.start_voltage)
        half_cycle_time = voltage_range / self.params.scan_rate
        self._cycle_time = 2 * half_cycle_time

        # Determine position in cycle
        cycle_time = elapsed % self._cycle_time

        if cycle_time < half_cycle_time:
            # Forward sweep
            fraction = cycle_time / half_cycle_time
            voltage = self.params.start_voltage + fraction * (
                self.params.end_voltage - self.params.start_voltage
            )
        else:
            # Reverse sweep
            fraction = (cycle_time - half_cycle_time) / half_cycle_time
            voltage = self.params.end_voltage - fraction * (
                self.params.end_voltage - self.params.start_voltage
            )

        return voltage

    def is_complete(self) -> bool:
        """Check if CV is complete."""
        if not hasattr(self, '_start_time'):
            self._start_time = time.time()
            return False

        elapsed = time.time() - self._start_time
        voltage_range = abs(self.params.end_voltage - self.params.start_voltage) * 2
        total_time = (voltage_range / self.params.scan_rate) * self.params.cycles

        return elapsed >= total_time

    def post_process(self):
        """Post-processing: calculate summary statistics."""
        if len(self.data['current']) > 0:
            import numpy as np

            self.metadata['peak_anodic'] = float(np.max(self.data['current']))
            self.metadata['peak_cathodic'] = float(np.min(self.data['current']))
            self.metadata['mean_current'] = float(np.mean(self.data['current']))
            self.metadata['total_points'] = len(self.data['current'])
```

### 3.3 Adding New Experiments

**Template for LSV (Linear Sweep Voltammetry):**

```python
# experiments/linear_sweep.py

from .base_experiment import BaseExperiment
from .parameters import LSVParameters
from typing import Dict, Any, List

class LSVExperiment(BaseExperiment):
    """Linear Sweep Voltammetry - single sweep from start to end."""

    def __init__(self, params: LSVParameters):
        super().__init__(params)
        self.params: LSVParameters = params

    @property
    def technique_name(self) -> str:
        return "Linear Sweep Voltammetry"

    @property
    def data_columns(self) -> List[str]:
        return ['time', 'voltage', 'current']

    @property
    def plot_config(self) -> Dict[str, Any]:
        return {
            'x_label': 'Applied Voltage (V)',
            'y_label': 'Current (µA)',
            'title': 'Linear Sweep Voltammogram'
        }

    def validate(self) -> bool:
        return True

    def generate_commands(self) -> List[str]:
        return [
            f"MODE_{self.params.current_mode}",
            f"LSV:{self.params.start_voltage}:{self.params.end_voltage}:{self.params.scan_rate}"
        ]

    def process_data_point(self, raw_data: Dict[str, Any]) -> Dict[str, float]:
        # Similar to CV, but single sweep
        pass

    def is_complete(self) -> bool:
        # Check if reached end voltage
        pass

# Register with registry
from .registry import registry
registry.register(
    'lsv',
    LSVExperiment,
    LSVParameters,
    'Linear Sweep Voltammetry',
    'Single potential sweep'
)
```

---

## 4. Communication Protocol

### 4.1 Protocol Specification

**Based on v0 firmware analysis:**

**Command Format (ASCII):**
```
<COMMAND>[:param1:param2:...]\n
```

**Supported Commands:**

| Command | Parameters | Description | Response |
|---------|-----------|-------------|----------|
| START | start_v:end_v:rate:cycles | Start CV | "START_CONFIRMED" |
| STOP | - | Stop experiment | "CV stopped." |
| CALIBRATE | - | Read ADC for calibration | ADC value (int) |
| MODE_0 | - | Set ±500µA range (10kΩ) | "Switched to mode: 0" |
| MODE_1 | - | Set ±100nA range (1MΩ) | "Switched to mode: 1" |
| TEST | - | Connection test | "OK" |

**Data Stream Format:**

During experiment execution, firmware sends continuous ADC readings:
```
12345\n
12456\n
12567\n
...
CV complete.\n
```

**Status Messages:**
- `START_CONFIRMED` - Experiment started
- `CV stopped.` - Experiment stopped
- `CV complete.` - Experiment finished normally
- `ADC:ERROR` - ADC read error
- `Error: ...` - Other errors

**Timing:**
- Baudrate: 115200
- Timeout: 100ms read timeout
- Command acknowledgment: Within 2 seconds
- Data rate: ~100 Hz (depends on scan rate)

### 4.2 Protocol Handler

**Location:** `communication/protocol.py`

```python
from enum import Enum
from typing import Dict, Any, Optional

class MessageType(Enum):
    """Types of messages from hardware."""
    DATA = "data"
    STATUS = "status"
    ERROR = "error"
    ACKNOWLEDGMENT = "ack"

class ProtocolHandler:
    """
    Parses firmware protocol messages.

    Handles both v0 protocol (simple) and future JSON protocol.
    """

    @staticmethod
    def parse_response(line: str) -> Dict[str, Any]:
        """
        Parse firmware response line.

        Args:
            line: Raw line from serial port

        Returns:
            Dict with parsed message
        """
        line = line.strip()

        # Status messages
        if line in ["START_CONFIRMED", "CV stopped.", "CV complete."]:
            return {
                'type': MessageType.STATUS,
                'message': line
            }

        # Error messages
        if line.startswith("Error:") or line == "ADC:ERROR":
            return {
                'type': MessageType.ERROR,
                'message': line
            }

        # Mode switch acknowledgment
        if line.startswith("Switched to mode:"):
            return {
                'type': MessageType.ACKNOWLEDGMENT,
                'message': line
            }

        # ADC data (numeric)
        try:
            value = float(line)
            if 0 <= value <= 32767:
                return {
                    'type': MessageType.DATA,
                    'adc_value': value
                }
        except ValueError:
            pass

        # Unknown message
        return {
            'type': MessageType.ERROR,
            'message': f"Unknown response: {line}"
        }

    @staticmethod
    def format_command(command: str, params: list = None) -> str:
        """
        Format command string.

        Args:
            command: Command name
            params: Optional parameters

        Returns:
            Formatted command string
        """
        if params:
            return f"{command}:{':'.join(map(str, params))}\n"
        return f"{command}\n"
```

### 4.3 Error Handling Strategy

**Categories:**

1. **Connection Errors**
   - Serial port not found
   - Connection timeout
   - Unexpected disconnect
   - **Action:** Notify user, attempt reconnection

2. **Command Errors**
   - Invalid parameters (caught by pydantic)
   - Firmware reports error
   - Command timeout
   - **Action:** Show error dialog, log details

3. **Data Errors**
   - Invalid ADC values
   - Corrupted data
   - Missing data points
   - **Action:** Skip point, log warning

4. **Hardware Errors**
   - ADC read failure
   - DAC write failure
   - **Action:** Abort experiment, notify user

**Recovery Strategies:**

```python
# In SerialManager
async def send_with_retry(self, command: str, max_retries: int = 3) -> bool:
    """Send command with automatic retry."""
    for attempt in range(max_retries):
        try:
            success = await self.send_command(command)
            if success:
                return True
            self.logger.warning(f"Retry {attempt+1}/{max_retries}")
        except Exception as e:
            self.logger.error(f"Attempt {attempt+1} failed: {e}")
            await asyncio.sleep(0.5)
    return False
```

---

## 5. File Structure

### 5.1 Complete Directory Layout

```
saxstat_gui_v1/
├── main.py                          # Application entry point
├── requirements.txt                 # Python dependencies
├── README.md                        # Project documentation
├── .gitignore                       # Git ignore file
│
├── gui/                             # GUI Layer
│   ├── __init__.py
│   ├── main_window.py               # MainWindow class
│   ├── parameter_panel.py           # Parameter input widgets
│   ├── plot_panel.py                # Plot display area
│   ├── status_bar.py                # Status/connection display
│   ├── experiment_selector.py       # Experiment type dropdown
│   └── dialogs/                     # Modal dialogs
│       ├── __init__.py
│       ├── calibration_dialog.py    # Calibration wizard
│       ├── settings_dialog.py       # Settings editor
│       └── about_dialog.py          # About/help dialog
│
├── experiments/                     # Experiment Definitions
│   ├── __init__.py
│   ├── base_experiment.py           # BaseExperiment abstract class
│   ├── registry.py                  # ExperimentRegistry
│   ├── parameters.py                # Pydantic parameter models
│   ├── cyclic_voltammetry.py        # CV implementation
│   ├── linear_sweep.py              # LSV implementation
│   ├── chronoamperometry.py         # CA implementation
│   └── square_wave.py               # SWV implementation (future)
│
├── communication/                   # Hardware Communication
│   ├── __init__.py
│   ├── serial_manager.py            # SerialManager class
│   ├── protocol.py                  # Protocol parsing
│   └── port_detector.py             # Serial port detection
│
├── data/                            # Data Management
│   ├── __init__.py
│   ├── data_manager.py              # DataManager class
│   ├── processors.py                # Data processing functions
│   └── exporters.py                 # Export to CSV/JSON/HDF5
│
├── plotting/                        # Plotting System
│   ├── __init__.py
│   ├── plot_manager.py              # PlotManager class
│   ├── cv_plot_widget.py            # CV-specific plot
│   ├── time_plot_widget.py          # Time-series plot
│   └── themes.py                    # Plot styling
│
├── config/                          # Configuration System
│   ├── __init__.py
│   ├── config_manager.py            # ConfigManager class
│   ├── defaults.py                  # Default values
│   └── schemas.py                   # Config schemas
│
├── utils/                           # Utilities
│   ├── __init__.py
│   ├── validators.py                # Input validators
│   ├── logger.py                    # Logging setup
│   └── helpers.py                   # Helper functions
│
└── tests/                           # Unit Tests
    ├── __init__.py
    ├── test_experiments.py          # Experiment tests
    ├── test_serial.py               # Serial communication tests
    ├── test_data.py                 # Data management tests
    └── fixtures/                    # Test fixtures
        ├── mock_serial.py           # Mock serial port
        └── sample_data.py           # Sample datasets
```

### 5.2 Class Dependency Diagram

```
┌──────────────────────────────────────────────────────────────┐
│                         SaxStatApp                           │
│                      (main_window.py)                        │
└────┬──────────┬──────────┬──────────┬─────────────┬─────────┘
     │          │          │          │             │
     ▼          ▼          ▼          ▼             ▼
┌─────────┐ ┌────────┐ ┌────────┐ ┌──────────┐ ┌──────────┐
│   GUI   │ │Serial  │ │  Data  │ │   Plot   │ │  Config  │
│ Manager │ │Manager │ │Manager │ │ Manager  │ │ Manager  │
└────┬────┘ └───┬────┘ └───┬────┘ └────┬─────┘ └────┬─────┘
     │          │          │           │            │
     │          │          │           │            │
     ▼          ▼          ▼           ▼            ▼
┌─────────┐ ┌────────┐ ┌────────┐ ┌──────────┐ ┌──────────┐
│Parameter│ │Protocol│ │Processor││PlotWidget│ │Settings  │
│ Panel   │ │Handler │ │Exporter │ │          │ │Calibrate │
└─────────┘ └────────┘ └────────┘ └──────────┘ └──────────┘
     │
     ▼
┌──────────────────┐
│ Experiment       │
│ Registry         │
└────┬─────────────┘
     │
     ▼
┌──────────────────┐         ┌──────────────────┐
│ BaseExperiment   │◄────────│  CVExperiment    │
│   (abstract)     │         │  LSVExperiment   │
└──────────────────┘         │  CAExperiment    │
                             └──────────────────┘
```

### 5.3 Key Module Interfaces

**SaxStatApp (main_window.py):**
```python
class SaxStatApp(QMainWindow):
    def __init__(self)
    def connect_to_hardware(port: str) -> bool
    def disconnect_from_hardware()
    def start_experiment(experiment_name: str, params: BaseModel)
    def stop_experiment()
    def save_data(filepath: str)
```

**SerialManager (communication/serial_manager.py):**
```python
class SerialManager:
    async def connect(port: str) -> bool
    async def disconnect()
    async def send_command(command: str) -> bool
    async def read_stream() -> AsyncIterator[Dict]
    @property def is_connected() -> bool
```

**DataManager (data/data_manager.py):**
```python
class DataManager:
    def start_acquisition()
    def append(data_point: Dict)
    def get_all() -> Dict[str, List]
    def to_dataframe() -> pd.DataFrame
    def export_csv(filepath: str, params: BaseModel)
```

**PlotManager (plotting/plot_manager.py):**
```python
class PlotManager:
    def set_data_manager(data_manager: DataManager)
    def start_updates()
    def stop_updates()
    def clear()
    def export_image(filepath: str)
```

---

## 6. Data Flow & State Management

### 6.1 Application State Machine

```
┌──────────────┐
│ DISCONNECTED │
└───────┬──────┘
        │ connect()
        ▼
┌──────────────┐
│  CONNECTED   │◄──────────────┐
└───────┬──────┘               │
        │ start_experiment()   │
        ▼                      │
┌──────────────┐               │
│CONFIGURING   │               │
└───────┬──────┘               │
        │ commands sent        │
        ▼                      │
┌──────────────┐               │
│   RUNNING    │               │
└───┬──────┬───┘               │
    │      │                   │
    │ stop()│                  │
    │ complete()               │
    │      │                   │
    ▼      ▼                   │
┌──────────────┐               │
│  COMPLETED   │───────────────┘
└──────────────┘
        │
        │ disconnect()
        ▼
┌──────────────┐
│ DISCONNECTED │
└──────────────┘
```

### 6.2 Data Flow During Experiment

```
User Input                    Application                   Hardware
──────────────────────────────────────────────────────────────────────

1. Enter parameters    →    Validate (Pydantic)
                                   │
2. Click "Start"       →    Create experiment object
                                   │
                       →    Generate commands
                                   │
                       →    Send to SerialManager
                                   │              →    START:...
                                   │              ←    START_CONFIRMED
                                   │
                       →    Start DataManager
                                   │
                       →    Start PlotManager
                                   │
                       ←──────  ADC data stream ←────  12345
                       │                              12456
                       │                              12457
                       ▼                              ...
              Process data point
                       │
              ├─────────┼─────────┐
              ▼         ▼         ▼
         DataManager  PlotManager  GUI
              │         │         │
         Store point  Update plot  Update status
              │         │         │
              └─────────┴─────────┘
                       │
                       │              ←────  CV complete.
                       ▼
              Post-process
                       │
              Update UI state
                       │
3. Click "Save"  →  Export to CSV/JSON
```

### 6.3 Threading Model

**Main Thread:**
- Qt event loop
- GUI rendering
- User input handling

**Asyncio Thread:**
- Serial I/O operations
- Command sending
- Data streaming

**Timer Thread (Qt):**
- Plot updates (50ms intervals)
- Status bar updates

**Data Flow Between Threads:**

```python
# In SaxStatApp.__init__
self.asyncio_thread = QThread()
self.serial_manager.moveToThread(self.asyncio_thread)
self.asyncio_thread.start()

# Signal/slot connections
self.serial_manager.data_received.connect(self.on_data_received)
self.serial_manager.status_changed.connect(self.on_status_changed)

# Thread-safe data access
self.data_lock = threading.Lock()

def on_data_received(self, data: Dict):
    with self.data_lock:
        self.data_manager.append(data)
```

---

## 7. Implementation Plan

### Phase 1: Core Infrastructure (Weeks 1-2)

**Goals:**
- Establish project structure
- Implement base classes
- Basic serial communication
- Simple GUI skeleton

**Tasks:**

1. **Project Setup**
   - [ ] Create directory structure
   - [ ] Setup virtual environment
   - [ ] Install dependencies (requirements.txt)
   - [ ] Configure logging system
   - [ ] Initialize git repository

2. **Base Experiment Class**
   - [ ] Implement BaseExperiment abstract class
   - [ ] Define experiment lifecycle methods
   - [ ] Create ExperimentStatus enum
   - [ ] Add observer pattern for status updates
   - [ ] Write unit tests

3. **Serial Communication**
   - [ ] Implement SerialManager class
   - [ ] Add async I/O with asyncio
   - [ ] Create ProtocolHandler
   - [ ] Test with mock serial port
   - [ ] Test with actual hardware

4. **Basic GUI**
   - [ ] Create MainWindow with QMainWindow
   - [ ] Add connection panel (port selector, connect button)
   - [ ] Add status bar
   - [ ] Implement port detection
   - [ ] Test connection flow

**Deliverable:** Can connect to hardware and send/receive basic commands

---

### Phase 2: CV Implementation (Weeks 3-4)

**Goals:**
- Complete CV experiment
- Real-time plotting
- Parameter validation
- Match v0 functionality

**Tasks:**

1. **CV Parameter Schema**
   - [ ] Define CVParameters with pydantic
   - [ ] Add all validators
   - [ ] Test validation edge cases
   - [ ] Create parameter panel UI

2. **CV Experiment Class**
   - [ ] Implement CVExperiment
   - [ ] Override all abstract methods
   - [ ] Test voltage ramp calculation
   - [ ] Test current conversion
   - [ ] Validate against v0 GUI

3. **Data Management**
   - [ ] Implement DataManager
   - [ ] Add real-time buffering
   - [ ] Test with simulated data
   - [ ] Add pandas DataFrame export

4. **Plotting**
   - [ ] Implement PlotManager
   - [ ] Create CV plot widget
   - [ ] Create time-series plot widget
   - [ ] Add downsampling logic
   - [ ] Test performance with large datasets

5. **Integration Testing**
   - [ ] Run full CV experiment
   - [ ] Compare with v0 GUI output
   - [ ] Verify data accuracy
   - [ ] Test edge cases (stop, abort)

**Deliverable:** Fully functional CV experiment matching v0 capabilities

---

### Phase 3: Additional Experiments (Weeks 5-6)

**Goals:**
- Add LSV and CA techniques
- Demonstrate extensibility
- Refine experiment registry

**Tasks:**

1. **Experiment Registry**
   - [ ] Implement ExperimentRegistry
   - [ ] Add registration decorator
   - [ ] Create experiment selector UI
   - [ ] Test dynamic experiment switching

2. **Linear Sweep Voltammetry**
   - [ ] Define LSVParameters
   - [ ] Implement LSVExperiment
   - [ ] Add to registry
   - [ ] Test with hardware

3. **Chronoamperometry**
   - [ ] Define CAParameters
   - [ ] Implement CAExperiment
   - [ ] Add to registry
   - [ ] Test with hardware

4. **Parameter Persistence**
   - [ ] Implement ConfigManager
   - [ ] Save last parameters per experiment
   - [ ] Load on startup
   - [ ] Test save/load cycle

**Deliverable:** Three working experiment types with persistent configuration

---

### Phase 4: Enhanced Features (Weeks 7-8)

**Goals:**
- Data export options
- Calibration wizard
- Error handling polish
- User documentation

**Tasks:**

1. **Data Export**
   - [ ] CSV export with metadata
   - [ ] JSON export
   - [ ] Plot image export (PNG, SVG)
   - [ ] Batch export for multiple runs

2. **Calibration System**
   - [ ] Implement CalibrationData model
   - [ ] Create calibration dialog
   - [ ] Add offset current calibration
   - [ ] Store calibration per current mode
   - [ ] Auto-apply on experiment start

3. **Configuration UI**
   - [ ] Settings dialog
   - [ ] Hardware settings
   - [ ] Plot preferences
   - [ ] Autosave configuration

4. **Error Handling**
   - [ ] Comprehensive error messages
   - [ ] Connection recovery
   - [ ] Data validation warnings
   - [ ] User-friendly error dialogs

5. **Documentation**
   - [ ] User manual (Markdown)
   - [ ] Parameter descriptions
   - [ ] Troubleshooting guide
   - [ ] Example workflows

**Deliverable:** Production-ready GUI with full feature set

---

### Phase 5: Testing & Packaging (Week 9)

**Tasks:**

1. **Testing**
   - [ ] Unit tests for all modules (>80% coverage)
   - [ ] Integration tests for full workflows
   - [ ] Hardware validation tests
   - [ ] Performance profiling

2. **Bug Fixes**
   - [ ] Address all critical bugs
   - [ ] Fix UI responsiveness issues
   - [ ] Resolve data accuracy problems

3. **Packaging**
   - [ ] Create standalone executable (PyInstaller)
   - [ ] Windows installer
   - [ ] Include dependencies
   - [ ] Test on clean Windows install

4. **Release**
   - [ ] Version 1.0.0 tag
   - [ ] Release notes
   - [ ] User documentation
   - [ ] Example datasets

**Deliverable:** SaxStat GUI v1.0.0 ready for distribution

---

## 8. Testing Strategy

### 8.1 Unit Tests

**Test Coverage Goals:**
- Experiments: 90%
- Communication: 85%
- Data Management: 90%
- Configuration: 80%
- GUI: 60% (focus on logic, not widgets)

**Example Test Structure:**

```python
# tests/test_experiments.py

import pytest
from experiments.cyclic_voltammetry import CVExperiment
from experiments.parameters import CVParameters

class TestCVExperiment:

    @pytest.fixture
    def valid_params(self):
        return CVParameters(
            start_voltage=-0.5,
            end_voltage=0.5,
            scan_rate=0.1,
            cycles=2
        )

    def test_validation_success(self, valid_params):
        exp = CVExperiment(valid_params)
        assert exp.validate() == True

    def test_validation_failure_same_voltages(self):
        with pytest.raises(ValueError):
            CVParameters(
                start_voltage=0.5,
                end_voltage=0.5,  # Same as start
                scan_rate=0.1,
                cycles=2
            )

    def test_command_generation(self, valid_params):
        exp = CVExperiment(valid_params)
        commands = exp.generate_commands()
        assert "START:-0.5:0.5:0.1:2" in commands

    def test_voltage_calculation(self, valid_params):
        exp = CVExperiment(valid_params)
        # At t=0, should be at start_voltage
        v = exp._calculate_voltage_at_time(0)
        assert abs(v - (-0.5)) < 0.01
```

### 8.2 Integration Tests

**Test Scenarios:**

1. **Full CV Workflow**
   - Connect to mock hardware
   - Configure CV parameters
   - Start experiment
   - Receive data stream
   - Complete experiment
   - Export data
   - Verify data integrity

2. **Error Recovery**
   - Disconnect during experiment
   - Invalid command response
   - Corrupted data
   - ADC read failure

3. **Performance Tests**
   - 10,000 point dataset plotting
   - Rapid start/stop cycles
   - Memory usage over time
   - CPU usage during acquisition

### 8.3 Hardware Validation Tests

**Using Prototype v03:**

1. **CV Test Protocol**
   - Standard ferricyanide solution (1mM)
   - Expected peak separation: ~60mV
   - Compare with commercial potentiostat

2. **Current Accuracy**
   - Known resistor test circuit
   - Verify 10kΩ mode: ±500µA range
   - Verify 1MΩ mode: ±100nA range

3. **Voltage Accuracy**
   - Measure DAC output with multimeter
   - Compare commanded vs actual
   - Test full range: -1.5V to +1.5V

---

## Appendix A: Migration from v0

**Key Changes for Users:**

| Feature | v0 GUI | v1 GUI |
|---------|--------|--------|
| Framework | PyQt5 (monolithic) | PyQt5 (modular) |
| Experiments | CV only | CV, LSV, CA (extensible) |
| Data Export | CSV only | CSV, JSON, HDF5 |
| Configuration | Manual entry | Persistent config |
| Calibration | Manual offset | Calibration wizard |
| Plotting | pyqtgraph | pyqtgraph (optimized) |

**File Compatibility:**
- v1 can read v0 CSV exports
- v1 exports include more metadata
- Parameter files not compatible (different format)

---

## Appendix B: Future Enhancements (v2+)

**Planned Features:**

1. **Advanced Techniques**
   - Square Wave Voltammetry (SWV)
   - Differential Pulse Voltammetry (DPV)
   - AC Voltammetry (ACV)
   - Electrochemical Impedance Spectroscopy (EIS)

2. **Data Analysis**
   - Peak detection
   - Baseline correction
   - Integration
   - Kinetic parameter extraction

3. **Method Builder**
   - Chain multiple experiments
   - Conditional logic
   - Automated sequences

4. **Remote Control**
   - REST API
   - Python scripting interface
   - Batch processing

5. **Database Integration**
   - SQLite local database
   - Experiment history
   - Sample tracking
   - Search and filter

---

**Document End**

*This architecture is designed to be actionable, extensible, and maintainable. Start with Phase 1 and build incrementally, validating each component before proceeding to the next.*
