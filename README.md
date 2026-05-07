# Battery Design Optimization
## CHEM 233 — Final Module: Electrochemistry and Engineering Applications

---

## Overview

In this module you will design battery systems for three real engineering applications, working from first principles of electrochemistry through to a computational model of real discharge behavior. Along the way you will discover why battery engineering is fundamentally about trade-offs — and why the right battery for a pacemaker is completely wrong for a flashlight.

**Motivating questions:**

> *Why is a 1.5 V D-cell physically larger than a 9 V battery, even though the 9 V battery has six times the voltage?*

> *A fresh battery reads 1.5 V on a voltmeter. An hour later, under load, it reads 1.1 V. The chemistry hasn't changed — so why has the voltage dropped?*

Both questions have precise, quantitative answers rooted in the electrochemistry you already know. This module builds the tools to answer them.

**Computation:** Python or MATLAB are the expected tools for this module. Excel can work for Parts 1 and 2 if you prefer, but you will need to figure out the implementation yourself. Part 3 (the discharge simulation) requires a programming environment — there is no practical spreadsheet equivalent for numerical integration.

---

## Learning Objectives

By completing this module you will:

1. Systematically evaluate all possible electrode combinations and classify them as galvanic or electrolytic
2. Calculate theoretical specific capacity and energy density using Faraday's law, with correct unit handling
3. Explain why cells must sometimes be connected in series or parallel to meet both voltage and capacity requirements simultaneously
4. Apply the Nernst equation to model how cell voltage changes as reactants are consumed during discharge
5. Numerically integrate a voltage–time curve and extract usable capacity from it
6. Construct a Ragone plot and use it to compare battery chemistries across applications
7. Translate electrochemical calculations into quantitative design recommendations for specific engineering applications

---

## The Engineering Context

### Three Applications

Before any formulas, it is worth understanding concretely what you are designing for. The three applications in this module represent very different engineering constraints, and those differences will drive every cell-selection decision you make.

**Medical pacemaker.** A pacemaker is implanted in a patient's chest and delivers precisely timed electrical pulses to keep the heart beating. The battery must last at least 10 years without replacement — replacing it requires surgery with real clinical risk. The device draws only about 10 μA of average current (a small LED draws 50× more), but it must never fail. **The overriding design constraint is longevity and reliability, not size or cost.** Minimum active electrode mass is the optimization target, because mass directly determines how many moles of reactant are available to sustain the reaction.

Real pacemaker batteries (lithium/iodine chemistry, developed in the 1970s) weigh about 25–30 g total and last 8–12 years. Your calculations will tell you how many grams of *active material* are theoretically needed — the rest is packaging, electrolyte, and safety margins.

**LED flashlight.** A flashlight draws roughly 400 mA — 40,000 times more current than a pacemaker. It needs to run for 2 hours. You could use an expensive, high-energy-density cell, but a flashlight battery is disposable and cost-sensitive; what matters is **how much charge you can deliver per kilogram of active material**. High specific capacity (mAh/kg) is the figure of merit, not energy density (Wh/kg), because the voltage is essentially set by the chemistry — you want the cell that stores the most charge, and therefore lasts the longest, per unit of material cost.

**Coin cell for an IoT sensor node.** A CR2032-style coin cell is the power source for countless small embedded systems: keyless entry fobs, cardiac monitors, environmental sensors, wireless Arduino nodes. The voltage requirement (≥ 3.0 V) rules out single alkaline cells and requires either a lithium chemistry or cells in series. The current is low — about 0.10 mA average, representing a microcontroller that spends most of its time in deep sleep and wakes briefly to take a measurement and transmit — but the device must run for a full year unattended. **The constraint is fitting adequate energy into a very small, light package.** For an EE student: this is the application where Ragone plot position matters most, because the device's form factor is set before the battery is chosen.

| Application | Target voltage | Current | Runtime | Key constraint |
|-------------|---------------|---------|---------|----------------|
| Medical pacemaker | ≥ 2.8 V | 10 μA (0.010 mA) | 10 years (87,600 h) | Minimum mass |
| LED flashlight | ≥ 1.5 V | 400 mA | 2 hours | Maximum capacity |
| IoT sensor / coin cell | ≥ 3.0 V | 0.10 mA | 1 year (8,760 h) | Minimum mass/volume |

---

### Cells, Series, and Parallel

