"""
battery_discharge.py  —  Module 7: Battery Design Optimization
Part 3: Nernst discharge simulation with internal resistance.

WHAT IS PROVIDED:
  - Euler integration loop (complete — do not modify)
  - Terminal voltage vs TIME (h) plot, three current levels
  - Coulombic efficiency and real usable capacity vs. Part 2 theoretical

WHAT YOU FILL IN  (search for  ← YOUR WORK):
  1. E_std and n for your chosen cell
  2. The Q expression in nernst_voltage()
  3. R_int and V_device_threshold
  4. Active mass inputs (Part 2 numbers) — lets the code run in real units

Usage:  python battery_discharge.py
"""

import numpy as np
import matplotlib.pyplot as plt
import math

# ─── Physical constants ───────────────────────────────────────────────────
F     = 96485.0    # C/mol
R_gas = 8.314      # J/(mol·K)
T_K   = 298.15     # K  (25°C)

# ─────────────────────────────────────────────────────────────────────────────
# CELL PARAMETERS  ← YOUR WORK
# ─────────────────────────────────────────────────────────────────────────────

E_std = 0.00    # ← YOUR WORK: standard cell potential E°_cell  (V)
n     = 0       # ← YOUR WORK: electrons transferred per formula unit

# Internal resistance R_int (Ω):
#   V_terminal = E_nernst − I × R_int
#   Coin cell (CR2032 type):  10 – 30 Ω
#   AA alkaline:               0.1 – 0.5 Ω
#   Li-ion 18650:              0.05 – 0.15 Ω
R_int = 10.0    # ← YOUR WORK (Ω)

# Device operating threshold (V) — simulation stops here.
#   IoT coin cell / 3.3 V MCU:  3.0 V
#   Pacemaker:                   2.5 V
#   Flashlight:                  1.2 V
V_device_threshold = 3.00     # ← YOUR WORK (V)

# ─────────────────────────────────────────────────────────────────────────────
# ACTIVE MASS INPUTS  ← YOUR WORK  (from your Part 2 Table 2)
#
#   These values connect the simulation to real battery mass and capacity.
#   Fill them in and V_soln is computed automatically so the simulation
#   runs in physical units — time axis in hours, mAh in real battery scale.
#
#   If you leave them at None the script falls back to the 0.1 mL model cell,
#   which gives correct voltage curves and efficiency fractions but tiny mAh
#   numbers that have no physical meaning for your application.
# ─────────────────────────────────────────────────────────────────────────────

# Cathode material ── the ionic species being reduced
MW_cathode_compound = None  # ← YOUR WORK: compound MW in g/mol  (e.g. AuCl₃ = 303.325)
cathode_coeff       = None  # ← YOUR WORK: stoichiometric coefficient in balanced equation

# Anode material ── the solid metal being oxidised
MW_anode_elemental  = None  # ← YOUR WORK: elemental MW in g/mol  (e.g. Mg = 24.305)
anode_coeff         = None  # ← YOUR WORK: stoichiometric coefficient in balanced equation

# Active mass your Part 2 says the application needs (one cell, not the pack)
active_mass_g       = None  # ← YOUR WORK: total active mass (g) for ONE cell

# ─── Derive V_soln from mass, or fall back to model cell ─────────────────
C_ox_0  = 1.000   # mol/L  — cathode ion starting concentration (fixed)
C_red_0 = 0.001   # mol/L  — anode ion start (~0 but non-zero to avoid ln 0)

_using_real_mass = all(x is not None for x in
    [MW_cathode_compound, cathode_coeff,
     MW_anode_elemental,  anode_coeff, active_mass_g])

if _using_real_mass:
    # total_mass_g per mol of reaction  (same formula as Part 1 Table 1)
    total_mass_g_per_mol_rxn = (anode_coeff   * MW_anode_elemental +
                                 cathode_coeff * MW_cathode_compound)

    # moles of reactant pair per gram of active material
    # moles of reaction  =  active_mass_g / total_mass_g_per_mol_rxn
    moles_rxn    = active_mass_g / total_mass_g_per_mol_rxn

    # moles of cathode ion  =  cathode_coeff × moles_rxn
    moles_cathode = cathode_coeff * moles_rxn

    # V_soln sets moles_cathode = C_ox_0 × V_soln
    V_soln = moles_cathode / C_ox_0                   # liters
    _mass_note = (f"  Active mass:  {active_mass_g:.4f} g  →  "
                  f"V_soln = {V_soln*1000:.4f} mL  "
                  f"(real-unit simulation)")
else:
    V_soln = 1.0e-4                                    # 0.1 mL model cell
    _mass_note = ("  ⚠  Active mass not set — using 0.1 mL model cell.\n"
                  "     Voltage curves and efficiency are correct;\n"
                  "     mAh values are for the model cell only.")

# Theoretical capacity for the simulated cell (mAh)
theo_cell_mAh = n * F * C_ox_0 * V_soln / 3.6 if n > 0 else 0.0


