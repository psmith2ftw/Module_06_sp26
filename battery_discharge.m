%% battery_discharge.m  —  Module 7: Battery Design Optimization
%  Part 3: Nernst discharge simulation with internal resistance.
%
%  WHAT YOU FILL IN  (search for  <- YOUR WORK):
%    1. E_std and n
%    2. Q expression in nernst_voltage subfunction
%    3. R_int, V_device_threshold
%    4. Active mass inputs (Part 2 numbers) -- real-unit simulation
%
%  Usage: open in MATLAB, press Run (F5).
% =========================================================================

%% --- Physical constants --------------------------------------------------
F_c   = 96485;
R_gas = 8.314;
T_K   = 298.15;

%% --- Cell parameters  <- YOUR WORK --------------------------------------
E_std = 0.00;   % <- YOUR WORK: E_cell (V)
n     = 0;      % <- YOUR WORK: electrons per formula unit

% Internal resistance
% Coin cell ~10-30 Ohm | AA alkaline ~0.1-0.5 | Li-ion ~0.05-0.15
R_int = 10.0;   % <- YOUR WORK (Ohm)

% Device threshold (V)
% IoT coin cell: 3.0 | Pacemaker: 2.5 | Flashlight: 1.2
V_device_threshold = 3.00;  % <- YOUR WORK

%% --- Active mass inputs  <- YOUR WORK (from Part 2 Table 2) -------------
%
%  Fill these in so the simulation runs in real physical units.
%  V_soln is then computed from your Part 2 mass.
%  Leave as NaN to fall back to the 0.1 mL model cell (curves correct,
%  mAh numbers meaningless for your application).
%
MW_cathode_compound = NaN;  % <- YOUR WORK: compound MW g/mol (e.g. AuCl3 = 303.325)
cathode_coeff       = NaN;  % <- YOUR WORK: stoich. coeff. in balanced equation
MW_anode_elemental  = NaN;  % <- YOUR WORK: elemental MW g/mol (e.g. Mg = 24.305)
anode_coeff         = NaN;  % <- YOUR WORK: stoich. coeff. in balanced equation
active_mass_g       = NaN;  % <- YOUR WORK: total active mass (g) for ONE cell

%% --- Derive V_soln from mass, or fall back to model cell ----------------
C_ox_0  = 1.000;   % mol/L
C_red_0 = 0.001;   % mol/L

using_real_mass = ~any(isnan([MW_cathode_compound, cathode_coeff, ...
                               MW_anode_elemental,  anode_coeff, active_mass_g]));

if using_real_mass
    % g per mol of reaction (same as Part 1 Table 1)
    total_mass_g_per_mol_rxn = anode_coeff * MW_anode_elemental + ...
                                cathode_coeff * MW_cathode_compound;
    moles_rxn     = active_mass_g / total_mass_g_per_mol_rxn;
    moles_cathode = cathode_coeff * moles_rxn;
    V_soln        = moles_cathode / C_ox_0;   % liters
    mass_note     = sprintf('  Active mass: %.4f g  ->  V_soln = %.4f mL  (real-unit simulation)', ...
                             active_mass_g, V_soln*1000);
else
    V_soln    = 1e-4;
    mass_note = '  WARNING: Active mass not set -- using 0.1 mL model cell.';
end

%% --- Discharge currents --------------------------------------------------
current_labels = {'Design   (0.10 mA)', '10x load  (1.0 mA)', '100x burst (10 mA)'};
current_mA     = [0.10, 1.00, 10.00];

%% --- Input check ---------------------------------------------------------
if E_std == 0 || n == 0
    error('Fill in E_std and n before running.');
end

theo_cell_mAh = n * F_c * C_ox_0 * V_soln / 3.6;
fprintf('====================================================================\n');
fprintf('  DISCHARGE SIMULATION\n');
fprintf('  E_std = %.2f V  |  n = %d  |  R_int = %.1f Ohm\n', E_std, n, R_int);
fprintf('  Cell capacity: %.4f mAh  (V_soln = %.4f mL)\n', theo_cell_mAh, V_soln*1000);
fprintf('  Device threshold: %.2f V\n', V_device_threshold);
fprintf('%s\n', mass_note);
fprintf('====================================================================\n');

%% --- Run simulations -----------------------------------------------------
N_STEPS = 1500;
colors  = {'steelblue', [0.85 0.45 0.10], 'seagreen'};
results = struct();

