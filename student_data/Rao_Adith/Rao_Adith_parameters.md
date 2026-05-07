# Battery Design Parameters — Rao, Adith
## Module 7: Battery Design Optimization
Generated: 2026-05-06 21:52

---

## Your Electrode Materials

You have been assigned the following four electrode materials.
Any of the four can act as the anode or cathode in a given cell.
You will evaluate all 12 possible ordered pairs.

### Sodium  (Na)
**Standard reduction half-reaction:** Na⁺(aq) + e⁻ → Na(s)
**E° = -2.71 V**

### Gold  (Au)
**Standard reduction half-reaction:** Au³⁺(aq) + 3e⁻ → Au(s)
**E° = +1.50 V**

### Copper  (Cu)
**Standard reduction half-reaction:** Cu²⁺(aq) + 2e⁻ → Cu(s)
**E° = +0.34 V**

### Iron  (Fe)
**Standard reduction half-reaction:** Fe²⁺(aq) + 2e⁻ → Fe(s)
**E° = -0.44 V**

---

## Molecular Weights

This table is the most important reference for your active mass calculations.
Read the **Which MW to use** column carefully — using the wrong value
is the single most common source of error on this assignment.

> **Rule:**
> - Material acting as the **ANODE** (oxidised, solid metal consumed)
>   → use the **Elemental MW**.
> - Material acting as the **CATHODE** (reduced, ionic species from solution)
>   → use the **Compound MW**.
>
> *Why the difference?* At the anode you are literally dissolving a pure metal
> electrode — the mass that gets used up is just the metal atoms. At the cathode,
> the ionic species you are reducing must come from a dissolved salt; the full
> formula weight of that salt represents the cathode material.

| Material | Symbol | Half-reaction (reduction) | E° (V) | Elemental MW (g/mol) | Use when ANODE | Compound formula | Compound MW (g/mol) | Use when CATHODE |
|----------|--------|--------------------------|--------|---------------------|----------------|-----------------|---------------------|-----------------|
| Sodium | Na | Na⁺(aq) + e⁻ → Na(s) | -2.71 | **22.990** | Na metal, elemental | NaCl | **58.443** | Na⁺ sourced from NaCl solution |
| Gold | Au | Au³⁺(aq) + 3e⁻ → Au(s) | +1.50 | **196.967** | Au metal, elemental | AuCl₃ | **303.325** | Au³⁺ sourced from AuCl₃ solution |
| Copper | Cu | Cu²⁺(aq) + 2e⁻ → Cu(s) | +0.34 | **63.546** | Cu metal, elemental | CuSO₄ | **159.609** | Cu²⁺ sourced from CuSO₄ solution |
| Iron | Fe | Fe²⁺(aq) + 2e⁻ → Fe(s) | -0.44 | **55.845** | Fe metal, elemental | FeSO₄ | **151.908** | Fe²⁺ sourced from FeSO₄ solution |

### Worked example using your materials

Suppose you pair **Sodium (anode)** with **Gold (cathode)**.
The balanced equation transfers n = 3 electron(s) per formula unit.
Stoichiometric coefficients: 3 × anode, 1 × cathode.

```
Active mass = (3 × 22.990 g/mol  [elemental, anode])
            + (1 × 303.325 g/mol  [compound, cathode])
           = 372.295 g/mol
           = 0.372295 kg/mol   ← divide by 1000 before plugging in

Capacity = (n × 96,485 × 1,000) / (3,600 × mass_kg)
         = (3 × 96,485 × 1,000) / (3,600 × 0.372295)
         = 215,969 mAh/kg
```

> ⚠️  **Units reminder:** the mass in the denominator must be in **kilograms**.
> Passing grams gives mAh/g (1000× too small), causing battery mass estimates
> to come out 1000× too heavy. Always divide your g/mol value by 1000 first.

---

## Application Requirements

These are fixed for all students.