A single electrochemical cell delivers a fixed voltage set by its chemistry — you cannot change this by modifying the physical size of the electrodes. What size *does* change is capacity: a larger electrode contains more moles of reactant, which means more charge available before depletion. This leads to two distinct design levers when a single cell is insufficient.

**Series connections — when you need more voltage.**

Connecting N identical cells in series adds their voltages while keeping the capacity the same:

```
V_series   = N × V_cell          (voltage adds)
C_series   = C_cell              (capacity unchanged)
mass_total = N × mass_cell
```

This makes intuitive sense: the same current flows through each cell in turn, so each cell delivers exactly its design capacity before the chain is exhausted. You have not gained any extra energy — you have traded lower current × higher voltage for the same total power. The 9 V battery is a classic example: it contains six 1.5 V alkaline cells in series. Six cells, six times the voltage, same capacity per cell — which is why a 9 V battery has *less* total energy storage than a single D-cell, even though its voltage is six times higher.

**Parallel connections — when you need more capacity.**

Connecting N identical cells in parallel adds their capacities while keeping the voltage the same:

```
V_parallel = V_cell              (voltage unchanged)
C_parallel = N × C_cell         (capacity adds)
mass_total = N × mass_cell
```

The current demand splits equally across the cells, so each cell is discharged more slowly. This extends runtime without changing the voltage a load sees.

**Series-parallel combinations — when you need both.**

A practical battery pack often needs to meet both a minimum voltage *and* a minimum capacity. The solution is an M-series, N-parallel configuration (written M×N or MsNp):

```
V_pack   = M × V_cell
C_pack   = N × C_cell
mass_pack = M × N × mass_cell
```

**Worked example:** Suppose your best available cell produces 1.5 V and has a specific capacity of 200,000 mAh/kg. A given application needs ≥ 3.0 V and ≥ 400 mAh total from 2.0 g of active material.

- Single cell mass for 400 mAh: (400 mAh) / (200,000 mAh/kg) = 2.0 × 10⁻³ kg = 2.0 g
- 1 cell: 1.5 V, 400 mAh, 2.0 g ✗ (voltage too low)
- 2 in series (2S1P): 3.0 V, 400 mAh, 4.0 g ✓ (meets voltage, meets capacity, doubles mass)
- 4 in series-parallel (2S2P): 3.0 V, 800 mAh, 8.0 g ✓ (meets voltage, doubles capacity, 4× mass)

The choice between 2S1P and 2S2P depends on whether 400 mAh is sufficient or whether you need the extra runtime that 800 mAh provides. **Note that specific capacity and energy density are properties of the chemistry — they do not change with configuration. Only total mass and total capacity change.**

---

## Conceptual Foundation

### Electrochemical Cells and Standard Potential

A galvanic cell converts chemical energy to electrical energy via a spontaneous redox reaction. Each half-reaction has a standard reduction potential E° measured against the standard hydrogen electrode. The cell voltage is:

```
E°_cell = E°_cathode − E°_anode
```

A positive E°_cell means the reaction is spontaneous — the cell can do work on an external circuit. A negative value means the reaction requires energy input (electrolytic). Only cells with E°_cell > 0 are useful as batteries.

### Faraday's Law and Specific Capacity

