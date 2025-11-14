n_paths    <- 10000
lambda     <- 8
alpha      <- 1
prob_good  <- 0.5
informative <- 1
W0         <- 100
mu_g <- 0.14
var_g <- 0.04^2
mu_b  <- -0.04 
var_b <- 0.04^2
gamma <- 10


## Posterior probability of good state from imbalance -------------------
p_post <- function(alpha, b, s) {
  1 / (1 + ((1 - alpha) / (1 + alpha))^(b - s))
}

## State moments for 3-outcome (or k-outcome) distributions -------------
state_moments <- function(values, probs) {
  stopifnot(abs(sum(probs) - 1) < 1e-8)
  m <- sum(values * probs)
  v <- sum(probs * (values - m)^2)
  list(mean = m, var = v)
}

## Predictive moments for returns given prob good state = q ------------------
predictive_return_moments <- function(q, mu_g, var_g, mu_b, var_b) {
  mu <- q * mu_g + (1 - q) * mu_b
  # apply law of total variance: var(Y)=E[var(Y|X)]+var(E[Y|X])
  var <- q * var_g + (1 - q) * var_b + q * (1 - q) * (mu_g - mu_b)^2
  list(mean = mu, var = var)
}

## Mean–variance utility over wealth with returns ----------------------
## Wealth: W = W0 + x * R
## Utility: U = E[W] - 0.5 * gamma * Var(W)
## Optimal x*: = mu / (gamma * var)
## U* = W0 + mu^2 / (2 * gamma * var)
opt_utility_return <- function(mu, var, gamma, W0 = 0) {
  # No uncertainty -> no reason to take risk if we don't allow leverage/shorting
  if (var <= 0) return(W0)
  
  # Risk-neutral case: can invest up to W0, but no leverage
  if (gamma == 0) {
    if (mu <= 0) {
      # best is to stay in cash
      return(W0)
    } else {
      # invest all wealth in the risky asset
      x <- W0
      return(W0 + x * mu)   # Var term has zero weight
    }
  }
  
  # Risk-averse case: unconstrained optimum
  x_star <- mu / (gamma * var)
  
  # Enforce constraint: 0 <= x <= W0 (no shorting, no leverage)
  x_star <- max(0, min(x_star, W0))
  
  # Mean–variance utility with constrained optimal x
  W0 + x_star * mu - 0.5 * gamma * x_star^2 * var
}
simulate_order_flow <- function(informative, state_direction, alpha, lambda) {
  # total orders in the period
  total_orders <- rpois(1, lambda)
  
  # how many are "directional" vs "noise"
  directional_orders    <- rbinom(1, size = total_orders, prob = alpha)
  nondirectional_orders <- total_orders - directional_orders
  
  # sign of directional traders
  if (informative == 1L) {
    # informed: always in direction of state
    directional_sign <- state_direction    # +1L or -1L
  } else {
    # uninformed: same aggressiveness but random direction
    directional_sign <- sample(c(-1L, 1L), size = 1)
  }
  
  # directional volumes: all on one side
  dir_buys  <- ifelse(directional_sign ==  1L, directional_orders, 0L)
  dir_sells <- ifelse(directional_sign == -1L, directional_orders, 0L)
  
  # non-directional (noise) traders: random split of non-directional_orders
  noise_buys  <- rbinom(1, size = nondirectional_orders, prob = 0.5)
  noise_sells <- nondirectional_orders - noise_buys
  
  # totals
  buys      <- dir_buys  + noise_buys
  sells     <- dir_sells + noise_sells
  imbalance <- buys - sells
  
  list(
    buys      = buys,
    sells     = sells,
    imbalance = imbalance
  )
}


simulate_value_of_order_flow_returns <- function(
    n_paths,
    lambda,       # Poisson intensity
    alpha,        # prob order is directional/informed
    prob_good,    # prior P(good)
    informative,  # 1 = informed directional
    mu_g, var_g,  # good-state mean and variance (Normal)
    mu_b, var_b,  # bad-state mean and variance (Normal)
    gamma,        # risk aversion
    W0            # initial wealth
) {
  ## Prior (uninformed) predictive return moments under the mixture
  q0    <- prob_good
  pred0 <- predictive_return_moments(q0, mu_g, var_g, mu_b, var_b)
  mu0   <- pred0$mean
  var0  <- pred0$var
  
  ## Baseline optimal utility without observing order flow
  U0 <- opt_utility_return(mu0, var0, gamma, W0)
  
  ## Utilities with order-flow information
  U_inf <- numeric(n_paths)
  
  for (i in seq_len(n_paths)) {
    ## 1. Draw true state
    state_good      <- rbinom(1, size = 1, prob = prob_good)  # 1 = good, 0 = bad
    state_direction <- ifelse(state_good == 1L, 1L, -1L)
    
    ## 2. Simulate order flow given state
    of <- simulate_order_flow(informative, state_direction, alpha, lambda)
    b  <- of$buys
    s  <- of$sells
    
    ## 3. Posterior prob good from imbalance
    q <- p_post(alpha, b, s)
    
    ## 4. Predictive mean/var of returns conditional on q
    pred <- predictive_return_moments(q, mu_g, var_g, mu_b, var_b)
    mu   <- pred$mean
    var  <- pred$var
    
    ## 5. Mean–variance utility with info
    U_inf[i] <- opt_utility_return(mu, var, gamma, W0)
  }
  
  list(
    baseline_utility      = U0,
    mean_informed_utility = mean(U_inf),
    value_of_order_flow   = mean(U_inf) - U0
  )
}


results<-simulate_value_of_order_flow_returns(
  n_paths  = n_paths,
  lambda   = lambda,
  alpha    = alpha,
  prob_good= prob_good,
  informative = informative,
  mu_g     = mu_g,
  var_g    = var_g,
  mu_b     = mu_b,
  var_b    = var_b,
  gamma    = gamma,
  W0       = W0
)

set.seed(123)  # for reproducibility

# grid of risk aversion parameters
gamma_grid <- seq(0, 5, by = 0.5)

# risk aversion grid (including γ = 0)
gamma_grid <- seq(0, 5, by = 0.5)

value_vec <- sapply(gamma_grid, function(g) {
  res <- simulate_value_of_order_flow_returns(
    n_paths  = n_paths,
    lambda   = lambda,
    alpha    = alpha,
    prob_good= prob_good,
    informative = informative,
    mu_g     = mu_g,
    var_g    = var_g,
    mu_b     = mu_b,
    var_b    = var_b,
    gamma    = g,
    W0       = W0
  )
  res$value_of_order_flow
})

plot(gamma_grid, value_vec,
     type = "b",
     xlab = expression(gamma),
     ylab = "Value of order flow",
     main = "Value of Order-Flow Information vs Risk Aversion")
abline(h = 0, lty = 2)