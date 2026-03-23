# Body Diode Clamping Issue — TS5A3160 Analog Switch

**Date:** 2026-03-13
**Status:** Workaround applied (voltage range limited); hardware fix pending
**Affects:** All voltammetric techniques (CV, LSV, DPV, SWV, NPV, CA)

---

## 1. Symptom

When the applied voltage (VRAMP) goes below approximately **-0.25 V**, a large spurious cathodic current appears in the measurement. At VRAMP = -0.5 V the reported current reaches **-160 µA** — even in air with no electrochemical cell connected.

The error grows **exponentially** with increasingly negative VRAMP, following the Shockley diode equation (n ≈ 1, ~26 mV per decade), confirming a semiconductor junction origin.

| VRAMP (V) | Expected Current (air) | Measured Current | Notes |
|-----------|:----------------------:|:----------------:|-------|
| 0.00 | ~0 µA | +0.3 µA | Normal baseline leakage |
| -0.20 | ~0 µA | -0.5 µA | Still acceptable |
| -0.25 | ~0 µA | -0.7 µA | Onset of exponential growth |
| -0.30 | ~0 µA | **-3.4 µA** | Body diode conducting |
| -0.35 | ~0 µA | **-20 µA** | Strong conduction |
| -0.40 | ~0 µA | **-103 µA** | Approaching ADC saturation |
| -0.42 | ~0 µA | **-168 µA** | ADC saturated (code 32767) |

## 2. Root Cause

### Signal chain overview

```
DAC (AD5761) → VRAMP
  ↓
TIA (LMC6484, U2) — inverting summing amplifier
  (+) = GND (0 V)
  (-) = WE + VRAMP coupled through matched 10 kΩ resistor
  Feedback = selectable via TS5A3160 analog switch (R = 10 kΩ or 1 MΩ)
  ↓
V_tia = VRAMP + I_cell × R_feedback   (at zero cell current: V_tia = VRAMP)
  ↓
Level shift (LMC6484, U2.3) — inverting amplifier, VREF1.0 at (+)
  V_out = 2 × 1.0 − V_tia = 2.0 − VRAMP − I_cell × R_feedback
  ↓
ADC (ADS1115, single-ended, PGA ±4.096 V, VDD = 3.3 V)
```

### The TIA output goes negative

At zero cell current, the TIA output voltage equals VRAMP:

- VRAMP = +0.5 V → V_tia = +0.5 V (positive, no issue)
- VRAMP = 0.0 V → V_tia = 0.0 V (at GND, borderline)
- VRAMP = -0.5 V → V_tia = **-0.5 V** (negative!)

### TS5A3160 body diode clamps the negative signal

The TS5A3160 analog switch (U5/U6) sits in the TIA feedback path to select between 10 kΩ and 1 MΩ gain resistors. It is powered by single supply (+5 V / GND). Its signal pins have internal body diodes that clamp to the supply rails:

```
         TS5A3160 signal pin
              │
     ┌────────┤
     │  Body  │
     ▼ diode  │
    GND       │
              │
    VDD ──────┘
     ▲  Body
     │  diode
     └────────
```

When V_tia drops below **~-0.3 V** (one diode drop below GND), the body diode from the signal pin to GND forward-biases. This injects exponentially increasing current into the TIA feedback network:

```
I_diode ∝ I_s × exp((|V_tia| − 0.3) / (n × V_t))
```

where V_t ≈ 26 mV at room temperature, n ≈ 1.

This parasitic current is indistinguishable from real cell current — the TIA faithfully converts it into a voltage change at its output, which propagates through the level-shift stage to the ADC.

### Secondary effect: ADS1115 input clamping

At VRAMP ≈ -0.40 V, the level-shifted output V_out reaches ~3.4 V, approaching the ADS1115 VDD (3.3 V). Above VDD + 0.3 V = 3.6 V, the ADS1115's own input protection diodes also conduct, further distorting the reading. At VRAMP ≈ -0.42 V the ADC reports its maximum code (32767), corresponding to 4.096 V full-scale.

## 3. Current Workaround (Software)

All experiment parameter definitions have been updated to limit the minimum voltage to **-0.2 V**, keeping VRAMP in the safe region where the body diode current is negligible (< 1 µA).

**Files changed:**

| File | Parameters limited |
|------|-------------------|
| `cyclic_voltammetry.py` | initial_voltage, high_voltage, low_voltage |
| `linear_sweep.py` | start_voltage, end_voltage |
| `chronoamperometry.py` | potential |
| `differential_pulse.py` | start_voltage, end_voltage |
| `square_wave.py` | start_voltage, end_voltage |
| `normal_pulse.py` | baseline_potential, start_voltage, end_voltage |

**Usable voltage range: -0.2 V to +1.5 V** (previously -1.5 V to +1.5 V)

## 4. Potential Hardware Fixes

### Option A: Replace analog switch

Use a switch that supports bipolar supply or has lower body-diode leakage for negative signals:

- **ADG1419** (Analog Devices): ±5 V supply capable, eliminates body diode issue
- **ADG1436**: dual SPST, ±5.5 V supply
- **TMUX1119** (TI): ±5.5 V supply, pin-compatible consideration needed

The -5 V rail from the ICL7660 charge pump is already available on the SaxStat PCB.

### Option B: Add level shift before the switch

Insert a fixed offset so the TIA output is always positive before entering the analog switch. For example, bias the TIA non-inverting input at +1.5 V instead of GND. This shifts V_tia to:

```
V_tia = 1.5 + VRAMP + I_cell × R_feedback
```

At VRAMP = -1.5 V (worst case): V_tia = 0 V (just at GND, no body diode).

**Trade-off:** This changes the level-shift formula and reduces the ADC dynamic range for current measurement (the baseline voltage is higher, leaving less headroom before the ADS1115 VDD clamp).

### Option C: Bypass the analog switch

Use fixed TIA feedback resistor(s) without the analog switch. This sacrifices gain switching but eliminates the body diode entirely.

### Option D: Software calibration (future)

Characterize the body diode I-V curve using an air test, then subtract the parasitic current from real measurements in software. This could extend the usable range to approximately -0.4 V without hardware changes, at the cost of accuracy.

## 5. Related Components

| Component | Part Number | Role |
|-----------|------------|------|
| U5 | TS5A3160DBVR | Analog switch — TIA gain select (GAIN1) |
| U6 | TS5A3160DBVR | Analog switch — TIA gain select (GAIN2) |
| U2 | LMC6484AIMX/NOPB | Quad op-amp (TIA, control amp, level shift) |
| U3 | AD5761RBRUZ | DAC (VRAMP output, ±3 V range) |
| U4 | ADS1115IDGSR | ADC (V_out measurement, VDD = 3.3 V) |
| U7 | ICL7660AIBAZA-T | Charge pump (-5 V supply, available for bipolar switch) |
| U9 | ADR510ARTZ | 1.0 V voltage reference (VREF1.0) |

## 6. References

- SaxStat schematic: `hardware/schematics/250804 SaxStat_v0.0.pdf`
- SweepStat reference circuit: `../../2025_Old/2025_Old/Ref/SweepStat/SweepStat circuit.pdf`
- TS5A3160 datasheet: absolute maximum rating, signal pin voltage = GND − 0.3 V to VDD + 0.3 V
- ADS1115 datasheet: analog input absolute max = VDD + 0.3 V
- Test data (air, CV -0.5 V): `C:\Users\Lenovo\Documents\SaxStat\Data\Cyclic Voltammetry_2026-03-13_15-06-12.csv`
