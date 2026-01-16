# market_simulation.R
# -----------------------------------
# Simulate price and order flow variables
# -----------------------------------

library(here)
library(rstudioapi)
setwd(dirname(getActiveDocumentContext()$path))
source("config.R")

marketsim <- function(
  N,     # number of half-hour intervals between 09:00 and 17:00
  mu,   # expected return
  sigma,   # std dev of baseline returns
  sigma_imb,   # std dev of imbalance (IID)
  match_var = TRUE,   # match Var(r_pred) = Var(r)
  seed = NULL,
  informative = 1,    # 1: plot r_pred, 0: plot iid r
  plot = TRUE,
  save_png = FALSE,
  outdir = "../plot_paths",
  save_excel = TRUE,
  show_orderflow = TRUE # save next return
) {
  if (!is.null(seed)) set.seed(seed)
  if (N < 2) stop("N must be >= 2")
  if (N != 16) warning("For 30-min steps from 09:00 to 17:00, N should be 16.")

  ## ----------------------------
  ## 1) Simulate processes
  ## ----------------------------
  # Baseline iid returns: r_t = mu + eps1_t
  eps1 <- rnorm(N, mean = 0, sd = sigma)
  r <- mu + eps1

  # IID imbalance: imb_t ~ N(0, sigma_imb^2)
  imb <- rnorm(N + 1, mean = 0, sd = sigma_imb)

  # Predictable returns: r_pred_t = mu + imb_t + eps2_t
  if (match_var) {
    if (sigma_imb >= sigma) {
      stop("sigma_imb must be < sigma to match variances.")
    }
    sigma_eps <- sqrt(sigma^2 - sigma_imb^2)
  } else {
    sigma_eps <- sigma
  }
  eps2 <- rnorm(N, mean = 0, sd = sigma_eps)
  r_pred <- mu + imb[1:N] + eps2
  imb <- imb[2:(N + 1)]

  ret_top <- if (informative == 1) r_pred else r

  ## --- NEW: percentage versions used only for plotting ---  # <<<
  ret_top_pct <- 100 * ret_top                              # <<<
  mu_pct <- 100 * mu                                   # <<<
  imb_pct <- 100 * imb                                  # <<<

  ## ----------------------------
  ## 2) Geometry for imbalance bars
  ## ----------------------------
  centers <- (1:N) - 0.5        # centers of intervals [t-1,t]
  w <- 0.5                # bar width

  bar_xmin <- centers - w / 2
  bar_xmax <- centers + w / 2

  orders_ylim <- range(imb_pct) * 1.15
  if (diff(orders_ylim) == 0) orders_ylim <- orders_ylim + c(-0.01, 0.01)

  price_ylim <- range(c(ret_top_pct, mu_pct)) * 1.1

  ## ----------------------------
  ## 3) Time labels: 09:00–17:00 every 30min
  ## ----------------------------
  times <- seq(from = as.POSIXct("09:00", format = "%H:%M"),
               to = as.POSIXct("17:00", format = "%H:%M"),
               by = "30 min")
  time_labels <- format(times, "%H:%M")

  price_x <- centers              # same centers
  label_pos <- c(price_x, N + 0.5)  # extra tick at 17:00

  ## ----------------------------
  ## 4) Plot helper (draw once on current device)
  ## ----------------------------
  draw_plot <- function() {
    ## Single panel only
    par(mar = c(4, 4, 4, 4), mgp = c(2.2, 0.6, 0))

    x_ret <- price_x
    x_imb <- price_x + 1   # shift imbalance forward by 1 interval (change to +0.5 if you prefer)

    ret_ylim <- c(-25, 60)

    imb_ylim <- range(imb_pct) * 1.15
    if (diff(imb_ylim) == 0) imb_ylim <- imb_ylim + c(-0.01, 0.01)

    ## Base plot: RETURNS (left axis)
    plot(x_ret, ret_top_pct,
         type = "n",
         xlab = "Time", ylab = "Return (%)",
         xlim = c(0, N + 1), ylim = ret_ylim,
         xaxs = "i", xaxt = "n", yaxt = "s", las = 2)

    usr <- par("usr")
    ymin <- usr[3]; ymax <- usr[4]

    # alternating gray bands
    for (t in 1:(N + 1)) {
      rect(t - 1, ymin, t, ymax,
           col = ifelse(t %% 2 == 0, gray(0.99), gray(0.9)),
           border = NA)
    }
    abline(v = 0:(N + 1), col = "gray85", lty = "dotted")

    # return line
    lines(x_ret, ret_top_pct, type = "o", lwd = 2, col = "blue")

    # prediction dot at 17:00 (N+0.5)
    x_last <- tail(x_ret, 1)
    y_last_pct <- tail(ret_top_pct, 1)
    x_pred <- N + 0.5

    segments(x_last, y_last_pct, x_pred, y_last_pct, lty = 2, col = "red")
    points(x_pred, y_last_pct, pch = 16, col = rgb(1, 0, 0, 0.15), cex = 4)
    points(x_pred, y_last_pct, pch = 16, col = rgb(1, 0, 0, 0.25), cex = 2.8)
    points(x_pred, y_last_pct, pch = 16, col = rgb(1, 0, 0, 0.35), cex = 1.8)
    points(x_pred, y_last_pct, pch = 16, col = "red", cex = 1.3)

    # time axis
    axis(1, at = label_pos, labels = time_labels, cex.axis = 1, las = 1)

    ## Overlay imbalance only if access is allowed
    ## Overlay imbalance only if access is allowed
    if (show_orderflow) {
      par(new = TRUE)
      plot(x_imb, imb_pct,
           type = "l", lwd = 2, col = "red",
           axes = FALSE, xlab = "", ylab = "",
           xlim = c(0, N + 1), ylim = imb_ylim,
           xaxs = "i")

      axis(4, las = 2)
      mtext("Buy/sell pressure (%)", side = 4, line = 2.5)

      legend("top",
             horiz = TRUE,
             inset = c(0, -0.1),
             xpd = TRUE,
             bty = "n",
             legend = c("Stock return", "Buy/sell pressure"),
             col = c("blue", "red"),
             lwd = c(2, 2),
             lty = c(1, 1),
             pch = c(16, NA))
    } else {
      ## Boxed message inside the plot area (no overlap with legend)
      usr <- par("usr")
      dx <- usr[2] - usr[1]
      dy <- usr[4] - usr[3]

      x0 <- usr[1] + 0.02 * dx
      x1 <- usr[1] + 0.62 * dx
      y1 <- usr[4] - 0.03 * dy
      y0 <- usr[4] - 0.12 * dy

      rect(x0, y0, x1, y1, col = rgb(1, 1, 1, 0.85), border = "gray40")
      text((x0 + x1) / 2, (y0 + y1) / 2,
           "You do not have access to order flow data.",
           cex = 1.05, font = 2)

      legend("top",
             horiz = TRUE,
             inset = c(0, -0.1),
             xpd = TRUE,
             bty = "n",
             legend = "Stock return",
             col = "blue",
             lwd = 2,
             lty = 1,
             pch = 16)
    }
  }

  ## ----------------------------
  ## 5) Device logic
  ## ----------------------------
  if (plot) {
    draw_plot()
  }

  png_file <- NULL
  if (save_png) {
    if (!dir.exists(outdir)) dir.create(outdir, recursive = TRUE)
    access_suffix <- if (show_orderflow) "access" else "noaccess"   # <<< NEW
    png_file <- file.path(
      outdir,
      sprintf("sim_seed-%s_info-%d_%s.png",                       # <<< NEW
              ifelse(is.null(seed), "NA", as.character(seed)),
              informative,
              access_suffix)                                      # <<< NEW
    )

    if (plot) {
      dev.copy(png, png_file, width = 1800, height = 800, res = 150)
      dev.off()
    } else {
      png(png_file, width = 1800, height = 800, res = 150)
      draw_plot()
      dev.off()
    }
  }

  ## ----------------------------
  ## 6) Next stock return + Excel-readable file
  ## ----------------------------

  next_return <- if (informative == 1)
    mu +
      tail(imb, 1) +
      rnorm(1, mean = 0, sd = sigma_eps)
  else
    mu + rnorm(1, mean = 0, sd = sigma)

  excel_file <- NULL
  if (save_excel) {
    if (!dir.exists(outdir)) dir.create(outdir, recursive = TRUE)
    excel_file <- file.path(
      outdir,
      sprintf("sim_seed-%s_info-%d_return.csv",
              ifelse(is.null(seed), "NA", as.character(seed)),
              informative)
    )

    next_df <- data.frame(
      next_return = 100 * next_return,
      last_imbalance_1 = 100 * imb[N],
      last_imbalance_2 = 100 * imb[N - 1],
      last_imbalance_3 = 100 * imb[N - 2],
      last_return_1 = 100 * ret_top[N],
      last_return_2 = 100 * ret_top[N - 1],
      last_return_3 = 100 * ret_top[N - 2]
    )

    write.csv(next_df, excel_file, row.names = FALSE)
  }

  invisible(list(
    data = data.frame(
      t = 1:N,
      r = r,
      r_pred = r_pred,
      imb = imb
    ),
    next_return = 100 * next_return,
    last_imbalances = 100 * imb[(N - 2):N],
    last_returns = 100 * ret_top[(N - 2):N],
    png_file = png_file
  ))
}