# ─────────────────────────────────────────────────────────────────────────────
# DISCHARGE CURRENTS  ← YOUR WORK
# Three currents for your chosen IoT coin cell:
#   design current | 10× overload | 100× overload
# ─────────────────────────────────────────────────────────────────────────────

currents_mA = {
    'Design   (0.10 mA)':   0.10,
    '10× load  (1.0 mA)':   1.00,
    '100× burst (10 mA)':  10.00,
}


# ─────────────────────────────────────────────────────────────────────────────
# NERNST VOLTAGE FUNCTION  ← YOUR WORK  (fill in Q)
# ─────────────────────────────────────────────────────────────────────────────

def nernst_voltage(C_red, C_ox):
    """
    E = E°_cell − (RT / nF) × ln(Q)

    Fill in Q for your cell.  For a 1:1 cell Q = C_red / C_ox.
    If stoichiometric coefficients differ, raise concentrations to those powers.
    Pure solids have activity = 1 and do NOT appear in Q.
    """
    if C_ox <= 0 or C_red <= 0:
        return np.nan
    Q = C_red / C_ox    # ← YOUR WORK: adjust if stoichiometry differs
    return E_std - (R_gas * T_K / (n * F)) * np.log(Q)


# ─────────────────────────────────────────────────────────────────────────────
# EULER INTEGRATION  — do not modify below this line
# ─────────────────────────────────────────────────────────────────────────────

N_STEPS = 1500

def run_discharge(I_mA):
    I_A = I_mA / 1000.0
    t_dep_est = C_ox_0 * V_soln * n * F / I_A
    dt        = t_dep_est / N_STEPS
    dCox      = -I_A / (n * F * V_soln)
    dCred     = +I_A / (n * F * V_soln)

    C_ox, C_red, t = C_ox_0, C_red_0, 0.0
    V_oc0   = nernst_voltage(C_red, C_ox)
    t_h_arr    = [0.0]
    V_oc_arr   = [V_oc0]
    V_term_arr = [V_oc0 - I_A * R_int]
    dod_arr    = [0.0]

    for _ in range(N_STEPS * 2):
        C_ox  += dCox  * dt
        C_red += dCred * dt
        t     += dt
        if C_ox <= 1e-9:
            break
        dod    = 1.0 - C_ox / C_ox_0
        V_oc   = nernst_voltage(C_red, C_ox)
        V_term = V_oc - I_A * R_int
        t_h_arr.append(t / 3600.0)
        V_oc_arr.append(V_oc)
        V_term_arr.append(V_term)
        dod_arr.append(dod)
        if V_term < V_device_threshold:
            break

    t_h_arr    = np.array(t_h_arr)
    V_oc_arr   = np.array(V_oc_arr)
    V_term_arr = np.array(V_term_arr)
    dod_arr    = np.array(dod_arr)

    usable_mAh = I_mA * t_h_arr[-1]

    try:
        area_Vh = np.trapezoid(V_term_arr, t_h_arr)
    except AttributeError:
        area_Vh = np.trapz(V_term_arr, t_h_arr)
    energy_Wh = area_Vh * I_A

    eff_frac  = dod_arr[-1]               # fraction of reactant consumed

    return dict(t_h=t_h_arr, V_oc=V_oc_arr, V_term=V_term_arr, dod=dod_arr,
                usable_mAh=usable_mAh, energy_Wh=energy_Wh,
                theo_mAh=(I_mA * t_dep_est / 3600.0),
                eff_frac=eff_frac,
                hit_threshold=(V_term_arr[-1] < V_device_threshold + 0.005))


# ─────────────────────────────────────────────────────────────────────────────
# RUN, PRINT, AND PLOT
# ─────────────────────────────────────────────────────────────────────────────

if E_std == 0.0 or n == 0:
    print("⚠  Fill in E_std and n before running.")
