# config.R

config <- list(
  mu = 0.15,          # Expected return (15%)
  sigma = 0.12,       # Return volatility (12%)
  sigma_imb = 0.09,   # Order imbalance volatility (9%)
  w0 = 100,           # Initial wealth (E$100)
  gamma = 24,         # Risk aversion coefficient
  N_plot = 16,        # Number of half-hour intervals (9:00-17:00)
  N = 50000,          # Simulations for valuation
  inner = 5000        # Inner simulations per draw
)