# 8319, 7316, 9479,
#
sim_specs <- data.frame(
  seed = c(22, 33, 49, 58, 60, 101, 174, 190, 154, 260, 320, 334, 418, 429, 489, 697),
  informative = c(1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0)
)

results <- list()

for (i in seq_len(nrow(sim_specs))) {
  s <- sim_specs$seed[i]
  inf <- sim_specs$informative[i]

  cat("Running: seed =", s, "| informative =", inf, "\n")

  results[[i]] <- marketsim(
    N = config$N_plot,
    mu = config$mu,
    sigma = config$sigma,
    sigma_imb = config$sigma_imb,
    seed = s,
    informative = inf,
    plot = TRUE,
    save_png = TRUE,
    show_orderflow = FALSE,
    outdir = "../plot_paths"
  )
}


# optional naming
names(results) <- paste0(
  "seed_", sim_specs$seed,
  "_info_", sim_specs$informative
)


# res <- marketsim(
#   N = config$N_plot,
#   mu = config$mu,
#   sigma = config$sigma,
#   sigma_imb = config$sigma_imb,
#   seed = 11377,
#   informative = 1,  # or 1 for r_pred
#   plot = TRUE,
#   save_png = TRUE,
#   outdir = "../plots"
# )

# After the for loop, create consolidated results
consolidated_results <- data.frame(
  seed = sim_specs$seed,
  informative = sim_specs$informative,
  next_return = numeric(nrow(sim_specs)),
  last_return_1 = numeric(nrow(sim_specs)),
  last_return_2 = numeric(nrow(sim_specs)),
  last_return_3 = numeric(nrow(sim_specs)),
  last_imbalance_1 = numeric(nrow(sim_specs)),
  last_imbalance_2 = numeric(nrow(sim_specs)),
  last_imbalance_3 = numeric(nrow(sim_specs))
)

# Fill in the results
for (i in seq_len(nrow(sim_specs))) {
  consolidated_results$next_return[i] <- results[[i]]$next_return
  consolidated_results$last_return_1[i] <- results[[i]]$last_returns[3]
  consolidated_results$last_return_2[i] <- results[[i]]$last_returns[2]
  consolidated_results$last_return_3[i] <- results[[i]]$last_returns[1]
  consolidated_results$last_imbalance_1[i] <- results[[i]]$last_imbalances[3]
  consolidated_results$last_imbalance_2[i] <- results[[i]]$last_imbalances[2]
  consolidated_results$last_imbalance_3[i] <- results[[i]]$last_imbalances[1]
}

# Save the consolidated CSV
consolidated_file <- file.path("consolidated_simulation_results.csv")
write.csv(consolidated_results, consolidated_file, row.names = FALSE)

cat("\nConsolidated results saved to:", consolidated_file, "\n")
print(consolidated_results)