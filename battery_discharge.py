"""
battery_discharge.py  —  Module 7: Battery Design Optimization
Part 3: Nernst discharge simulation with internal resistance.

WHAT IS PROVIDED:
  - Euler integration loop (complete — do not modify)
  - Terminal voltage vs TIME plot showing three current levels
  - Usable capacity and energy (via trapezoidal integration) for each rate

WHAT YOU FILL IN  (search for  ← YOUR WORK):
  1. E_std and n for your chosen cell
  2. The Q expression in nernst_voltage()
  3. R_int — see guidance below
  4. V_device_threshold — your device's minimum operating voltage

ABOUT V_soln:
  V_soln = 0.1 mL is a small model cell chosen so all three simulations
  run in seconds.  The SHAPE of the curves and the usable-fraction results
  are what matter here, not the absolute mAh scale.
  To match your Part 2 active mass, see the optional section at the end.

Usage:  python battery_discharge.py
"""

import numpy as np
import matplotlib.pyplot as plt

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
#   At low current the drop is negligible; at high current it can shut the
#   device off even when the cell is fresh.
#
#   Typical values:
#     Coin cell (CR2032 type):    10 – 30 Ω
#     AA alkaline:                 0.1 – 0.5 Ω
#     Li-ion 18650:                0.05 – 0.15 Ω
R_int = 10.0    # ← YOUR WORK: choose a value appropriate for your cell (Ω)

# Model electrolyte cell
C_ox_0  = 1.000   # mol/L  — cathode ion, starting concentration
C_red_0 = 0.001   # mol/L  — anode ion, ~0 at start (but non-zero to avoid ln(0))
V_soln  = 1.0e-4  # L      — model volume (0.1 mL); see note above

# Device operating threshold:
# The simulation stops when V_terminal drops below this value.
# IoT coin cell / 3.3 V microcontroller: 3.0 V
# Pacemaker application:                 2.5 V
# Flashlight application:                1.2 V
V_device_threshold = 3.00     # ← YOUR WORK (V)

# ─────────────────────────────────────────────────────────────────────────────
# DISCHARGE CURRENTS  ← YOUR WORK
# Three currents for your chosen IoT coin cell:
#   design current | 10× overload | 100× overload
# These span the range from normal sleep-cycle operation to a brief hardware fault.
# ─────────────────────────────────────────────────────────────────────────────

currents_mA = {
    'Design   (0.10 mA)':    0.10,
    '10× load  (1.0 mA)':    1.00,
    '100× burst (10 mA)':   10.00,
}


# ─────────────────────────────────────────────────────────────────────────────
# NERNST VOLTAGE FUNCTION  ← YOUR WORK  (fill in the Q expression)
# ─────────────────────────────────────────────────────────────────────────────

def nernst_voltage(C_red, C_ox):
    """
    Open-circuit voltage via the Nernst equation:
        E = E°_cell − (RT / nF) × ln(Q)

    Fill in the correct Q for your cell.

    For a simple 1:1 cell:
        Anode:   A(s)     → A^n+(aq) + n e⁻
        Cathode: B^n+(aq) + n e⁻ → B(s)
        Q = [A^n+] / [B^n+]  =  C_red / C_ox    ← already written below

    If your balanced equation has different stoichiometric coefficients,
    adjust the exponents accordingly.
    Pure solids do NOT appear in Q (their activity = 1).
    """
    if C_ox <= 0 or C_red <= 0:
        return np.nan

    Q = C_red / C_ox    # ← YOUR WORK: modify if stoichiometry differs

    return E_std - (R_gas * T_K / (n * F)) * np.log(Q)


# ─────────────────────────────────────────────────────────────────────────────
# EULER INTEGRATION  — do not modify below this line
# ─────────────────────────────────────────────────────────────────────────────

N_STEPS = 1500   # data points per simulation (adaptive dt achieves this)

