## Quick context

This repository simulates intraday returns and order-flow imbalance to produce plots and small CSV files used in experiments. Primary code lives in `simulations/` (R). Example outputs land in `plot_paths/` and `plots/`. A Python helper/test lives in `tests/test_payoffs.py` and uses CSVs under `tests/bots/`.

When editing or running R scripts note they frequently call `setwd(dirname(getActiveDocumentContext()$path))` (RStudio helper). Many scripts are intended to be opened and run inside RStudio — an AI should prefer editing functions and avoiding blind changes to working-directory logic.

## Big picture / major components

- `simulations/market_simulation.R` (exports `marketsim`): core simulator. Returns a list with `data` (time series), `next_return`, and `png_file`.
- `simulations/run_simulations.R`: example driver that sources the simulator and runs single and batch simulations (shows usage patterns and flags).
- `simulations/select_seeds.R`: seed-selection utility that runs `marketsim` with `informative` on/off to pick seeds matching correlation tolerances.
- `simulations/config.R`: parameter bag (`config`) used by other scripts. Watch for naming mismatch: some scripts reference `config$N_plot` while `config.R` defines `N_plot.` (trailing dot) — be cautious and validate before changing.
- `plot_paths/` and `plots/`: output folders for PNGs and CSVs. Naming conventions: PNGs `sim_seed-<seed>_info-<0|1>_<access|noaccess>.png` and CSVs `sim_seed-<seed>_info-<0|1>_return.csv`.

## Common patterns and conventions to preserve

- Scripts set working directory to the script location via `rstudioapi::getActiveDocumentContext()`. If you need to run scripts non-interactively (CI or `Rscript`), adjust working-dir logic or call `source()` from project root explicitly.
- The simulator has `informative` flag: `1` uses predictable `r_pred`, `0` uses iid `r`. Many downstream steps (plots, csv names) depend on this flag.
- The `match_var` parameter enforces `sigma_imb < sigma` and computes `sigma_eps` accordingly; do not change this behavior without checking `select_seeds.R` and `config.R` assumptions.
- Plotting code multiplies returns by 100 (percentage) for display and writes `next_return` multiplied by 100 to CSVs. When comparing numeric outputs between R and Python, remember this scaling.

## How to run (developer workflows)

- Interactive (recommended for reproducing figures): open `simulations/run_simulations.R` in RStudio and run the example calls that call `simulate_market` / `marketsim`.
- Non-interactive (CI or scripted): prefer calling R functions from an R wrapper that sets working directory explicitly, e.g.

  - From project root in a shell: `Rscript -e "source('simulations/market_simulation.R'); marketsim(N=16, mu=0.15, sigma=0.12, sigma_imb=0.08, seed=88, informative=1)"`

- Outputs: PNGs and CSVs are saved into `plot_paths/` or `plots/` (see `outdir` parameter). Use `save_png` and `save_excel` flags to control writing.

## Tests and data

- There is a single Python check script `tests/test_payoffs.py` that reads `tests/bots/all_apps_wide.csv` and computes expected payoffs. This is a functional script, not a pytest suite. Run with `python3 tests/test_payoffs.py` for quick local checks.

## Integration points & I/O

- File outputs: `plot_paths/sim_seed-<seed>_info-<0|1>_return.csv` (next return, 100x) and PNG files as noted above.
- Data inputs for Python checks: `tests/bots/*.csv` (participant data exported from experiments).

## Safety notes & low-risk edits

- Avoid wholesale renames of `config` entries; instead, add compatibility shims (e.g., set `config$N_plot <- config$N_plot.` at the top of scripts) and run the small examples in `run_simulations.R` to verify.
- Preserve `show_orderflow` / `save_png` / `save_excel` flags and their downstream naming conventions (used by plot selection and experiment pipelines).

## Examples for the AI to follow when editing

- To add a new parameter to the simulator: add it to `simulations/config.R`, then add a default argument to `marketsim()` with the same name and update `run_simulations.R` examples. Run one example from `run_simulations.R` to ensure no break.
- To change output CSV format: update `marketsim()` write.csv call and add a small reader in `tests/test_payoffs.py` to verify parity with previous files.

If anything here looks wrong or you want more detail on running inside CI / R CMD check / packaging, tell me which area to expand and I will iterate.