for k = 1:numel(current_mA)
    I_mA = current_mA(k);
    I_A  = I_mA / 1000;

    t_dep_est = C_ox_0 * V_soln * n * F_c / I_A;
    dt        = t_dep_est / N_STEPS;
    dCox      = -I_A / (n * F_c * V_soln);
    dCred     = +I_A / (n * F_c * V_soln);

    C_ox  = C_ox_0;  C_red = C_red_0;  t = 0;
    V_oc0 = nernst_voltage(C_red, C_ox, E_std, n, R_gas, T_K, F_c);

    t_h_arr    = 0;
    V_oc_arr   = V_oc0;
    V_term_arr = V_oc0 - I_A * R_int;
    dod_arr    = 0;

    for step = 1:(N_STEPS * 2)
        C_ox  = C_ox  + dCox  * dt;
        C_red = C_red + dCred * dt;
        t     = t + dt;
        if C_ox <= 1e-9; break; end

        dod    = 1 - C_ox / C_ox_0;
        V_oc   = nernst_voltage(C_red, C_ox, E_std, n, R_gas, T_K, F_c);
        V_term = V_oc - I_A * R_int;

        t_h_arr(end+1)    = t / 3600;   %#ok<AGROW>
        V_oc_arr(end+1)   = V_oc;       %#ok<AGROW>
        V_term_arr(end+1) = V_term;     %#ok<AGROW>
        dod_arr(end+1)    = dod;        %#ok<AGROW>

        if V_term < V_device_threshold; break; end
    end

    usable_mAh = I_mA * t_h_arr(end);
    area_Vh    = trapz(t_h_arr, V_term_arr);   % integral of V over t [V*h]
    energy_Wh  = area_Vh * I_A;               % [V*h * A = Wh]
    eff_frac   = dod_arr(end);
    ohmic_mV   = I_A * R_int * 1000;
    hit_thresh = V_term_arr(end) < V_device_threshold + 0.005;
    if hit_thresh; stop_str = 'device threshold'; else; stop_str = 'reactant depleted'; end

    results(k).label     = current_labels{k};
    results(k).t_h       = t_h_arr;
    results(k).V_oc      = V_oc_arr;
    results(k).V_term    = V_term_arr;
    results(k).dod       = dod_arr;
    results(k).usable    = usable_mAh;
    results(k).energy    = energy_Wh;
    results(k).eff_frac  = eff_frac;
    results(k).ohmic_mV  = ohmic_mV;

    fprintf('\n  %s\n', current_labels{k});
    fprintf('    Ohmic drop:              %.1f mV\n',   ohmic_mV);
    fprintf('    V at start:              %.4f V\n',    V_term_arr(1));
    fprintf('    Runtime:                 %.4f h  (%.2f min)\n', t_h_arr(end), t_h_arr(end)*60);
    fprintf('    Usable capacity (cell):  %.4f mAh\n',  usable_mAh);
    fprintf('    Usable energy  (trapz):  %.4f mWh\n',  energy_Wh*1000);
    fprintf('    Coulombic efficiency:    %.1f%%  (%s)\n', eff_frac*100, stop_str);
end

%% --- Plot ----------------------------------------------------------------
t_max = max(cellfun(@(k) results(k).t_h(end), num2cell(1:numel(results))));

figure('Position', [50 50 1200 520], 'Name', 'Discharge Curves');

% Left panel: V_term vs time (h)
subplot(1, 2, 1);  hold on;
for k = 1:numel(results)
    plot(results(k).t_h, results(k).V_term, ...
         'Color', colors{k}, 'LineWidth', 2.2, 'DisplayName', results(k).label);
    mask   = results(k).V_term >= V_device_threshold;
    t_fill = results(k).t_h(mask);
    v_fill = results(k).V_term(mask);
    if any(mask)
        fill([t_fill, fliplr(t_fill)], [v_fill, zeros(1,sum(mask))], ...
             colors{k}, 'FaceAlpha', 0.12, 'EdgeColor', 'none', ...
             'HandleVisibility', 'off');
    end
end
yline(V_device_threshold, 'r--', 'LineWidth', 1.8, ...
      'Label', sprintf('Threshold (%.1f V)', V_device_threshold), ...
      'LabelHorizontalAlignment', 'left', 'FontSize', 9, ...
      'DisplayName', sprintf('Device threshold (%.1f V)', V_device_threshold));
yline(E_std, ':', 'Color', [0.5 0.5 0.5], 'LineWidth', 1.2, ...
      'Label', sprintf('E_std = %.2f V', E_std), ...
      'LabelHorizontalAlignment', 'left', 'FontSize', 9, ...
      'HandleVisibility', 'off');
