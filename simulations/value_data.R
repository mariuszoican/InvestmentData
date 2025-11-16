mu<-0.06 # unconditional mean
sigma<-0.12 # unconditional volatility
sigma_imb <-0.09 # volatility of imbalance
w0<-100 # initial wealth
gamma<-24 # risk aversion


# Compute expected CRRA utility via simulation
expected_crra_utility <- function(w0,
                                  mu, sigma,
                                  gamma, n_sim = 1e6) {
  # risky return ~ Normal(mu, sigma)
  r <- rnorm(n_sim, mean = mu, sd = sigma)
  
  alpha <- min(1,max(mu/(gamma*sigma^2),0)) # optimal investment
  # final wealth
  w1 <- w0 * (1 + alpha * r)
  
  if (gamma == 1) {
    # log utility limit case
    util <- log(w1)
    eu<-mean(util)
    ce<- exp(eu)
  } else {
    util <- (w1^(1 - gamma)) / (1 - gamma)
    eu<-mean(util)
    ce <- ((1 - gamma) * eu)^(1 / (1 - gamma))
  }
  
  list(exputility=eu,certequiv=ce, alpha=alpha)
}



value_data <- function(w0, mu, sigma_imb, sigma, gamma,
                              N = 50000, inner = 5000) {
  
  uninformative <- expected_crra_utility(w0,mu,sigma,gamma)
  
  sigma_eps <- sqrt(sigma^2 - sigma_imb^2)
  
  # Draw imbalance
  imbalance <- rnorm(N, 0, sigma_imb)
  mu_vec <- mu + imbalance
  
  # Preallocate
  CE  <- numeric(N)
  EU  <- numeric(N)
  Alp <- numeric(N)
  
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
  
  value_data<-mean(CE)-uninformative$certequiv
  
  list(
    CE = CE,
    EU = EU,
    alpha = Alp,
    mean_CE = mean(CE),
    mean_EU = mean(EU),
    alpha_informed = mean(Alp),
    alpha_uninformed=uninformative$alpha,
    CE_uninformed=uninformative$CE,
    
    value_data=value_data
  )
}

data<-value_data(w0, mu, sigma_imb, sigma, gamma)

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
    N = 20000,     # reduce N / inner if slow
    inner = 3000
  )
  
  value_vec[j] <- out$value_data
}

# Plot
plot(gammas, value_vec, type = "b", pch = 19, col = "blue",
     xlab = "Risk aversion γ",
     ylab = "Value of data (certainty equivalent gain)",
     main = "Information Value vs. Risk Aversion")
