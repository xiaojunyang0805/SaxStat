# SaxStat Project Folder Structure

**Date:** 2025-10-12

This document describes the reorganized folder structure for the SaxStat project.

## Public Folders (Will be on GitHub)

### `/hardware` - Hardware Design Files
```
hardware/
├── schematics/           # PCB schematics (PDF and EasyEDA project)
├── bom/                  # Bill of Materials
├── 3d_models/           # 3D models (STEP files)
└── gerbers_private/     # PRIVATE - Manufacturing files (Gerbers, P&P)
```

**Public contents:**
- ✓ Schematic PDFs
- ✓ EasyEDA project files
- ✓ Bill of Materials (BOM)
- ✓ 3D models

**Private contents (excluded from GitHub):**
- ✗ Gerber files
- ✗ Pick and Place files

### `/firmware` - ESP32 Firmware Code
```
firmware/
├── prototype_v01/       # Firmware for prototype v01
├── prototype_v02/       # Firmware for prototype v02
└── prototype_v03/       # Firmware for prototype v03 (current)
```

### `/software` - GUI Application
```
software/
├── saxstat_gui/         # Main GUI application (PyQt5)
├── experiments/         # Experiment modules (CV, LSV, CA, etc.)
└── utils/              # Utility functions
```

### `/docs` - Documentation
```
docs/
├── hardware/           # Hardware documentation
├── software/           # Software/API documentation
├── user_guide/         # User manuals and guides
└── datasheets/         # Component datasheets
```

### `/examples` - Example Data
```
examples/
└── test_data/          # Sample electrochemical test data
```

## Private Folders (Excluded from GitHub)

### `/SaxStat_private docs` - Private Documentation
Contains:
- Business documentation
- Engineering notes
- Reference materials (including DStat and other references)
- EC potentiostat references

### `/hardware/gerbers_private` - Manufacturing Files
Contains:
- Gerber files for PCB fabrication
- Pick and Place files for SMT assembly

## Old Folders (To be archived/removed after verification)

These folders contain the original unorganized files:
- `3D model/` → Moved to `hardware/3d_models/`
- `EasyEDA_file/` → Moved to `hardware/schematics/` and `hardware/bom/`
- `JLC parts/` → Moved to `docs/datasheets/`
- `Prototype_v01/` → Firmware moved to `firmware/prototype_v01/`
- `prototype_v02/` → Firmware moved to `firmware/prototype_v02/`
- `prototype_v03/` → Firmware and GUI moved
- `Electrochemical Test/` → Moved to `examples/test_data/`

**Note:** After verifying the new structure works correctly, these old folders can be deleted.

## `.gitignore` Configuration

The following will be excluded from GitHub:
```
# Private documentation
SaxStat_private docs/
*_private*/

# Private hardware files
hardware/gerbers_private/

# Python
__pycache__/
*.pyc
*.pyo
.venv/
venv/
build/
dist/
*.spec
*.egg-info/

# IDE
.idea/
.vscode/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Temporary
*.tmp
*.bak
~$*
```

## Quick Navigation

**Current working GUI:** `software/saxstat_gui/SaxStat_GUI_V03.py`
**Current firmware:** `firmware/prototype_v03/SaxStat_V03_GUI_Test/`
**Test data:** `examples/test_data/`
**Work plan:** `WORK_PLAN.md`

## File Counts

- Hardware schematics: 2 files
- Hardware BOM: 1 file
- 3D models: 2 files
- Firmware versions: 3 prototypes
- Test data sets: 2 folders
- Datasheets: Multiple component datasheets organized by part

---

**Last Updated:** 2025-10-12
