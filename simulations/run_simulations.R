library(here)
library(rstudioapi)
setwd(dirname(getActiveDocumentContext()$path))


source("market_sim.R")   # load simulation function

# Single run, informative:
res1 <- simulate_market(seed = 88, alpha = 0.3, informative = 1)
# Single run, uninformative:
res1 <- simulate_market(seed = 88, alpha = 0.3, informative = 0)


# Loop over many seeds:
results <- lapply(1:100, function(i) {
  simulate_market(seed = 400 + i,
                  informative = i %% 2,   # alternate info / non-info
                  plot = TRUE,           # no plotting in big loops
                  save_png = TRUE)
})