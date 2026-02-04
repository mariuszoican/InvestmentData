# run_simulations.R

library(rstudioapi)

setwd(dirname(getActiveDocumentContext()$path))
setwd("..")

source("code/config.R")
source("code/market_simulation.R")   # defines marketsim()

# Single run, informative:
res1 <- marketsim(
  N = config$N_plot,
  mu = config$mu,
  sigma = config$sigma,
  sigma_imb = config$sigma_imb,
  seed = 88,
  informative = 1
)

# Single run, uninformative:
res2 <- marketsim(
  N = config$N_plot,
  mu = config$mu,
  sigma = config$sigma,
  sigma_imb = config$sigma_imb,
  seed = 88,
  informative = 0
)

# Loop over many seeds:
results <- lapply(1:100, function(i) {
  marketsim(
    N = config$N_plot,
    mu = config$mu,
    sigma = config$sigma,
    sigma_imb = config$sigma_imb,
    seed = 400 + i,
    informative = i %% 2,           # alternate info / non-info
    plot = FALSE,                   # no plotting in big loops
    save_png = TRUE,
    outdir = "generated_data/plot_paths",
    save_excel = FALSE
  )
})
