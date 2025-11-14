library(manipulate)


# Probability of being in a good state 
# (as function of directional trading and order imbalance)
p <- function(alpha, b, s) {
  1 / (1 + ((1 - alpha) / (1 + alpha))^(b - s))
}

# expected return conditional on imbalance
ER <- function(alpha, b, s, rg, rb) {
  p(alpha, b, s) * rg + (1 - p(alpha, b, s)) * rb
}

# variance conditional on imbalance
varR <- function(alpha, b, s, rg, rb) {
  pr <- p(alpha, b, s)
  mu <- ER(alpha, b, s, rg, rb)
  pr * (rg - mu)^2 + (1 - pr) * (rb - mu)^2
}

# generate plot

manipulate(
  {
    im_vals <- seq(-3, 3, length.out = 400)
    b_vals  <- s + im_vals
    
    pr    <- p(alpha, b_vals, s)
    mu    <- ER(alpha, b_vals, s, rg, rb)
    v     <- varR(alpha, b_vals, s, rg, rb)
    ratio <- pmax(0, mu / v)
    
    # save & restore graphical parameters
    oldpar <- par(no.readonly = TRUE)
    on.exit(par(oldpar))
    par(mfrow = c(2, 2))
    
    # 1) p
    plot(im_vals, pr, type = "l",
         xlab = "im", ylab = "p",
         main = "p(alpha, s + im, s)")
    
    # 2) ER
    plot(im_vals, mu, type = "l",
         xlab = "im", ylab = "ER",
         main = "ER(alpha, s + im, s, rg, rb)")
    
    # 3) varR
    plot(im_vals, v, type = "l",
         xlab = "im", ylab = "varR",
         main = "varR(alpha, s + im, s, rg, rb)")
    
    # 4) ER / varR
    ok <- is.finite(ratio)
    plot(im_vals[ok], ratio[ok], type = "l",
         xlab = "im", ylab = "ER / varR",
         main = "ER / varR")
  },
  alpha = slider(0, 1,   initial = 0.3),
  rg    = slider(0.1, 0.2, initial = 0.2),
  rb    = slider(-0.1, 0,  initial = -0.05),
  s     = slider(0, 5,   initial = 0)
)