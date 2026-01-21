library(here)
library(rstudioapi)
setwd(dirname(getActiveDocumentContext()$path))

source("market_simulation.R")
source("config.R")

mu <- config$mu # unconditional mean
sigma <- config$sigma # unconditional volatility
sigma_imb <- config$sigma_imb # volatility of imbalance
w0 <- config$w0 # initial wealth
gamma <- config$gamma # risk aversion


# Compute expected CRRA utility via simulation
expected_crra_utility <- function(w0, mu, sigma, gamma, n_sim = 1e6) {
  # generate stock return
  r <- rnorm(n_sim, mean = mu, sd = sigma)
  # optimal investment: no short-selling, no leverage
  alpha <- min(1, max(mu / (gamma * sigma^2), 0))
  # final wealth
  w1 <- w0 * (1 + alpha * r)

  if (gamma == 1) {
    # log utility limit case
    util <- log(w1)
    eu <- mean(util)
    ce <- exp(eu)
  } else {
    util <- (w1^(1 - gamma)) / (1 - gamma)
    eu <- mean(util)
    # certainty equivalent
    ce <- ((1 - gamma) * eu)^(1 / (1 - gamma))
  }

  list(exputility = eu,
       certequiv = ce,
       alpha = alpha)
}


# function to get the value of data
value_data <- function(w0,
                       mu,
                       sigma_imb,
                       sigma,
                       gamma,
                       N = 50000,
                       inner = 5000) {
  # compute the baseline (uninformative benchmark)
  uninformative <- expected_crra_utility(w0, mu, sigma, gamma)

  # residual volatility after observing imbalance
  sigma_eps <- sqrt(sigma^2 - sigma_imb^2)

  # Draw imbalance
  imbalance <- rnorm(N, 0, sigma_imb)

  # new mean (\mu+observed imbalance)
  mu_vec <- mu + imbalance

  # Pre-allocate memory
  CE <- numeric(N)
  EU <- numeric(N)
  Alp <- numeric(N)

  # run simulations for different observed imbalances
  for (i in seq_len(N)) {
    res <- expected_crra_utility(
      w0 = w0,
      mu = mu_vec[i],
      sigma = sigma_eps,
      gamma = gamma,
      n_sim = inner
    )

    CE[i] <- res$certequiv
    EU[i] <- res$exputility
    Alp[i] <- res$alpha
  }

  # compute the value of data
  value_data <- mean(CE) - uninformative$certequiv

  list(
    CE = CE,
    EU = EU,
    alpha = Alp,
    mean_CE = mean(CE),
    mean_EU = mean(EU),
    alpha_informed = mean(Alp),
    alpha_uninformed = uninformative$alpha,
    CE_uninformed = uninformative$certequiv,

    value_data = value_data
  )
}

data <- value_data(w0, mu, sigma_imb, sigma, gamma)


gammas <- 10:25
value_vec <- numeric(length(gammas))

for (j in seq_along(gammas)) {
  g <- gammas[j]
  cat("Computing gamma =", g, "\n")

  out <- value_data(
    w0 = w0,
    mu = mu,
    sigma_imb = sigma_imb,
    sigma = sigma,
    gamma = g,
    N = 20000,
    # reduce N / inner if slow
    inner = 3000
  )

  value_vec[j] <- out$value_data
}

#### Plot of data value for different risk aversion levels
#### -----------------------------------------------------

# Needed packages
library(ggplot2)
library(patchwork)   # install.packages("patchwork") if needed
library(latex2exp)

# ---- 1) Data frames ----
df_gamma <- data.frame(
  gamma = gammas,
  value = value_vec
)

df_ce <- data.frame(
  CE = data$CE
)

df_alpha <- data.frame(
  alpha = data$alpha
)

ce_mean <- mean(df_ce$CE)
ce_uninf <- data$CE_uninformed

alpha_mean <- mean(df_alpha$alpha)
alpha_median <- median(df_alpha$alpha)
alpha_uninf <- data$alpha_uninformed