def run_discharge(I_mA):
    """
    Constant-current Euler discharge.
    Returns arrays of time (h), open-circuit voltage, terminal voltage,
    and depth-of-discharge, plus scalar summary metrics.
    """
    I_A = I_mA / 1000.0

    # Adaptive dt: scale so we always get ~N_STEPS data points
    t_dep_est = C_ox_0 * V_soln * n * F / I_A   # estimated time to full depletion (s)
    dt        = t_dep_est / N_STEPS

    # Concentration change rates [mol/L/s] at constant current
    dCox  = -I_A / (n * F * V_soln)    # cathode ion consumed
    dCred = +I_A / (n * F * V_soln)    # anode ion produced

    C_ox  = C_ox_0
    C_red = C_red_0
    t     = 0.0

    V_oc0 = nernst_voltage(C_red, C_ox)
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

    # Usable capacity: constant current, so I × t is exact.
    # Usable energy via trapezoidal integration under V(t) curve (README Step 8):
    #   ∫ V(t) dt  [V·h]  × I [A]  =  energy [Wh]
    try:
        area_Vh = np.trapezoid(V_term_arr, t_h_arr)   # numpy ≥ 2.0
    except AttributeError:
        area_Vh = np.trapz(V_term_arr, t_h_arr)        # numpy < 2.0
    energy_Wh  = area_Vh * I_A                        # Wh  (V·h × A = Wh)

    theo_mAh   = I_mA * (t_dep_est / 3600.0)          # if discharged to depletion
    usable_mAh = I_mA * t_h_arr[-1]                   # delivered above threshold

    eff_pct    = 100.0 * dod_arr[-1]                  # reactant fraction consumed

    return dict(t_h=t_h_arr, V_oc=V_oc_arr, V_term=V_term_arr, dod=dod_arr,
                usable_mAh=usable_mAh, energy_Wh=energy_Wh,
                theo_mAh=theo_mAh, eff_pct=eff_pct,
                hit_threshold=(V_term_arr[-1] < V_device_threshold + 0.005))


# ─────────────────────────────────────────────────────────────────────────────
# RUN, PRINT, AND PLOT
# ─────────────────────────────────────────────────────────────────────────────

if E_std == 0.0 or n == 0:
    print("⚠  Fill in E_std and n (marked ← YOUR WORK) before running.")
