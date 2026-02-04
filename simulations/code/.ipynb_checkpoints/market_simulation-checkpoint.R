# market_simulation.R
# -----------------------------------
# Simulate price and order flow variables
# -----------------------------------

library(here)
library(rstudioapi)
setwd(dirname(getActiveDocumentContext()$path))
setwd("..")

source("code/config.R")


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
  outdir = "generated_data/plot_paths",
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

  # bar_xmin <- centers - w / 2
  # bar_xmax <- centers + w / 2

  bar_centers <- (1:N) + 0.5    # shifted one step forward
  bar_xmin <- bar_centers - w/2
  bar_xmax <- bar_centers + w/2

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
    layout(matrix(c(1, 2), nrow = 2),
           heights = c(1.2, 1))

    ## ------------------------------
    ## TOP PANEL: returns
    ## ------------------------------
    par(mar = c(1, 4, 4, 2), mgp = c(2.2, 0.6, 0))

    plot(price_x, ret_top,
         type = "n",
         xlab = "Time", ylab = "Return (%)",
         xlim = c(0, N + 1), ylim = price_ylim,
         xaxs = "i", xaxt = "n", yaxt = "s", las = 2)

    usr <- par("usr")
    ymin <- usr[3]
    ymax <- usr[4]

    # alternating gray bands
    for (t in 1:(N + 1)) {
      rect(t - 1, ymin,
           t, ymax,
           col = ifelse(t %% 2 == 0, gray(0.99), gray(0.9)),
           border = NA)
    }
    abline(v = 0:(N + 1), col = "gray85", lty = "dotted")

    # return line
    lines(price_x, ret_top_pct, type = "o", lwd = 2, col = "blue")

    # horizontal line at mu
    abline(h = mu_pct, col = "red", lty = 3, lwd = 1.5)

    # prediction dot at 17:00 (N+0.5)
    x_last <- tail(price_x, 1)
    y_last_pct <- tail(ret_top_pct, 1)
    x_pred <- N + 0.5

    segments(x_last, y_last_pct, x_pred, y_last_pct,
             lty = 2, col = "red")

    # fuzzy halo + solid core + ?
    points(x_pred, y_last_pct, pch = 16, col = rgb(1, 0, 0, 0.15), cex = 4)
    points(x_pred, y_last_pct, pch = 16, col = rgb(1, 0, 0, 0.25), cex = 2.8)
    points(x_pred, y_last_pct, pch = 16, col = rgb(1, 0, 0, 0.35), cex = 1.8)
    points(x_pred, y_last_pct, pch = 16, col = "red", cex = 1.3)
    # text(x_pred, y_last_pct, labels = "?", pos = 4,                   # <<<
    #      col = "red", cex = 1.5, font = 2)

    legend("top",
           horiz = TRUE,
           inset = c(0, -0.2),
           xpd = TRUE,
           legend = c(
             if (informative == 1) "Stock return" else "Stock return",
             "Buying pressure",
             "Selling pressure"
           ),
           col = c(
             "blue",
             rgb(0, 0.6, 0, 0.6),   # green
             rgb(0.8, 0, 0, 0.6)    # red
           ),
           lwd = c(2, NA, NA),
           pch = c(16, 15, 15),   # 15 = square
           pt.cex = c(1, 1.6, 1.6),
           lty = c(1, NA, NA),
           bty = "n")

    # <<< NEW: if no orderflow panel, show time axis on TOP panel
    if (!show_orderflow) {
      axis(1, at = label_pos, labels = time_labels,
           cex.axis = 0.9, las = 1)
    }

    # axis(1, at = label_pos, labels = time_labels,
    #      cex.axis = 0.9, las = 1)

    ## ------------------------------
    ## BOTTOM PANEL: single imbalance
    ## ------------------------------
    par(mar = c(4, 4, 2, 2), mgp = c(2.2, 0.6, 0))

    if (show_orderflow) {
      plot(NA, xlim = c(0, N + 1), ylim = orders_ylim,
           xaxs = "i", yaxs = "i",
           xlab = "Time", ylab = "Buy/sell pressure (%)",
           axes = FALSE)

      for (t in 1:(N + 1)) {
        rect(t - 1, orders_ylim[1],
             t, orders_ylim[2],
             col = ifelse(t %% 2 == 0, gray(0.99), gray(0.9)),
             border = NA)
      }

      abline(v = 0:(N + 1), col = "gray85", lty = "dotted")
      abline(h = 0, col = "gray60")

      # single bar per interval: green if positive, red if negative
      for (i in 1:N) {
        if (imb_pct[i] > 0) {                                 # <<< use imb_pct
          rect(bar_xmin[i], 0, bar_xmax[i], imb_pct[i],
               col = rgb(0, 0.6, 0, 0.6), border = NA)
        } else if (imb_pct[i] < 0) {
          rect(bar_xmin[i], 0, bar_xmax[i], imb_pct[i],
               col = rgb(0.8, 0, 0, 0.6), border = NA)
        }
      }

      axis(1, at = label_pos, labels = time_labels,
           cex.axis = 1, las = 1)
      axis(2, las = 2)
    } else {
      plot(NA,
           xlim = c(0, 1), ylim = c(0, 1),
           xaxs = "i", yaxs = "i",
           xlab = "", ylab = "",
           axes = FALSE)
      text(0.5, 0.5,
           "You do not have access to order flow data.",
           cex = 1.3)
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
      last_imbalance = 100 * tail(imb, 1)
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
    png_file = png_file
  ))
}

