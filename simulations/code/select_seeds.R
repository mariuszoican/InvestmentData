#select_seeds.R

library(here)
library(rstudioapi)
setwd(dirname(getActiveDocumentContext()$path))
setwd("..")

source("code/config.R")
source("code/market_simulation.R")


# candidate seeds
seeds  <- 1:1000

target_corr_info <- 0.67
tol_info         <- 0.01   # accept e.g. between 0.70 and 0.80

good_info <- data.frame(
  seed      = integer(),
  corr_pred = numeric()
)

for (s in seeds) {
  sim <- marketsim(
    N           = config$N_plot,
    mu          = config$mu,
    sigma       = config$sigma,
    sigma_imb   = config$sigma_imb,
    seed        = s,
    informative = 1,
    plot        = FALSE,
    save_png    = FALSE,
    outdir = "generated_data/plots",
    save_excel = FALSE
  )
  
  imb_lag1 <- c(NA, sim$data$imb[-nrow(sim$data)])
  corr_pred <-cor(sim$data$r_pred,imb_lag1, use="complete.obs")
  
  
  if (!is.na(corr_pred) &&
      abs(corr_pred - target_corr_info) <= tol_info) {
    good_info <- rbind(
      good_info,
      data.frame(seed = s, corr_pred = corr_pred)
      
    )
  }
}

tol_uninf <- 0.01   # accept e.g. between -0.05 and 0.05

good_uninf <- data.frame(
  seed     = integer(),
  corr_iid = numeric()
)

for (s in seeds) {
  sim <- marketsim(
    N           = config$N_plot,
    mu          = config$mu,
    sigma       = config$sigma,
    sigma_imb   = config$sigma_imb,
    seed        = s,
    informative = 0,   # iid case
    plot        = FALSE,
    save_png    = FALSE,
    outdir = "generated_data/plots",
    save_excel = FALSE  # save next return
  )
  
  imb_lag1 <- c(NA, sim$data$imb[-nrow(sim$data)])
  corr_iid <-cor(sim$data$r,imb_lag1, use="complete.obs")
  
  if (!is.na(corr_iid) &&
      abs(corr_iid) <= tol_uninf) {
    good_uninf <- rbind(
      good_uninf,
      data.frame(seed = s, corr_iid = corr_iid)
    )
  }
}