| Application | Min. voltage (V) | Current (mA) | Runtime (h) | Capacity required (mAh) | Optimisation goal |
|-------------|-----------------|--------------|-------------|------------------------|-------------------|
| Medical Pacemaker | 2.8 | 0.01 | 87,600 | 876.0 | Minimum active material mass |
| LED Flashlight | 1.5 | 400.0 | 2.0 | 800.0 | Maximum specific capacity (mAh/kg) |
| IoT Sensor / Coin Cell | 3.0 | 0.1 | 8,760 | 876.0 | Minimum mass and volume |

### Application context
**Medical Pacemaker:** Implanted device — battery replacement requires surgery. Current draw is extremely low (10 μA); must last 10 years reliably.

**LED Flashlight:** Disposable, cost-sensitive battery. High current draw. Longest runtime per kg of active material is the goal.

**IoT Sensor / Coin Cell:** Wireless sensor node (e.g. Arduino with BLE). Spends most time in deep sleep (2–5 μA) and wakes briefly every minute to transmit (8–15 mA burst) — 100 μA is the effective average. Must run 1 year in a CR2032-sized package. Device stops working when V_terminal < 3.0 V.

---

## Series and Parallel Configuration

If your best cell does not meet the voltage requirement alone:

```
N_series = ceil(V_target / E°_cell)      # cells wired in series

V_pack   = N_series × E°_cell            # voltage adds
C_pack   = C_cell  (unchanged)           # capacity stays the same
mass_total = N_series × mass_per_cell    # mass multiplies
```

For parallel connections (increasing capacity, not voltage):

```
V_pack   = V_cell  (unchanged)
C_pack   = N_parallel × C_cell
mass_total = N_parallel × mass_per_cell
```

---

## Part 3: Discharge Simulation Parameters

Use these values when setting up `battery_discharge.py` or `battery_discharge.m`.

| Parameter | Value | Notes |
|-----------|-------|-------|
| Suggested R_int | **20.0 Ω** | Adjust if your cell resembles a different type |
| V_device_threshold | See application | Pacemaker: 2.5 V; Coin cell: 3.0 V; Flashlight: 1.2 V |
| C_ox_0 | 1.00 mol/L | Starting cathode ion concentration |
| C_red_0 | 0.001 mol/L | Starting anode ion concentration (non-zero to avoid ln(0)) |
| V_soln | 1 × 10⁻⁴ L | Model cell for curve shape; see script for scaling to Part 2 mass |

Choose the cell you select for your **IoT coin cell** application for the
simulation. Run at three currents: your design current (0.10 mA),
a moderate overload (1.0 mA), and a burst (10 mA).
The burst case should illustrate what happens when V_terminal drops below 3.0 V
before significant discharge occurs — the device shuts off while energy remains in the cell.

---

## Key Formulas Reference

```
Cell voltage:
  E°_cell = E°_cathode − E°_anode

Active mass per mole of reaction:
  total_mass_g  = (anode_coeff × element_MW_g) + (cathode_coeff × compound_MW_g)
  total_mass_kg = total_mass_g / 1000                ← MUST divide by 1000

Specific capacity:
  Capacity (mAh/kg) = (n × 96,485 × 1,000) / (3,600 × total_mass_kg)

Energy density:
  Energy Density (Wh/kg) = E°_cell × Capacity (mAh/kg) / 1,000

Capacity required for application:
  Capacity_req (mAh) = Current (mA) × Runtime (h)

Series cells needed:
  N_series = ceil(V_target / E°_cell)

Active mass needed:
  Mass (kg) = N_series × Capacity_req (mAh) / Capacity (mAh/kg)
  Mass (g)  = Mass (kg) × 1000          ← sanity check: pacemaker ≈ 1–5 g

Nernst equation (Part 3):
  E_cell = E°_cell − (0.02569 / n) × ln(Q)   [at 25°C]
  Q = [anode product ions] / [cathode reactant ions]
  V_terminal = E_cell − I_A × R_int
```
