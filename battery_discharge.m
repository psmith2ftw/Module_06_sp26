%% battery_discharge.m  —  Module 7: Battery Design Optimization
%  Part 3: Nernst discharge simulation with internal resistance.
%
%  WHAT IS PROVIDED:
%    - Euler integration loop (complete — no need to modify)
%    - Terminal voltage vs TIME (hours) plot, three current levels
%    - Usable capacity and energy via trapezoidal integration
%
%  WHAT YOU FILL IN  (search for  ← YOUR WORK):
%    1. E_std and n for your chosen cell
%    2. Q expression in the nernst_voltage subfunction
%    3. R_int and V_device_threshold
%
%  Usage: open in MATLAB and press Run (F5).
% =========================================================================

%% ─── Physical constants ──────────────────────────────────────────────────
F_c   = 96485;      % C/mol
R_gas = 8.314;      % J/(mol·K)
T_K   = 298.15;     % K  (25°C)

%% ─── Cell parameters  ← YOUR WORK ───────────────────────────────────────
E_std = 0.00;   % ← YOUR WORK: E°_cell  (V)
n     = 0;      % ← YOUR WORK: electrons transferred per formula unit

% Internal resistance (Ω):
%   Coin cell ≈ 10–30 Ω  |  AA alkaline ≈ 0.1–0.5 Ω  |  Li-ion ≈ 0.05–0.15 Ω
R_int = 10.0;   % ← YOUR WORK (Ω)

% Model electrolyte cell
C_ox_0  = 1.000;    % mol/L  cathode ion, initial
C_red_0 = 0.001;    % mol/L  anode ion, initial
V_soln  = 1e-4;     % L  (0.1 mL model cell)

% Device threshold (V) — simulation stops here
% IoT coin cell / 3.3 V MCU: 3.0 V | Pacemaker: 2.5 V | Flashlight: 1.2 V
V_device_threshold = 3.00;     % ← YOUR WORK

%% ─── Discharge currents (IoT coin cell: design + two overloads) ──────────
current_labels = {'Design   (0.10 mA)', '10x load  (1.0 mA)', '100x burst (10 mA)'};
current_mA     = [0.10,  1.00,  10.00];   % design | 10× | 100×

%% ─── Input check ─────────────────────────────────────────────────────────
if E_std == 0 || n == 0
    error('Fill in E_std and n (marked <- YOUR WORK) before running.');
end

%% ─── Run simulations ─────────────────────────────────────────────────────
N_STEPS = 1500;
colors  = {'steelblue', [0.85 0.45 0.10], 'seagreen'};
results = struct();

theo_model_mAh = n * F_c * C_ox_0 * V_soln / 3.6;
fprintf('=================================================================\n');
fprintf('  DISCHARGE SIMULATION\n');
fprintf('  E° = %.2f V  |  n = %d  |  R_int = %.1f Ω\n', E_std, n, R_int);
fprintf('  Model cell capacity: %.2f mAh  (V_soln = %.2f mL)\n', ...
        theo_model_mAh, V_soln*1000);
fprintf('  Device threshold: %.2f V\n', V_device_threshold);
fprintf('=================================================================\n');