hold off;
xlabel('Time (h)',             'FontSize', 12);
ylabel('Terminal Voltage (V)', 'FontSize', 12);
title({'Terminal Voltage vs. Time', 'Three discharge rates overlaid'}, ...
      'FontSize', 12, 'FontWeight', 'bold');
legend('Location', 'northeast', 'FontSize', 9);
grid on;  xlim([0  t_max*1.03]);  ylim([0  inf]);  set(gca,'FontSize',10);

% Right panel: Voc vs Vterm vs time (h)
subplot(1, 2, 2);  hold on;
plot(results(1).t_h, results(1).V_oc, 'k--', 'LineWidth', 1.8, ...
     'DisplayName', 'Open-circuit (Nernst, no load)');
for k = 1:numel(results)
    plot(results(k).t_h, results(k).V_term, ...
         'Color', colors{k}, 'LineWidth', 2.0, ...
         'DisplayName', sprintf('%s  (-%.0f mV ohmic)', ...
             results(k).label, results(k).ohmic_mV));
end
yline(V_device_threshold, 'r--', 'LineWidth', 1.8, ...
      'Label', sprintf('Threshold (%.1f V)', V_device_threshold), ...
      'LabelHorizontalAlignment', 'left', 'FontSize', 9);
hold off;
xlabel('Time (h)',     'FontSize', 12);
ylabel('Voltage (V)',  'FontSize', 12);
title({'Open-Circuit vs. Terminal Voltage', 'Gap = I x R_{int}'}, ...
      'FontSize', 12, 'FontWeight', 'bold');
legend('Location', 'northeast', 'FontSize', 9);
grid on;  xlim([0  t_max*1.03]);  set(gca,'FontSize',10);

sgtitle(sprintf('Discharge Model  |  E_std = %.2f V,  n = %d,  R_int = %.1f Ohm', ...
                E_std, n, R_int), 'FontSize', 13, 'FontWeight', 'bold');
saveas(gcf, 'discharge_curves.png');
fprintf('\n  Saved: discharge_curves.png\n');

%% --- Capacity summary ----------------------------------------------------
fprintf('\n====================================================================\n');
fprintf('  USABLE CAPACITY SUMMARY\n');

if using_real_mass
    specific_cap_mAh_kg = (n * F_c * 1000) / (3600 * (total_mass_g_per_mol_rxn / 1000));
    theo_part2_mAh      = specific_cap_mAh_kg * (active_mass_g / 1000);
    fprintf('  Specific capacity (Part 1):  %.0f mAh/kg\n', specific_cap_mAh_kg);
    fprintf('  Active mass (Part 2):        %.4f g\n', active_mass_g);
    fprintf('  Theoretical capacity:        %.4f mAh\n', theo_part2_mAh);
    fprintf('\n  %-26s  %11s  %14s  %16s  %14s\n', ...
            'Current', 'Runtime (h)', 'Usable (mAh)', 'Coulombic eff.', 'Real usable');
    fprintf('  %s\n', repmat('-', 1, 86));
    for k = 1:numel(results)
        real_usable = results(k).eff_frac * theo_part2_mAh;
        fprintf('  %-26s  %11.4f  %14.4f  %14.1f%%  %14.4f mAh\n', ...
                results(k).label, results(k).t_h(end), ...
                results(k).usable, results(k).eff_frac*100, real_usable);
    end
    fprintf('\n  ''Real usable'' = Coulombic efficiency x theoretical capacity\n');
else
    fprintf('  %-26s  %11s  %14s  %16s\n', ...
            'Current', 'Runtime (h)', 'Usable (mAh)', 'Coulombic eff.');
    fprintf('  %s\n', repmat('-', 1, 70));
    for k = 1:numel(results)
        fprintf('  %-26s  %11.4f  %14.4f  %14.1f%%\n', ...
                results(k).label, results(k).t_h(end), ...
                results(k).usable, results(k).eff_frac*100);
    end
    fprintf('\n  Fill in MW, stoich coefficients, and active_mass_g for real-unit output.\n');
end

%% --- Nernst subfunction --------------------------------------------------
function V = nernst_voltage(C_red, C_ox, E_std, n, R_gas, T_K, F_c)
    if C_ox <= 0 || C_red <= 0; V = NaN; return; end
    Q = C_red / C_ox;   % <- YOUR WORK: adjust for your cell's stoichiometry
    V = E_std - (R_gas * T_K / (n * F_c)) * log(Q);
end