else:
    print("=" * 72)
    print("  DISCHARGE SIMULATION")
    print(f"  E° = {E_std} V  |  n = {n}  |  R_int = {R_int} Ω")
    print(f"  Model cell capacity: {theo_cell_mAh:.4f} mAh  "
          f"(V_soln = {V_soln*1000:.4f} mL)")
    print(f"  Device threshold: {V_device_threshold} V")
    print(_mass_note)
    print("=" * 72)

    colors  = ['steelblue', 'darkorange', 'seagreen']
    results = {}
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5.5))

    for (label, I_mA), color in zip(currents_mA.items(), colors):
        res      = run_discharge(I_mA)
        results[label] = res
        ohmic_mV = (I_mA / 1000) * R_int * 1000

        ax1.plot(res['t_h'], res['V_term'], color=color, lw=2.2, label=label)
        ax1.fill_between(res['t_h'], 0, res['V_term'],
                         where=(res['V_term'] >= V_device_threshold),
                         color=color, alpha=0.12)

        if label == list(currents_mA.keys())[0]:
            ax2.plot(res['t_h'], res['V_oc'], 'k--', lw=1.8, alpha=0.55,
                     label='Open-circuit  (Nernst, no load)')
        ax2.plot(res['t_h'], res['V_term'], color=color, lw=2.0,
                 label=f'{label}  (−{ohmic_mV:.0f} mV ohmic)')

        stop = "device threshold" if res['hit_threshold'] else "reactant depleted"
        print(f"\n  {label}")
        print(f"    Ohmic drop:              {ohmic_mV:.1f} mV")
        print(f"    V at start:              {res['V_term'][0]:.4f} V")
        print(f"    Runtime:                 {res['t_h'][-1]:.4f} h  "
              f"({res['t_h'][-1]*60:.2f} min)")
        print(f"    Usable capacity (cell):  {res['usable_mAh']:.4f} mAh")
        print(f"    Usable energy  (trapz):  {res['energy_Wh']*1000:.4f} mWh")
        print(f"    Coulombic efficiency:    {res['eff_frac']*100:.1f}%  ({stop})")

    t_max = max(res['t_h'][-1] for res in results.values())

    # Left panel: V_term vs time
    ax1.axhline(V_device_threshold, color='red', ls='--', lw=1.8,
                label=f'Device threshold ({V_device_threshold} V)')
    ax1.axhline(E_std, color='grey', ls=':', lw=1.2,
                label=f'E°_cell = {E_std} V')
    ax1.set_xlabel('Time (h)',             fontsize=12)
    ax1.set_ylabel('Terminal Voltage (V)', fontsize=12)
    ax1.set_title('Terminal Voltage vs. Time\nThree discharge rates overlaid',
                  fontsize=12, fontweight='bold')
    ax1.legend(fontsize=9, loc='upper right')
    ax1.grid(True, alpha=0.3)
    ax1.set_xlim(0, t_max * 1.03)
    ax1.set_ylim(bottom=0)
    ax1.tick_params(labelsize=10)

    # Right panel: Voc vs Vterm vs time
    ax2.axhline(V_device_threshold, color='red', ls='--', lw=1.8,
                label=f'Device threshold ({V_device_threshold} V)')
    ax2.set_xlabel('Time (h)',    fontsize=12)
    ax2.set_ylabel('Voltage (V)', fontsize=12)
    ax2.set_title('Open-Circuit vs. Terminal Voltage\nGap = I × R_int  (hidden voltage loss)',
                  fontsize=12, fontweight='bold')
    ax2.legend(fontsize=9, loc='upper right')
    ax2.grid(True, alpha=0.3)
    ax2.set_xlim(0, t_max * 1.03)
    ax2.tick_params(labelsize=10)

    plt.suptitle(
        f'Discharge Model  |  E° = {E_std} V,  n = {n},  R_int = {R_int} Ω',
        fontsize=13, fontweight='bold', y=1.01)
    plt.tight_layout()
    plt.savefig('discharge_curves.png', dpi=150, bbox_inches='tight')
    plt.show()
    print("\n  Saved: discharge_curves.png")

    # ── Capacity summary ─────────────────────────────────────────────────
    print()
    print("=" * 72)
    print("  USABLE CAPACITY SUMMARY")
    if _using_real_mass:
        # Part 2 theoretical capacity for the real cell
        specific_cap_mAh_kg = (n * F * 1000) / (3600 * (total_mass_g_per_mol_rxn / 1000))
        theo_part2_mAh      = specific_cap_mAh_kg * (active_mass_g / 1000)
        print(f"  Specific capacity (Part 1):  {specific_cap_mAh_kg:,.0f} mAh/kg")
        print(f"  Active mass (Part 2):        {active_mass_g:.4f} g")
        print(f"  Theoretical capacity:        {theo_part2_mAh:.4f} mAh")
        print()
        print(f"  {'Current':26s}  {'Runtime (h)':>11}  "
              f"{'Usable (mAh)':>14}  {'Coulombic eff.':>16}  "
              f"{'Real usable':>14}")
        print(f"  {'─'*88}")
        for label, res in results.items():
            real_usable = res['eff_frac'] * theo_part2_mAh
            print(f"  {label:26s}  {res['t_h'][-1]:>11.4f}  "
                  f"{res['usable_mAh']:>14.4f}  "
                  f"{res['eff_frac']*100:>14.1f}%  "
                  f"{real_usable:>14.4f} mAh")
        print()
        print("  'Real usable' = Coulombic efficiency × theoretical capacity")
        print("   This is the actual deliverable charge for your application.")
    else:
        print(f"  {'Current':26s}  {'Runtime (h)':>11}  "
              f"{'Usable (mAh)':>14}  {'Coulombic eff.':>16}")
        print(f"  {'─'*72}")
        for label, res in results.items():
            print(f"  {label:26s}  {res['t_h'][-1]:>11.4f}  "
                  f"{res['usable_mAh']:>14.4f}  "
                  f"{res['eff_frac']*100:>14.1f}%")
        print()
        print("  ⚠  Fill in MW_cathode_compound, cathode_coeff, MW_anode_elemental,")
        print("     anode_coeff, and active_mass_g to see real-battery capacity.")