for k = 1:numel(current_mA)
    I_mA = current_mA(k);
    I_A  = I_mA / 1000;

    % Adaptive time step
    t_dep_est = C_ox_0 * V_soln * n * F_c / I_A;
    dt        = t_dep_est / N_STEPS;

    % Concentration change rates [mol/L/s]
    dCox  = -I_A / (n * F_c * V_soln);
    dCred = +I_A / (n * F_c * V_soln);

    C_ox  = C_ox_0;
    C_red = C_red_0;
    t     = 0;

    V_oc0 = nernst_voltage(C_red, C_ox, E_std, n, R_gas, T_K, F_c);
    t_h_arr    = 0;
    V_oc_arr   = V_oc0;
    V_term_arr = V_oc0 - I_A * R_int;
    dod_arr    = 0;

    for step = 1:(N_STEPS * 2)
        C_ox  = C_ox  + dCox  * dt;
        C_red = C_red + dCred * dt;
        t     = t + dt;

        if C_ox <= 1e-9
            break
        end

        dod    = 1 - C_ox / C_ox_0;
        V_oc   = nernst_voltage(C_red, C_ox, E_std, n, R_gas, T_K, F_c);
        V_term = V_oc - I_A * R_int;

        t_h_arr(end+1)    = t / 3600;  %#ok<AGROW>
        V_oc_arr(end+1)   = V_oc;      %#ok<AGROW>
        V_term_arr(end+1) = V_term;    %#ok<AGROW>
        dod_arr(end+1)    = dod;       %#ok<AGROW>

        if V_term < V_device_threshold
            break
        end
    end

    % Usable capacity (constant current)
    usable_mAh = I_mA * t_h_arr(end);

    % Usable energy via trapezoidal integration under V(t) curve (README Step 8)
    %   area [V·h] × I [A] = energy [Wh]
    area_Vh   = trapz(t_h_arr, V_term_arr);
    energy_Wh = area_Vh * I_A;

    theo_mAh   = I_mA * (t_dep_est / 3600);
    eff_pct    = dod_arr(end) * 100;
    ohmic_mV   = I_A * R_int * 1000;
    hit_thresh = V_term_arr(end) < V_device_threshold + 0.005;
    if hit_thresh; stop_str = 'device threshold';
    else;          stop_str = 'reactant depleted'; end

    results(k).label    = current_labels{k};
    results(k).t_h      = t_h_arr;
    results(k).V_oc     = V_oc_arr;
    results(k).V_term   = V_term_arr;
    results(k).dod      = dod_arr;
    results(k).usable   = usable_mAh;
    results(k).energy   = energy_Wh;
    results(k).theo     = theo_mAh;
    results(k).eff_pct  = eff_pct;
    results(k).ohmic_mV = ohmic_mV;

    fprintf('\n  %s\n', current_labels{k});
    fprintf('    Ohmic drop:             %.1f mV\n',   ohmic_mV);
    fprintf('    V at start:             %.4f V\n',    V_term_arr(1));
    fprintf('    Runtime:                %.4f h  (%.1f min)\n', t_h_arr(end), t_h_arr(end)*60);
    fprintf('    Usable capacity:        %.4f mAh\n',  usable_mAh);
    fprintf('    Usable energy (trapz):  %.4f mWh\n',  energy_Wh*1000);
    fprintf('    DoD at cutoff:          %.1f%%  (%s)\n', eff_pct, stop_str);
end

%% ─── Plot ────────────────────────────────────────────────────────────────
t_max = max([results.t_h], [], 'all');   % longest runtime across all cases

figure('Position', [50 50 1200 520], 'Name', 'Discharge Curves');

% Left panel: terminal voltage vs TIME (h)
subplot(1, 2, 1);
hold on;
for k = 1:numel(results)
    plot(results(k).t_h, results(k).V_term, ...
         'Color', colors{k}, 'LineWidth', 2.2, ...
         'DisplayName', results(k).label);
    % Shade area under curve for usable energy (where V_term >= threshold)
    mask = results(k).V_term >= V_device_threshold;
    t_fill = results(k).t_h(mask);
    v_fill = results(k).V_term(mask);
    if any(mask)
        fill([t_fill, fliplr(t_fill)], ...
             [v_fill,  zeros(1, sum(mask))], ...
             colors{k}, 'FaceAlpha', 0.12, 'EdgeColor', 'none', ...
             'HandleVisibility', 'off');
    end
end
yline(V_device_threshold, 'r--', 'LineWidth', 1.8, ...
      'Label', sprintf('Device threshold (%.1f V)', V_device_threshold), ...
      'LabelHorizontalAlignment', 'left', 'FontSize', 9, ...
      'DisplayName', sprintf('Device threshold (%.1f V)', V_device_threshold));
yline(E_std, ':', 'Color', [0.5 0.5 0.5], 'LineWidth', 1.2, ...
      'Label', sprintf('E° = %.2f V', E_std), ...
      'LabelHorizontalAlignment', 'left', 'FontSize', 9, ...
      'HandleVisibility', 'off');