Every mole of electrons that flows through the external circuit corresponds to 96,485 Coulombs (Faraday's constant, F). For a reaction that transfers n electrons per formula unit, each mole of active material provides n × 96,485 C. Converting to the practical unit of battery capacity (milliamp-hours):

```
1 Ah = 3,600 C     →     1 mAh = 3.6 C
```

Specific capacity normalizes by active mass, giving mAh per kilogram of electrode material:

```
Capacity (mAh/kg) = (n × 96,485 × 1,000) / (3,600 × total_mass_kg)
```

where `total_mass_kg` is the combined mass of anode and cathode reactants *per mole of reaction* (see Mass Calculation in Investigation 1).

> **Unit note.** A common error is to pass mass in grams and label the result as mAh/kg — this gives a value that is 1,000× too small, which then causes mass estimates to come out 1,000× too large. Always convert mass to kilograms before plugging in, or multiply the numerator by 1,000,000 instead of 1,000. See Common Mistakes for details.

Multiplying specific capacity by cell voltage gives specific energy (energy per kilogram):

```
Energy Density (Wh/kg) = E°_cell × Capacity (mAh/kg) / 1,000
```

### The Nernst Equation (preview for Part 3)

E°_cell is the standard potential — valid only when all dissolved species are at exactly 1 mol/L and all gases at 1 atm. In a real discharging battery, reactant concentrations fall and product concentrations rise as the reaction proceeds. The Nernst equation corrects for this:

$$E_{cell} = E°_{cell} - \frac{RT}{nF} \ln Q$$

where R = 8.314 J/(mol·K), T is temperature in Kelvin, and Q is the reaction quotient (same form as the equilibrium expression, but evaluated at the instantaneous concentrations rather than at equilibrium). As a cell discharges, Q grows, ln(Q) grows, and E_cell falls — this is exactly why battery voltage drops under load. Part 3 asks you to model this process quantitatively.

---

## Your Parameter Set

Each student is assigned a set of four electrode materials with their standard reduction potentials. Your parameter packet lists these.

**Fixed conditions (same for all students):**

| Parameter | Value |
|-----------|-------|
| Faraday constant F | 96,485 C/mol |
| Gas constant R | 8.314 J/(mol·K) |
| Temperature | 298.15 K (25°C) |
| Anode mass convention | Elemental molecular weight |
| Cathode mass convention | Compound (salt) molecular weight |
| Nernst simulation: initial cathode ion concentration | 1.00 mol/L |
| Nernst simulation: initial anode ion concentration | 0.001 mol/L |
| Nernst simulation: electrolyte volume | 50 mL (0.050 L) |
| Nernst simulation: cutoff voltage | 0.70 × E°_cell |

---

## Analysis Workflow

### Investigation 1: Which electrode pairs produce viable cells, and what are their theoretical performance limits?

**Why this comes first.** Before you can select a cell for any application, you need to know which of your assigned electrode pairs even produce spontaneous (galvanic) cells, and among those, how they compare on the two fundamental performance metrics: specific capacity and energy density. The chemistry sets hard limits on both — no amount of engineering can push a cell's energy density above its theoretical maximum. This investigation establishes that map.

**What you will find.** With four electrode materials, you have 4 × 3 = 12 ordered electrode pair combinations (each material as anode paired with each of the other three as cathode, and vice versa). Exactly half of these will be the same reaction run backwards — one will be galvanic, the other electrolytic. The cells with highest E°_cell will not necessarily have the highest specific capacity or energy density, because those also depend on molecular weight. You will discover that the chemistry with the best voltage and the chemistry with the best capacity are almost certainly different cells — and that tension is what makes battery selection non-trivial.

---

#### Step 1: Cell voltages for all combinations

For each of the 12 ordered electrode pairs, calculate:

```
E°_cell = E°_cathode − E°_anode
```

Classify as **Galvanic** (E°_cell > 0) or **Electrolytic** (E°_cell < 0). Record all 12 in Table 1. Only galvanic cells proceed to the capacity calculation.

---

#### Step 2: Active mass per mole of reaction

Use the mixed molecular weight convention: the anode material contributes its elemental molecular weight (you are consuming pure metal), while the cathode contributes the compound molecular weight of its ionic form in solution (what gets reduced). Balance the half-reactions first to get stoichiometric coefficients, then:

```
total_mass_g/mol = (anode_coefficient × element_MW) + (cathode_coefficient × compound_MW)
total_mass_kg    = total_mass_g / 1000
```

Use the LCM of the electron counts in each half-reaction to find `n` (total electrons transferred per balanced equation).

---

#### Step 3: Specific capacity and energy density

```
Capacity (mAh/kg) = (n × 96,485 × 1,000) / (3,600 × total_mass_kg)

Energy Density (Wh/kg) = E°_cell × Capacity (mAh/kg) / 1,000
```

Record these for each galvanic cell in Table 1, along with the balanced overall equation.

**Sanity check:** Specific capacities for simple metal/salt cells typically fall in the range of 100,000 – 400,000 mAh/kg theoretical. If your values are in the hundreds of mAh/kg, you have a units error (see Common Mistakes).

---

### Investigation 2: How do application requirements constrain cell selection and pack configuration?

**Why this comes second.** Knowing the theoretical performance of each cell is necessary but not sufficient. Each application imposes a minimum voltage, a current demand, and a runtime — and these requirements interact in ways that aren't always obvious. A cell with excellent specific capacity may still be the wrong choice if it cannot meet the voltage requirement without a series stack that doubles the mass. This investigation builds the quantitative framework for making those trade-offs explicit.

**What you will find.** The three applications span eight orders of magnitude in current (10 μA to 400 mA) and require different voltages. Some of your galvanic cells will fail the voltage threshold for certain applications outright; others will require series stacking. The optimal cell for the pacemaker and the optimal cell for the flashlight will likely be different chemistries chosen on different grounds. The coin cell application, with its 3.0 V requirement and modest current, is the most likely to require a series configuration.

---

#### Step 4: Mass needed for each application

For each application, identify all galvanic cells that meet or can be stacked to meet the voltage requirement. Then calculate:

**Number of cells in series needed:**
```
N_series = ceil(V_target / E°_cell)     [round up to nearest integer]
```

**Active mass needed per the application's energy demand:**
```
Capacity_required (mAh) = Current (mA) × Runtime (h)
Mass_needed (kg) = Capacity_required / Capacity (mAh/kg)
```

**Total active mass including series stacking:**
```
Total_mass (kg) = N_series × Mass_needed (kg)
```

Because the series cells carry the same charge (same current through each), stacking in series multiplies both voltage and mass by N_series, but leaves specific capacity and energy density unchanged. The extra mass is the price of meeting the voltage requirement.

**If parallel cells are also needed** (to meet a capacity target that exceeds what a single cell can provide in the required form factor), use:
```
Total_mass = N_series × N_parallel × mass_per_cell_kg
```
where N_parallel is the number of parallel branches.

**Application parameters:**

*Medical pacemaker:*
```
Current: 0.010 mA   Runtime: 87,600 h   Target voltage: ≥ 2.8 V
Capacity required: 0.010 × 87,600 = 876 mAh
```

*LED flashlight:*
```
Current: 400 mA     Runtime: 2 h        Target voltage: ≥ 1.5 V
Capacity required: 400 × 2 = 800 mAh
```

*IoT sensor / coin cell:*
```
Current: 0.10 mA    Runtime: 8,760 h    Target voltage: ≥ 3.0 V
Capacity required: 0.10 × 8,760 = 876 mAh
```
*Context for the coin cell current:* 0.10 mA (100 μA) represents a microcontroller that spends most of its time in deep sleep (drawing ~2–5 μA) and wakes for ~1 second every minute to read a sensor and transmit over Bluetooth Low Energy (drawing ~8–15 mA during the burst). The 100 μA average is a reasonable approximation for this duty cycle.

Record the optimal cell choice, required configuration, and total active mass for each application in Table 2.

---

#### Step 5: Ragone plot

A Ragone plot is the standard tool battery engineers use to compare chemistries and guide application-driven selection. It plots **specific energy (Wh/kg)** on the y-axis against **specific power (W/kg)** on the x-axis, both on logarithmic scales.

**Specific power** for a cell discharging at current I:
```
Specific Power (W/kg) = E°_cell (V) × I (mA) / total_mass (g)
```
(This works because [V × mA / g] = [V × 10⁻³ A / 10⁻³ kg] = [W/kg].)

For each of your galvanic cells, compute the specific power at each application's current draw. This gives you up to three points per cell on the Ragone plot (one per application).

Plot all your cells as labeled points. For reference, draw approximate shaded regions for:
- Lead-acid batteries: 30–50 Wh/kg, 75–300 W/kg
- Lithium-ion (commercial): 150–250 Wh/kg, 250–750 W/kg
- Supercapacitors: 5–15 Wh/kg, 1,000–10,000 W/kg

Where do your theoretical cells fall relative to these real-world benchmarks? The gap between your theoretical values and commercial Li-ion is a useful measure of how much efficiency is lost to packaging, electrolyte, separator, and current-collector mass in a real cell.

---

### Investigation 3: How does real discharge behavior depart from the theoretical ideal?

**Why this comes last.** Parts 1 and 2 assume that a cell delivers exactly E°_cell from start to finish. Real cells do not — voltage drops progressively as reactants are consumed, and the cell becomes "dead" at some cutoff voltage that is above zero. This means the **usable capacity is always less than the theoretical capacity**. The Nernst equation gives us the physical mechanism behind this drop, and numerical integration lets us model it quantitatively.

This is the question the original module raised in Note 3 and left open: *"How would you approach calculating the actual capacity of a battery given that voltages drop as the reactions approach equilibrium?"* Part 3 answers it with a working computational model.

**What you will find.** Even a relatively simple cell shows a measurable voltage drop over its discharge life. More importantly, cells behave very differently depending on the current draw: at high current (flashlight application), the reaction quotient Q advances rapidly and the voltage drops steeply, giving lower usable capacity. At low current (pacemaker application), Q advances slowly and the cell delivers nearly its theoretical capacity before reaching the cutoff voltage. This rate-dependent behavior — fundamentally rooted in the Nernst equation — is why it is not sufficient to characterize a battery by a single capacity number; the discharge rate always matters.

---

#### Step 6: Derive the Q expression for your chosen cell

Select one of your galvanic cells to model. A cell with both redox species as dissolved ions (rather than solids) works best for this simulation because concentrations appear explicitly in Q.

For a general cell:
```
Anode:   A(s) → A^n+(aq) + n e⁻
Cathode: B^n+(aq) + n e⁻ → B(s)
Overall: A(s) + B^n+(aq) → A^n+(aq) + B(s)
```

The reaction quotient, excluding pure solids (activity = 1):
```
Q = [A^n+] / [B^n+]
```

If your half-reactions have different electron counts and require stoichiometric coefficients, Q will have concentration terms raised to those powers. Write the correct Q for your chosen chemistry.

The Nernst equation:
```
E_cell = E°_cell − (R × T) / (n × F) × ln(Q)
       = E°_cell − (8.314 × 298.15) / (n × 96,485) × ln(Q)
       = E°_cell − (0.02569 / n) × ln(Q)     [at 25°C]
```

---

#### Step 7: Euler integration of the discharge curve

At constant discharge current I (Amperes), charge flows at exactly I Coulombs per second. By Faraday's law, this corresponds to a fixed rate of moles of reaction per second:

```
moles of reaction per second = I / (n × F)
```

In an electrolyte of volume V_soln (liters), this translates to concentration changes:

```
d[B^n+]/dt = − I / (n × F × V_soln)     [mol/L/s]   consumed at cathode
d[A^n+]/dt = + I / (n × F × V_soln)     [mol/L/s]   produced at anode
```

**The Euler loop** takes small time steps of size dt (seconds) and applies these rates repeatedly:

```
for each time step:
    1. compute E = E°_cell − (0.02569/n) × ln([A^n+] / [B^n+])   ← Nernst
    2. [B^n+] ← [B^n+] − (I / (n × F × V_soln)) × dt            ← update concentration
    3. [A^n+] ← [A^n+] + (I / (n × F × V_soln)) × dt
    4. record time, voltage, and concentrations
    5. stop if E < V_cutoff  or  [B^n+] ≤ 0
```

This is not an approximation — it is exact in the limit of small dt. A step size of dt = 10 seconds is more than adequate for the timescales involved.

**Scaffolded code is provided.** The Python and MATLAB templates give you the working Euler loop and plotting structure. Your tasks are:
1. Fill in the correct E°_cell, n, and Q expression for your chosen cell
2. Run the simulation at three current levels: pacemaker (0.010 mA), coin cell (0.10 mA), and flashlight (400 mA)
3. Overlay all three discharge curves on one plot
4. Use `np.trapezoid` (Python) or `trapz` (MATLAB) to compute the area under each V(t) curve — this gives the **usable energy in Wh**, from which you can extract usable capacity

---

#### Step 8: Compare usable capacity to theoretical capacity

**Usable capacity** from the simulation:
```
Usable_capacity (mAh) = area under V(t) curve (Wh) / E_avg (V) × 1000
```
where E_avg is the average voltage over the discharge.

Alternatively, since current is constant:
```
Usable_capacity (mAh) = I (mA) × t_discharge (h)
```

**Theoretical capacity** from Part 1 scaled to the same mass:
```
Theoretical_capacity (mAh) = Capacity (mAh/kg) × mass_of_active_material (kg)
```

The ratio (usable / theoretical) is called the **Coulombic efficiency** under this discharge condition. Report it for each of your three current levels and discuss the trend: does the efficiency improve or worsen at high current, and why?

**What this means for the device.** For the coin cell application, the minimum operating voltage of a 3.3 V microcontroller with a standard LDO regulator is typically 3.0–3.2 V. Once your cell drops below this threshold, the device shuts down even though chemical energy remains in the cell. Identify the point on your discharge curve where the voltage crosses this threshold — the charge delivered up to that point is the **actually usable capacity for this application**, which may be substantially less than either the theoretical or the Nernst-corrected value.

---

## Computation Tools

**Python (recommended):** Use `numpy` for all array operations and `matplotlib` for plotting. A scaffolded template (`battery_discharge.py`) is provided that handles the Euler loop and multi-curve plotting. You fill in the cell parameters and Q expression.

**MATLAB:** An equivalent `.m` script (`battery_discharge.m`) is provided. The structure mirrors the Python template.

**Excel:** Workable for Parts 1 and 2 (cell voltages, capacities, mass calculations, Table 1, Table 2). Not practical for Part 3 — the Euler loop requires hundreds of rows and does not lend itself to clean visualization. If you use Excel for Parts 1–2, you will need to switch to Python or MATLAB for Part 3.

---

## Visualization Requirements

### Required Plots

**Plot 1 — Discharge curves (Part 3)**
- Three curves on one set of axes: pacemaker current, coin cell current, flashlight current
- X-axis: Time (hours), Y-axis: Cell Voltage (V)
- Horizontal dashed line at the cutoff voltage
- Horizontal dotted line at E°_cell (standard potential, for reference)
- Legend identifying each curve by current (mA)
- Shaded region under each curve (or just the recommended cell) showing usable energy

**Plot 2 — Ragone plot (Part 2)**
- Log-log axes: X = Specific Power (W/kg), Y = Specific Energy (Wh/kg)
- Each galvanic cell plotted as a labeled point at each application's current
- Shaded reference regions for lead-acid, Li-ion, and supercapacitors
- Both axes labeled with units

### Visual requirements for all plots
- Descriptive title
- Both axes labeled with units, ≥ 12 pt font
- Legend present where multiple series appear
- Grid on
- Saved as PNG at ≥ 150 dpi

---

## What to Report

### Executive Summary
One paragraph. State: how many galvanic cells you found, which cell you recommend for each application, the total active mass required, and the key finding from your discharge simulation.

### Table 1: Complete Electrochemical Analysis

All 12 electrode combinations:

| Anode | Cathode | E°_cell (V) | Type | n | Active mass (g/mol) | Capacity (mAh/kg) | Energy density (Wh/kg) | Balanced equation |
|-------|---------|-------------|------|---|---------------------|-------------------|----------------------|-------------------|
| ... | ... | ... | G/E | | | | | |

Electrolytic cells: fill voltage and type only; leave capacity/energy blank.

### Table 2: Application Design

| Application | Cell chosen | E°_cell (V) | Series config | Parallel config | Capacity/cell (mAh/kg) | Mass required (g) |
|-------------|------------|-------------|--------------|----------------|----------------------|-------------------|
| Pacemaker | | | | | | |
| Flashlight | | | | | | |
| IoT coin cell | | | | | | |

Include a brief justification (1–2 sentences) for each cell selection below the table.

### Engineering Analysis

Write 1–2 paragraphs on each of the following:

**1. Why is the D-cell larger than the 9 V battery?**
Use your Table 1 and Table 2 numbers to make this argument quantitative, not just qualitative. Compare specific capacity and total energy stored.

**2. Voltage, capacity, and energy density: why you cannot maximize all three.**
Use your data to identify whether your highest-voltage cell is also your highest-capacity cell. If not, explain the trade-off in terms of the molecular weights and electron counts involved.

**3. Rate dependence and usable capacity.**
From your discharge simulation: how much usable capacity does your chosen flashlight cell deliver versus your chosen pacemaker cell, as a fraction of the theoretical maximum? Why does the ratio differ? What does this imply about how battery capacity ratings should always be interpreted alongside a discharge rate?

**4. The microcontroller voltage threshold.**
For your IoT coin cell application: at what time does your simulated cell voltage cross the 3.0 V device cutoff? What fraction of the total charge has been delivered at that point? Is the battery "dead" by a chemical criterion or an engineering criterion — and what is the distinction?

Cite any external sources you use.

### Discharge curve plot and Ragone plot
Both plots described above, with complete captions. A caption should state what is shown, which cell/chemistry is being modeled, and the key quantitative finding.

---

## Common Mistakes

### Unit error in the capacity formula (very common)

```
WRONG:  Capacity = (n × 96485 × 1000) / (3600 × mass_g)
        → gives mAh/g, not mAh/kg → values are 1000× too small
        → mass estimates come out 1000× too heavy (pacemakers at 3 kg!)

RIGHT:  Capacity = (n × 96485 × 1000) / (3600 × mass_kg)
        where mass_kg = mass_g / 1000
```

Sanity check: Li/MnO₂ theoretical capacity should come out near 285,000 mAh/kg. A pacemaker needing 876 mAh total should require about 3 g of active material, not 3 kg.

### Forgetting to account for series stacking in mass

If a voltage requirement forces N cells in series, the total active mass is N times the single-cell mass needed for capacity. Both factors multiply.

```
WRONG:  mass = capacity_required / capacity_per_kg   (ignores series cells)
RIGHT:  mass = N_series × (capacity_required / capacity_per_kg)
```

### Celsius instead of Kelvin in the Nernst equation

The Nernst equation requires absolute temperature. At 25°C, T = 298.15 K, not 25.

### Q includes only aqueous species

Pure solids and pure liquids have activity = 1 and do not appear in Q. Only dissolved ions and gases appear. If both products and reactants include a solid electrode, Q may reduce to a simple ratio of two ion concentrations.

### Cutoff voltage choice in the simulation

The simulation cutoff (0.70 × E°_cell) is a model parameter, not a physical constant. Real cutoff voltages depend on the device's minimum operating voltage, which is an engineering specification. For the microcontroller application specifically, the device cutoff is set by the regulator datasheet (typically 3.0–3.2 V for a 3.3 V system), not by any property of the battery chemistry.

---

## Grading

| Component | Points | Focus |
|-----------|--------|-------|
| Table 1: Electrochemical analysis | 25 | All 12 combinations, correct voltages, correct capacity/energy calculations for galvanic cells, balanced equations |
| Table 2: Application design | 20 | Correct series/parallel configuration, correct mass calculations, justified selection |
| Discharge simulation | 25 | Correct Q expression, working Euler loop, three-curve overlay plot, usable capacity extracted and compared to theoretical |
| Ragone plot | 10 | Correct specific power and energy, real-world benchmarks included, correctly interpreted |
| Engineering analysis | 15 | Quantitative arguments, rate dependence correctly explained, microcontroller threshold analysis |
| Report quality | 5 | Executive summary, complete captions, clear organization |
| **Total** | **100** | |

---

## Key Formulas Reference

```
Cell voltage:
  E°_cell = E°_cathode − E°_anode

Active mass per mole of reaction:
  total_mass_kg = (anode_coeff × element_MW + cathode_coeff × compound_MW) / 1000

Specific capacity:
  Capacity (mAh/kg) = (n × 96,485 × 1,000) / (3,600 × total_mass_kg)

Energy density:
  Energy Density (Wh/kg) = E°_cell × Capacity (mAh/kg) / 1,000

Capacity required for application:
  Capacity_req (mAh) = Current (mA) × Runtime (h)

Active mass needed (single cell, meeting capacity):
  Mass (kg) = Capacity_req (mAh) / Capacity (mAh/kg)

Series cells needed (meeting voltage):
  N_series = ceil(V_target / E°_cell)

Total mass with series stacking:
  Total_mass (kg) = N_series × Mass (kg)

Specific power on Ragone plot:
  P_specific (W/kg) = E°_cell (V) × I (mA) / total_mass (g)

Nernst equation:
  E_cell = E°_cell − (0.02569 / n) × ln(Q)     [at 25°C]

Concentration change rate (Euler integration):
  d[cathode ion]/dt = − I_A / (n × F × V_soln)   [mol/L/s]
  d[anode ion]/dt   = + I_A / (n × F × V_soln)   [mol/L/s]

Usable capacity from simulation:
  Usable_capacity (mAh) = I (mA) × t_discharge (h)
```

---

## Expected Insights

By the end of this module you should be able to answer the two motivating questions precisely:

**Why is the D-cell larger than the 9 V battery?** The 9 V battery achieves its voltage by connecting six 1.5 V cells in series. Series stacking adds voltage but does not add capacity — each cell stores the same charge as a standalone cell. The D-cell is a single large cell whose volume is dedicated entirely to maximizing active material and therefore maximizing stored charge. More material = more capacity = longer runtime at the same current. The 9 V battery trades capacity for voltage.

**Why does battery voltage drop during discharge?** As the reaction proceeds, the cathode ion (oxidant) is consumed and the anode ion (reductant) accumulates. The reaction quotient Q = [product ions] / [reactant ions] grows. The Nernst equation says E_cell decreases as ln(Q) increases. Near end of life, Q approaches its equilibrium value K, at which point E_cell → 0. A "dead" battery has not lost its electrons — it has equilibrated.
