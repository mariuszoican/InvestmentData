# Does Paying for Data Change Investment Decisions?

**Philipp Chapkovski, Arzu Işık, Mariana Khapko, and Marius Zoican**

## Experimental Replication Package

### Quick Start

To replicate all results:

1. **Generate Simulations**:
   ```bash
   cd simulations/
   Rscript market_simulation.R 
   python merge_roundnumber_seed.py
   Rscript value_data.R 
   ```

2. **Analyze Experimental Data**:
   ```bash
   cd Investment_Decision_Project/code/
   python prepare_panels.py
   Rscript regression_code.R
   python figures.py

   # (optional) additional specifications / robustness
   Rscript additional_exploration.R
   ```

---

## Repository Structure

```
├── simulations/
│   ├── code/                         # Simulation scripts
│   │   ├── config.R
│   │   ├── market_simulation.R
│   │   ├── order_imbalance_distribution.R
│   │   ├── run_simulations.R
│   │   ├── select_seeds.R
│   │   ├── value_data.R
│   │   └── merge_roundnumber_seed.py
│   │
│   └── generated_data/               # Simulation outputs (auto-generated)
│       ├── consolidated_simulation_results.csv
│       ├── round_metadata.csv
│       ├── plot_paths/               # Output: price path visualizations
│       └── plots/                    # Output: value-of-data panels
│
└── Investment_Decision_Project/       # Experimental analysis
    ├── code/
    │   ├── prepare_panels.py
    │   ├── regression_code.R
    │   ├── figures.py
    │   └── payoff_computation.py
    ├── data/                         # Raw oTree exports (input data)
    ├── generated_data/               # Generated datasets (created by code)
    ├── tables/                       # Output: LaTeX tables
    └── figures/                      # Output: EPS figures

```
---

## Prerequisites

**R packages:**
```r
install.packages(c("tidyverse", "fixest", "stargazer", "ggplot2", "ggfixest", "cowplot"))
```

**Python packages:**
```bash
pip install pandas numpy matplotlib seaborn statsmodels
```

---

## Simulations

### 1. Generate Experimental Rounds

```bash
cd simulations/
Rscript run_simulations.R
```

**What it does:**
- Generates 12 experimental rounds (+ 2 training)
- Creates price path visualizations with/without order flow access
- Saves PNG files in `plot_paths/`
- Outputs consolidated results to CSV

**Output files:**
- `plot_paths/sim_seed-*_info-*_access.png` (24 files)
- `plot_paths/sim_seed-*_info-*_noaccess.png`
- `consolidated_simulation_results.csv`



### 2. Calculate Data Valuation

```bash
Rscript value_data.R
```

**Output:** `plots/info_value_panels.png` showing:
- (A) Distribution of optimal investment shares
- (B) Distribution of certainty equivalents  
- (C) Value of data across risk aversion levels

### 3. Merge Round Metadata

```bash
python merge_roundnumber_seed.py
```

**Output:** `round_metadata.csv` mapping experimental rounds to simulation seeds

---

## Experimental Analysis

### Data Preparation

```bash
cd Investment_Decision_Project/code/
python prepare_panels.py
```

**What it does:**
- Filters to completed session
- Drops training rounds
- Merges main, post-experimental, and pre-experimental data
- Creates treatment indicators: `treated`, `paid_round`, `pay_for_data`
- Calculates derived variables: `investment_share`, `overconfidence`, `fin_quiz`
- Merges simulation metadata (seeds, returns, imbalances)

**Output:** `../processed_panels.csv`

---

### Main Regression Analysis

```bash
Rscript regression_code.R
```

**Generates 6 tables in `../tables/`:**

1. **beliefs_table.tex**: Payment effect on perceived informativeness
   - Tests if paying increases belief that data is informative
   - Sample splits: All, High literacy, Low literacy

2. **forecasts_table.tex**: Payment effect on forecast sensitivity to order flow
   - For participants who believe data is informative
   - Placebo test on those who believe it's uninformative

3. **forecastserror_table.tex**: Forecast errors in uninformative rounds
   - Tests "noise overfitting" when paying for data

4. **iv_table.tex**: Investment pass-through (instrumental variables)
   - First stage: Order imbalance instruments return forecasts
   - Second stage: Investment response to (instrumented) forecasts
   - Tests if payment reduces forecast pass-through

5. **selection_table.tex**: Who chooses to pay for data
   - OLS and Probit specifications
   - Predictors: overconfidence, financial literacy, demographics

6. **summary_stats.tex**: Descriptive statistics

**Also generates:** `../figures/figure_iv_results.eps`

---

### Generate Figures

```bash
python figures.py
```

**Generates 3 figures in `../figures/`:**

1. **paid_beliefs.eps**: 
   - (A) Impact of payments on beliefs
   - (B) Selection effect

2. **paid_forecasts.eps**:
   - Return forecasts by order imbalance (positive/negative)
   - Split by: (A) Full sample, (B) High literacy, (C) Low literacy

3. **selection.eps**:
   - (A) Pay choice by financial literacy
   - (B) Pay choice by overconfidence

## Authors

- **Philipp Chapkovski** (University of Duisburg-Essen) - chapkovski@gmail.com
- **Arzu Işık** (University of Calgary) - arzu.isiktopbas@ucalgary.ca
- **Mariana Khapko** (University of Toronto) - mariana.khapko@rotman.utoronto.ca
- **Marius Zoican** (University of Calgary) - marius.zoican@haskayne.ucalgary.ca