hold off;
xlabel('Time (h)',              'FontSize', 12);
ylabel('Terminal Voltage (V)', 'FontSize', 12);
title({'Terminal Voltage vs. Time', 'Three discharge rates overlaid'}, ...
      'FontSize', 12, 'FontWeight', 'bold');
legend('Location', 'northeast', 'FontSize', 9);
grid on;  set(gca, 'FontSize', 10);
xlim([0  t_max * 1.03]);
ylim([0  inf]);

% Right panel: open-circuit vs terminal vs TIME (h)
subplot(1, 2, 2);
hold on;
plot(results(1).t_h, results(1).V_oc, 'k--', 'LineWidth', 1.8, ...
     'DisplayName', 'Open-circuit  (no load, Nernst only)');
for k = 1:numel(results)
    plot(results(k).t_h, results(k).V_term, ...
         'Color', colors{k}, 'LineWidth', 2.0, ...
         'DisplayName', sprintf('%s  (-%.0f mV ohmic)', ...
             results(k).label, results(k).ohmic_mV));
end
yline(V_device_threshold, 'r--', 'LineWidth', 1.8, ...
      'Label', sprintf('Device threshold (%.1f V)', V_device_threshold), ...
      'LabelHorizontalAlignment', 'left', 'FontSize', 9);
hold off;
xlabel('Time (h)',     'FontSize', 12);
ylabel('Voltage (V)', 'FontSize', 12);
title({'Open-Circuit vs. Terminal Voltage', 'Gap = I x R_{int}  (hidden voltage loss)'}, ...
      'FontSize', 12, 'FontWeight', 'bold');
legend('Location', 'northeast', 'FontSize', 9);
grid on;  set(gca, 'FontSize', 10);
xlim([0  t_max * 1.03]);

sgtitle(sprintf('Discharge Model  |  E° = %.2f V,  n = %d,  R_{int} = %.1f Ohm', ...
                E_std, n, R_int), 'FontSize', 13, 'FontWeight', 'bold');
saveas(gcf, 'discharge_curves.png');
fprintf('\n  Saved: discharge_curves.png\n');

%% ─── Efficiency table ────────────────────────────────────────────────────
fprintf('\n=================================================================\n');
fprintf('  USABLE CAPACITY SUMMARY\n');
fprintf('  %-24s  %11s  %14s  %14s  %7s\n', ...
        'Current', 'Runtime (h)', 'Usable (mAh)', 'Energy (mWh)', 'DoD');
fprintf('  %s\n', repmat('-', 1, 76));
for k = 1:numel(results)
    fprintf('  %-24s  %11.4f  %14.4f  %14.4f  %6.1f%%\n', ...
            results(k).label, results(k).t_h(end), ...
            results(k).usable, results(k).energy*1000, results(k).eff_pct);
end
fprintf('\n  To compare to your Part 2 theoretical capacity:\n');
fprintf('    specific_cap_mAh_kg = ???;  %% Table 1\n');
fprintf('    active_mass_kg      = ???;  %% Table 2\n');
fprintf('    theoretical_mAh     = specific_cap_mAh_kg * active_mass_kg;\n');
fprintf('    efficiency = usable_mAh / theoretical_mAh * 100;\n');

%% ─── Nernst voltage subfunction ─────────────────────────────────────────
function V = nernst_voltage(C_red, C_ox, E_std, n, R_gas, T_K, F_c)
    % E = E°_cell − (RT/nF) × ln(Q)
    % ← YOUR WORK: replace Q with the correct expression for your cell.
    % For a simple 1:1 cell: Q = C_red / C_ox
    if C_ox <= 0 || C_red <= 0
        V = NaN; return
    end
    Q = C_red / C_ox;   % ← YOUR WORK
    V = E_std - (R_gas * T_K / (n * F_c)) * log(Q);
end

%% ─── Optional: scale V_soln to Part 2 active mass ───────────────────────
% active_mass_g    = ???;   % from Table 2, in grams
% MW_cathode_g_mol = ???;   % cathode compound molecular weight
% moles_cathode    = active_mass_g / MW_cathode_g_mol;
% V_soln           = moles_cathode / C_ox_0;   % liters
% (Replace V_soln at the top of the script; voltage curves unchanged.)
