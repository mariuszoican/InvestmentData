# Does Paying for Data Change Investment Decisions?

This repository contains the code, simulations, and documentation supporting the paper:

**Does Paying for Data Change Investment Decisions?**  
Philipp Chapkovski, Arzu Işık, Mariana Khapko, and Marius Zoican

The project studies how paying for market data (as opposed to receiving it for free)
affects belief formation, forecasting, and investment behavior in a controlled
investment experiment.

---

### Repository Overview

This repository is organized to separate **experimental data and empirical analysis**,
**theoretical simulations**, and **supporting documentation**.  
The `clean-share` branch removes pilot data and administrative material, focusing on
replication and transparency.

---

### Directory Structure

#### `experimental_project/`
Contains all code and outputs used for the **main empirical analysis** in the paper.

- Data processing scripts  
- Estimation code  
- Regression outputs and tables  
- Figures used in the paper  

This folder is the primary entry point for reproducing the empirical results.

---

#### `simulations/`
Contains theory and simulation code used to:

- Calibrate the experimental environment  
- Simulate investment outcomes  
- Quantify the ex-ante value of data acquisition  

---

#### `plots/` and `plot_paths/`
Scripts and outputs used to generate figures based on simulation and empirical results.

---

#### `tables/`
Generated regression tables and intermediate outputs used in the paper.

---

#### `IRISS/`
Documentation related to research ethics approval and experimental protocols.

Includes:
- REB certificate  
- Consent forms  
- Experimental protocols  
- Platform screenshots and methodology documents