else:
    theo_model_cell_mAh = n * F * C_ox_0 * V_soln / 3.6

    print("=" * 68)
    print(f"  DISCHARGE SIMULATION")
    print(f"  E° = {E_std} V  |  n = {n}  |  R_int = {R_int} Ω")
    print(f"  Model cell capacity: {theo_model_cell_mAh:.2f} mAh  "
          f"(V_soln = {V_soln*1000:.2f} mL)")
    print(f"  Device threshold: {V_device_threshold} V")
    print("=" * 68)

    colors  = ['steelblue', 'darkorange', 'seagreen']
    results = {}

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5.5))

    for (label, I_mA), color in zip(currents_mA.items(), colors):
        res = run_discharge(I_mA)
        results[label] = res
        ohmic_mV = (I_mA / 1000) * R_int * 1000

        # ── Left plot: terminal voltage vs TIME (h) ──────────────────────
        ax1.plot(res['t_h'], res['V_term'],
                 color=color, linewidth=2.2, label=label)
        # Shade the area UNDER the curve for usable energy (above threshold)
        ax1.fill_between(res['t_h'],
                         0, res['V_term'],
                         where=(res['V_term'] >= V_device_threshold),
                         color=color, alpha=0.12)

        # ── Right plot: V_oc (once) and V_term for each current ──────────
        if label == list(currents_mA.keys())[0]:
            ax2.plot(res['t_h'], res['V_oc'],
                     'k--', lw=1.8, alpha=0.55,
                     label='Open-circuit  (no load, Nernst only)')
        ax2.plot(res['t_h'], res['V_term'],
                 color=color, linewidth=2.0,
                 label=f'{label}  (−{ohmic_mV:.0f} mV ohmic)')

        stop = "device threshold" if res['hit_threshold'] else "reactant depleted"
        print(f"\n  {label}")
        print(f"    Ohmic drop:             {ohmic_mV:.1f} mV")
        print(f"    V at start:             {res['V_term'][0]:.4f} V")
        print(f"    Runtime:                {res['t_h'][-1]:.4f} h  "
              f"({res['t_h'][-1]*60:.1f} min)")
        print(f"    Usable capacity:        {res['usable_mAh']:.4f} mAh")
        print(f"    Usable energy (trapz):  {res['energy_Wh']*1000:.4f} mWh")
        print(f"    DoD at cutoff:          {res['eff_pct']:.1f}%  ({stop})")

    # Shared x-limit: span the full runtime of the slowest discharge
    t_max = max(res['t_h'][-1] for res in results.values())

    # Left panel ──────────────────────────────────────────────────────────
    ax1.axhline(V_device_threshold, color='red', ls='--', lw=1.8,
                label=f'Device threshold ({V_device_threshold} V)')
    ax1.axhline(E_std, color='grey', ls=':', lw=1.2,
                label=f'E°_cell = {E_std} V')
    ax1.set_xlabel('Time (h)',              fontsize=12)
    ax1.set_ylabel('Terminal Voltage (V)',  fontsize=12)
    ax1.set_title('Terminal Voltage vs. Time\n'
                  'Three discharge rates overlaid',
                  fontsize=12, fontweight='bold')
    ax1.legend(fontsize=9, loc='upper right')
    ax1.grid(True, alpha=0.30)
    ax1.set_xlim(0, t_max * 1.03)
    ax1.set_ylim(bottom=0)
    ax1.tick_params(labelsize=10)

    # Right panel ─────────────────────────────────────────────────────────
    ax2.axhline(V_device_threshold, color='red', ls='--', lw=1.8,
                label=f'Device threshold ({V_device_threshold} V)')
    ax2.set_xlabel('Time (h)',          fontsize=12)
    ax2.set_ylabel('Voltage (V)',       fontsize=12)
    ax2.set_title('Open-Circuit vs. Terminal Voltage\n'
                  'Gap = I × R_int  (the hidden voltage loss)',
                  fontsize=12, fontweight='bold')
    ax2.legend(fontsize=9, loc='upper right')
    ax2.grid(True, alpha=0.30)
    ax2.set_xlim(0, t_max * 1.03)
    ax2.tick_params(labelsize=10)

    plt.suptitle(
        f'Discharge Model  |  E° = {E_std} V,  n = {n},  R_int = {R_int} Ω',
        fontsize=13, fontweight='bold', y=1.01)
    plt.tight_layout()
    plt.savefig('discharge_curves.png', dpi=150, bbox_inches='tight')
    plt.show()
    print("\n  Saved: discharge_curves.png")

    # Efficiency table ────────────────────────────────────────────────────
    print()
    print("=" * 68)
    print("  USABLE CAPACITY SUMMARY")
    print(f"  {'Current':26s}  {'Runtime (h)':>11}  {'Usable (mAh)':>14}  "
          f"{'Energy (mWh)':>14}  {'DoD':>7}")
    print(f"  {'─'*76}")
    for label, res in results.items():
        print(f"  {label:26s}  {res['t_h'][-1]:>11.4f}  "
              f"{res['usable_mAh']:>14.4f}  "
              f"{res['energy_Wh']*1000:>14.4f}  "
              f"{res['eff_pct']:>6.1f}%")

    print()
    print("  To compare to your Part 2 theoretical capacity:")
    print("    specific_cap_mAh_kg = ???   # from your Table 1")
    print("    active_mass_kg      = ???   # from your Table 2")
    print("    theoretical_mAh     = specific_cap_mAh_kg * active_mass_kg")
    print("    efficiency = usable_mAh / theoretical_mAh * 100  # %")


# ─────────────────────────────────────────────────────────────────────────────
# OPTIONAL: scale V_soln to your Part 2 active mass
# ─────────────────────────────────────────────────────────────────────────────
# This changes the time axis but not the voltage curves or efficiency:
#
#   active_mass_g    = ???   # your Part 2 mass in grams
#   MW_cathode_g_mol = ???   # molecular weight of cathode compound (g/mol)
#   moles_cathode    = active_mass_g / MW_cathode_g_mol
#   V_soln           = moles_cathode / C_ox_0   # liters
