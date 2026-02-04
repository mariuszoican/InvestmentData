# order_imbalance_distributions.R

library(here)
library(rstudioapi)
setwd(dirname(getActiveDocumentContext()$path))

source(here::here("code", "market_simulation.R"))
source(here::here("code", "config.R"))


n_rep <- 10000


sim_uninform <- marketsim(
  N = n_rep,
  mu = config$mu,
  sigma = config$sigma,
  sigma_imb = config$sigma_imb,
  seed = sample.int(1e9, 1),
  informative = 0,  # or 1 for r_pred
  plot = FALSE,
  save_png = FALSE
)

sim_inform <- marketsim(
  N = n_rep,
  mu = config$mu,
  sigma = config$sigma,
  sigma_imb = config$sigma_imb,
  seed = sample.int(1e9, 1),
  informative = 1,  # or 1 for r_pred
  plot = FALSE,
  save_png = FALSE
)

mean_inf <- mean(sim_inform$data$r_pred)
var_inf <-var(sim_inform$data$r_pred)

imb_lag1 <- c(NA, sim_inform$data$imb[-nrow(sim_inform$data)])
cor_inf <-cor(sim_inform$data$r_pred,imb_lag1, use="complete.obs")

mean_uninf <- mean(sim_uninform$data$r)
var_uninf <-var(sim_uninform$data$r)

imb_lag1 <- c(NA, sim_uninform$data$imb[-nrow(sim_uninform$data)])
cor_uninf <-cor(sim_uninform$data$r,imb_lag1, use="complete.obs")

ks_res_imb  <- ks.test(sim_inform$data$imb, sim_uninform$data$imb)
ks_stat_imb <- as.numeric(ks_res_imb$statistic)
ks_p_imb    <- ks_res_imb$p.value

ks_res_r  <- ks.test(sim_inform$data$r_pred, sim_uninform$data$r)
ks_stat_r <- as.numeric(ks_res_r$statistic)
ks_p_r    <- ks_res_r$p.value
