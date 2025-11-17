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
  CE  <- numeric(N)
  EU  <- numeric(N)
  Alp <- numeric(N)
  
  # run simulations for different observed imbalances
  for (i in seq_len(N)) {
    res <- expected_crra_utility(
      w0    = w0,
      mu    = mu_vec[i],
      sigma = sigma_eps,
      gamma = gamma,
      n_sim = inner
    )
    
    CE[i]  <- res$certequiv
    EU[i]  <- res$exputility
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

#### Plot of data value for different risk aversion levels
#### -----------------------------------------------------

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

# Plot
plot(
  gammas,
  value_vec,
  type = "b",
  pch = 19,
  col = "blue",
  xlab = "Risk aversion γ",
  ylab = "Value of data (certainty equivalent gain)",
  main = "Information Value vs. Risk Aversion"
)

df <- data.frame(CE = data$CE)

ggplot(df, aes(x = CE)) +
  geom_histogram(aes(y = ..density..),
                 bins = 60,
                 fill = "#4C72B0", color = "white", alpha = 0.6) +
  geom_density(color = "black", linewidth = 1.2) +
  geom_vline(xintercept = mean(df$CE), color = "red", linetype = "dotted", linewidth = 1) +
  geom_vline(xintercept = data$CE_uninformed, color = "darkblue", linetype = "dashed", linewidth = 1) +
  annotate("text", x = mean(df$CE)+5, y = 0.075, label = "Informative rounds", vjust = -1, color = "red") +
  annotate("text", x = median(data$CE_uninformed)+5.5, y = 0.1, label = "Uninformative rounds", vjust = 1.5, color = "darkblue") +
  theme_minimal(base_size = 16) +
  labs(
    x = "Certainty equivalent",
    y = "Density"
  )


dfalpha <- data.frame(alpha = data$alpha)

ggplot(dfalpha, aes(x = alpha)) +
  geom_histogram(aes(y = ..density..),
                 bins = 60,
                 fill = "#4C72B0", color = "white", alpha = 0.6) +
  geom_density(color = "black", linewidth = 1.2) +
  geom_vline(xintercept = mean(df$alpha), color = "red", linetype = "dotted", linewidth = 1) +
  geom_vline(xintercept = data$alpha_uninformed, color = "darkblue", linetype = "dashed", linewidth = 1) +
  annotate("text", x = mean(df$alpha), y = 0.075, label = "Informative rounds", vjust = -1, color = "red") +
  annotate("text", x = median(data$alpha_uninformed), y = 0.1, label = "Uninformative rounds", vjust = 1.5, color = "darkblue") +
  theme_minimal(base_size = 16) +
  labs(
    x = "Certainty equivalent",
    y = "Density"
  )
