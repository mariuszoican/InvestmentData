### Code to simulate price and order flow
### -------------------------------------

# use local folder
library(here)
library(rstudioapi)
setwd(dirname(getActiveDocumentContext()$path))

# Parameters
S0 <- 100         # initial stock price
N <- 16           # number of periods in time series
steps <- c(5, 10, 15)  # possible move sizes
lambda <- 8 # order arrival rate per period
alpha <- 1 # fraction of informed traders

# set seed for reproducibility
seed <- 448
set.seed(seed) 

# initialize price vector
S <- numeric(N + 1)
S[1] <- S0 # first price
move_direction <- integer(N) # move directions, could be +1 or -1
move_size <- integer(N) # can be 5, 10, or 15.

# simulate prices
for (t in 1:N) {
  move_size[t] <- sample(steps, 1)
  move_direction[t] <- sample(c(-1, 1), 1)
  S[t + 1] <- S[t] + move_direction[t] * move_size[t]
}

# simulate order flow
total_orders      <- rpois(N, lambda) # total orders per period
informed_orders   <- rbinom(N, size = total_orders, prob = alpha) # how many informed?
uninformed_orders <- total_orders - informed_orders               # how many uninformed?

# Informed: all trade in the direction of the next move
informed_buys  <- ifelse(move_direction ==  1L, informed_orders, 0L)
informed_sells <- ifelse(move_direction == -1L, informed_orders, 0L)

# Uninformed: random buys/sells
uninformed_buys  <- rbinom(N, size = uninformed_orders, prob = 0.5)
uninformed_sells <- uninformed_orders - uninformed_buys

# Totals per period
buys  <- informed_buys  + uninformed_buys
sells <- informed_sells + uninformed_sells

# show short stubs instead of true zeros if order flow is zero on one side
stub <- 0.2
buys_disp  <- ifelse(buys  == 0, stub, buys)
sells_disp <- ifelse(sells == 0, stub, sells)

## ----------------------------
## Geometry for bars (predictive: between t-1 and t)
## ----------------------------
centers <- (1:N) - 0.5      # each period [t-1, t] centered at t-0.5
gap <- 0.12
w   <- 0.35

buy_xmin  <- centers - gap/2 - w
buy_xmax  <- centers - gap/2
sell_xmin <- centers + gap/2
sell_xmax <- centers + gap/2 + w

# y-limits for order flow: buys positive, sells negative
orders_ylim <- c(-max(sells_disp) * 1.15,
                 max(buys_disp) * 1.15)
price_ylim  <- range(S)

## ----------------------------
## Time labels: 09:00–17:00 every 30min
## ----------------------------
times <- seq(from = as.POSIXct("09:00", format = "%H:%M"),
             to   = as.POSIXct("17:00", format = "%H:%M"),
             by   = "30 min")
time_labels <- format(times, "%H:%M")

# positions: 09:00..16:30 at centers 0.5..15.5, 17:00 at 16.5
price_x    <- seq(0.5, N - 0.5, by = 1)    # 16 real points
label_pos  <- c(price_x, N + 0.5)          # add 17:00 at 16.5

## ----------------------------
## Plot
## ----------------------------

if (!is.null(dev.list())) dev.off()

if (!dir.exists("plots")) {
  dir.create("plots", recursive = TRUE)
  message("Created plots directory.")
} else {
  message("Directory exists.")
}

fname <- sprintf("plots/pricesimulation_seed_%d_alpha_%d.png",
                 seed, as.integer(100 * alpha))

### Code to simulate price and order flow
### -------------------------------------

# use local folder
library(here)
library(rstudioapi)
setwd(dirname(getActiveDocumentContext()$path))

# Parameters
S0 <- 100         # initial stock price
N <- 16           # number of periods in time series
steps <- c(5, 10, 15)  # possible move sizes
lambda <- 8 # order arrival rate per period
alpha <- 1 # fraction of informed traders

# set seed for reproducibility
seed <- 448
set.seed(seed) 

# initialize price vector
S <- numeric(N + 1)
S[1] <- S0 # first price
move_direction <- integer(N) # move directions, could be +1 or -1
move_size <- integer(N) # can be 5, 10, or 15.

# simulate prices
for (t in 1:N) {
  move_size[t] <- sample(steps, 1)
  move_direction[t] <- sample(c(-1, 1), 1)
  S[t + 1] <- S[t] + move_direction[t] * move_size[t]
}

# simulate order flow
total_orders      <- rpois(N, lambda) # total orders per period
informed_orders   <- rbinom(N, size = total_orders, prob = alpha) # how many informed?
uninformed_orders <- total_orders - informed_orders               # how many uninformed?

# Informed: all trade in the direction of the next move
informed_buys  <- ifelse(move_direction ==  1L, informed_orders, 0L)
informed_sells <- ifelse(move_direction == -1L, informed_orders, 0L)

# Uninformed: random buys/sells
uninformed_buys  <- rbinom(N, size = uninformed_orders, prob = 0.5)
uninformed_sells <- uninformed_orders - uninformed_buys

# Totals per period
buys  <- informed_buys  + uninformed_buys
sells <- informed_sells + uninformed_sells

# show short stubs instead of true zeros if order flow is zero on one side
stub <- 0.5
buys_disp  <- pmax(buys,  stub)
sells_disp <- pmax(sells, stub)   # will be plotted as negative

## ----------------------------
## Geometry for bars (predictive: between t-1 and t)
## ----------------------------
centers <- (1:N) - 0.5      # each period [t-1, t] centered at t-0.5
gap <- 0.12
w   <- 0.35

buy_xmin  <- centers - gap/2 - w
buy_xmax  <- centers - gap/2
sell_xmin <- centers + gap/2
sell_xmax <- centers + gap/2 + w