# 8319, 7316, 9479,
#
sim_specs <- data.frame(
  seed = c(22, 33, 49, 58, 60, 101, 174, 190, 154, 260, 320, 334, 418, 429, 489, 697),
  informative = c(1, 0, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0)
)

results <- list()

for (i in seq_len(nrow(sim_specs))) {
  s <- sim_specs$seed[i]
  inf <- sim_specs$informative[i]

  cat("Running: seed =", s, "| informative =", inf, "\n")

  results[[i]] <- list(
    noaccess = marketsim(
      N = config$N_plot,
      mu = config$mu,
      sigma = config$sigma,
      sigma_imb = config$sigma_imb,
      seed = s,
      informative = inf,
      plot = FALSE,
      save_png = TRUE,
      show_orderflow = FALSE,   # -> *_noaccess.png
      outdir = "generated_data/plot_paths"
    ),
    access = marketsim(
      N = config$N_plot,
      mu = config$mu,
      sigma = config$sigma,
      sigma_imb = config$sigma_imb,
      seed = s,
      informative = inf,
      plot = FALSE,
      save_png = TRUE,
      show_orderflow = TRUE,    # -> *_access.png
      outdir = "generated_data/plot_paths"
    )
  )
}


# optional naming
names(results) <- paste0(
  "seed_", sim_specs$seed,
  "_info_", sim_specs$informative
)

# -----------------------------------
# Consolidated results (choose which version to consolidate)
# -----------------------------------
# Set this to "access" or "noaccess"
# which_version <- "access"
 which_version <- "noaccess"



# After the for loop, create consolidated results
consolidated_results <- data.frame(
  seed = sim_specs$seed,
  informative = sim_specs$informative,
  next_return = numeric(nrow(sim_specs)),
  last_return = numeric(nrow(sim_specs)),
  last_imbalance = numeric(nrow(sim_specs))
)

# Fill in the results
for (i in seq_len(nrow(sim_specs))) {
  inf <- sim_specs$informative[i]



  # Get the appropriate last return based on informative setting
  res <- results[[i]][[which_version]]
  
  consolidated_results$next_return[i] <- res$next_return
  
  if (inf == 1) {
    consolidated_results$last_return[i] <- 100 * tail(res$data$r_pred, 1)
  } else {
    consolidated_results$last_return[i] <- 100 * tail(res$data$r, 1)
  }
  
  consolidated_results$last_imbalance[i] <- 100 * tail(res$data$imb, 1)
}

# Save the consolidated CSV
consolidated_file <- file.path("consolidated_simulation_results.csv")

write.csv(consolidated_results, consolidated_file, row.names = FALSE)

cat("\nConsolidated results saved to:", consolidated_file, "\n")
print(consolidated_results)