# ---- 2) Top-left: distribution of alpha ----
p_alpha <- ggplot(df_alpha, aes(x = alpha)) +
  # geom_histogram(aes(y = ..density..),
  #                bins = 60,
  #                fill = "#4C72B0", color = "white", alpha = 0.6) +
  geom_density(linewidth = 1.2, fill = "#69b3a2", alpha = 0.6) +
  geom_vline(xintercept = alpha_mean,
             color = "darkred", linetype = "dotted", linewidth = 0.5) +
  geom_vline(xintercept = alpha_uninf,
             color = "darkblue", linetype = "dashed", linewidth = 0.5) +
  annotate("text",
           x = alpha_mean - 0.01, y = Inf,
           label = "predictable \nrounds (mean)",
           vjust = 2, hjust = 1, color = "darkred", size = 4.5) +
  annotate("text",
           x = alpha_uninf - 0.01, y = Inf,
           label = "baseline \nrounds (mean)",
           vjust = 2, hjust = 1, color = "darkblue", size = 4.5) +
  theme_classic(base_size = 14) +
  theme(panel.grid.major = element_blank(),    # <<< no grids
        panel.grid.minor = element_blank()
  ) +
  labs(
    x = TeX("Optimal share in risky asset $\\alpha_p^*$"),
    y = "Density",
    title = "(A) Distribution of optimal investment share"
  )


# ---- 3) Top-right: distribution of certainty equivalents ----

vlines_ce <- data.frame(
  x = c(ce_mean, ce_uninf),
  type = c("Informative", "Uninformative")
)

p_ce <- ggplot(df_ce, aes(x = CE)) +
  # geom_histogram(aes(y = ..density..),
  #                bins = 60,
  #                fill = "#4C72B0", color = "white", alpha = 0.6) +
  geom_density(linewidth = 1.2, fill = "#69b3a2", alpha = 0.6) +
  geom_vline(xintercept = ce_mean,
             color = "darkred", linetype = "dotted", linewidth = 0.5) +
  geom_vline(xintercept = ce_uninf,
             color = "darkblue", linetype = "dashed", linewidth = 0.5) +
  annotate("text",
           x = ce_mean + 1, y = 0.11,
           label = "predictable \nrounds (mean)",
           vjust = 2, hjust = 0, color = "darkred", size = 4.5) +
  annotate("text",
           x = ce_uninf + 1, y = 0.18,
           label = "baseline \nrounds (mean)",
           vjust = 2, hjust = 0, color = "darkblue", size = 4.5) +
  theme_classic(base_size = 14) +
  theme(
    panel.grid.major = element_blank(),    # <<< no grids
    panel.grid.minor = element_blank(),
    legend.position = c(0.80, 0.82),          # inside the plot
    legend.justification = c(0.5, 0.5),
    legend.direction = "horizontal",           # legend items arranged horizontally
    legend.background = element_rect(
      fill = scales::alpha("white", 0.65),
      color = NA
    ),
    legend.key = element_rect(fill = NA)
  ) +
  labs(
    x = "Certainty equivalent in predictable round",
    y = "Density",
    title = "(B) Distribution of certainty equivalents"
  )


# ---- 4) Bottom panel: value of data vs risk aversion ----
p_value <- ggplot(df_gamma, aes(x = gamma, y = value)) +
  geom_line(linewidth = 1) +
  geom_point(size = 2) +
  expand_limits(y = 4) +                    # <<< start at zero
  theme_classic(base_size = 14) +
  theme(
    panel.grid.major = element_blank(),     # <<< no grids
    panel.grid.minor = element_blank()
  ) +
  labs(
    x = "Risk aversion \u03B3",
    y = "Certainty equivalent gain",
    title = "(C) Value of order imbalance data"
  )

# ---- 5) Combine: top row 2 panels, bottom row spanning both ----
combined_plot <- (p_alpha | p_ce) / p_value +
  plot_layout(heights = c(1, 1.1))  # slightly more height for bottom panel

# ---- 6) Save to ../plots as PNG ----
if (!dir.exists("../plots")) {
  dir.create("../plots", recursive = TRUE)
}

print(combined_plot)

ggsave(
  filename = "../plots/info_value_panels.png",
  plot = combined_plot,
  width = 16,
  height = 9,
  dpi = 300
)