# y-limits for order flow: buys positive, sells negative
orders_ylim <- c(-max(sells_disp) * 1.15,
                 max(buys_disp) * 1.15)
price_ylim  <- c(min(S)*0.9, max(S)*1.1)

## ----------------------------
## Time labels: 09:00–17:00 every 30min
## ----------------------------
times <- seq(from = as.POSIXct("09:00", format = "%H:%M"),
             to   = as.POSIXct("17:00", format = "%H:%M"),
             by   = "30 min")
time_labels <- format(times, "%H:%M")

# positions: 09:00..16:30 at centers 0.5..15.5, 17:00 at 16.5
price_x    <- seq(0.5, N - 0.5, by = 1)    # 16 real points
label_pos  <- c(price_x, N + 0.5)          # add 17:00 at 16.5

## ----------------------------
## Plot (two panels)
## ----------------------------

if (!is.null(dev.list())) dev.off()

if (!dir.exists("plots")) {
  dir.create("plots", recursive = TRUE)
  message("Created plots directory.")
} else {
  message("Directory exists.")
}

fname <- sprintf("plots/pricesimulation_seed_%d_alpha_%d.png",
                 seed, as.integer(100 * alpha))

# Layout: price panel tall, order-flow panel short
layout(matrix(c(1, 2), nrow = 2),
       heights = c(1.2, 1))   # price gets 3x the height of order flow


## ------------------------------
## 1) TOP PANEL: PRICE (with gray bands)
## ------------------------------
par(mar = c(1, 4, 4, 2), mgp = c(2.2, 0.6, 0))

# Empty canvas first
plot(price_x, S[1:N], type = "o", lwd = 2, col = "blue",
     xlab = "Time", ylab = "Stock price",
     xlim = c(0, N + 1), ylim = price_ylim,
     xaxs = "i", xaxt = "n", yaxt = "s")

# Get actual y-limits of this panel
usr <- par("usr")          # c(xmin, xmax, ymin, ymax)
ymin <- usr[3]
ymax <- usr[4]

# Alternating gray bands across full vertical range
for (t in 1:(N + 1)) {
  rect(t - 1, ymin,
       t,     ymax,
       col = ifelse(t %% 2 == 0, gray(0.99), gray(0.9)),
       border = NA)
}

# Shared vertical grid (same as bottom panel)
abline(v = 0:(N + 1), col = "gray85", lty = "dotted")

# --- Price line on top, aligned with bar centers ---
# price_x = 0.5, 1.5, ..., N-0.5
# S[1:N]  = price for intervals [0,1], [1,2], ..., [N-1,N]
lines(price_x, S[1:N], type = "o", lwd = 2, col = "blue")

# --- Prediction at 17:00, horizontal from last price ---
x_last  <- tail(price_x, 1)   # 16:30 position (15.5)
y_last  <- S[N]               # price at last real half-hour (interval N)
x_pred  <- N + 0.5            # 17:00 at 16.5

segments(x_last, y_last, x_pred, y_last,
         lty = 2, col = "red")

# fuzzy halo
points(x_pred, y_last, pch = 16, col = rgb(1, 0, 0, 0.15), cex = 4)
points(x_pred, y_last, pch = 16, col = rgb(1, 0, 0, 0.25), cex = 2.8)
points(x_pred, y_last, pch = 16, col = rgb(1, 0, 0, 0.35), cex = 1.8)

# solid core
points(x_pred, y_last, pch = 16, col = "red", cex = 1.3)

# question mark
text(x_pred, y_last, labels = "?", pos = 4,
     col = "red", cex = 1.5, font = 2)

# Legend at top, horizontal, like a title bar
legend("top",
       horiz = TRUE,
       inset = c(0, -0.2),
       xpd   = TRUE,
       legend = c("Price", "Buy orders", "Sell orders"),
       col    = c("blue", rgb(0, 0.6, 0, 0.6), rgb(0.8, 0, 0, 0.6)),
       lwd    = c(2, NA, NA),
       pch    = c(16, 15, 15),
       pt.cex = c(1, 1.6, 1.6),
       lty    = c(1, NA, NA),
       bty    = "n")

## ------------------------------
## 2) BOTTOM PANEL: ORDER FLOW (narrower)
## ------------------------------
#par(mar = c(1, 4, 4, 2), mgp = c(2.2, 0.6, 0))
par(mar = c(4, 4, 2, 2), mgp = c(2.2, 0.6, 0))

plot(NA, xlim = c(0, N + 1), ylim = orders_ylim,
     xaxs = "i", yaxs = "i",
     xlab = "Time", ylab = "Order volume",
     axes = FALSE)

# Alternating gray bands across full order-flow range
for (t in 1:(N + 1)) {
  rect(t - 1, orders_ylim[1],
       t,     orders_ylim[2],
       col = ifelse(t %% 2 == 0, gray(0.99), gray(0.9)),
       border = NA)
}

# Shared vertical grid (aligned with top panel)
abline(v = 0:(N + 1), col = "gray85", lty = "dotted")

# Zero line
abline(h = 0, col = "gray60")

# Buy bars positive, sell bars negative
rect(buy_xmin,  0, buy_xmax,  buys_disp,
     col = rgb(0, 0.6, 0, 0.6), border = NA)
rect(sell_xmin, 0, sell_xmax, -sells_disp,
     col = rgb(0.8, 0, 0, 0.6), border = NA)

# Axes
axis(2, las = 1)
#axis(4, las = 1)

# Common x-axis (only here, bottom panel)
axis(1, at = label_pos, labels = time_labels,
     cex.axis = 1, las = 1)

## ----------------------------
## Save to PNG
## ----------------------------
dev.copy(png, fname,
         width = 1800, height = 800, res = 150)
dev.off()