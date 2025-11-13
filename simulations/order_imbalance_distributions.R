library(here)
library(rstudioapi)
setwd(dirname(getActiveDocumentContext()$path))


source("market_sim.R")   # load simulation function

n_rep <- 10000
N     <- 16   # number of periods per simulation

# Containers for results
imbal_inf   <- numeric(n_rep * N)
imbal_uninf <- numeric(n_rep * N)
ret_inf     <- numeric(n_rep * N)
ret_uninf   <- numeric(n_rep * N)

idx <- 1

##########################################
## Informative order flow simulations
##########################################

for (k in 1:n_rep) {
  sim <- simulate_market(
    seed        = sample.int(1e9, 1),
    alpha       = 0.3,
    informative = 1,
    plot        = FALSE,
    save_png    = FALSE
  )
  
  imbal_inf[idx:(idx+N-1)] <- sim$imbalance
  
  # If your function returns prices S, compute returns
  ret_inf[idx:(idx+N-1)]   <- diff(sim$S)
  
  idx <- idx + N
}



print(ks.test(imbal_inf, imbal_uninf))

##########################################
## Uninformative order flow simulations
##########################################

idx <- 1

for (k in 1:n_rep) {
  sim <- simulate_market(
    seed        = sample.int(1e9, 1),
    alpha       = 0.3,
    informative = 0,
    plot        = FALSE,
    save_png    = FALSE
  )
  
  imbal_uninf[idx:(idx+N-1)] <- sim$imbalance
  ret_uninf[idx:(idx+N-1)]   <- diff(sim$S)
  
  idx <- idx + N
}

##########################################
## Compute summary statistics
##########################################

mean_inf <- mean(imbal_inf)
var_inf  <- var(imbal_inf)
cor_inf  <- cor(imbal_inf, ret_inf)

mean_un  <- mean(imbal_uninf)
var_un   <- var(imbal_uninf)
cor_un   <- cor(imbal_uninf, ret_uninf)

ks_res  <- ks.test(imbal_inf, imbal_uninf)
ks_stat <- as.numeric(ks_res$statistic)
ks_p    <- ks_res$p.value

##########################################
## Choose where to save the LaTeX file
##########################################

out_dir  <- "../tables"              # folder name
out_file <- "imbalance_results.tex"

if (!dir.exists(out_dir)) dir.create(out_dir, recursive = TRUE)

path <- file.path(out_dir, out_file)

##########################################
## Build LaTeX table as a single string
##########################################

latex_table <- sprintf("
\\begin{table}[ht]
\\centering
\\begin{tabular}{lcc}
\\hline
\\textbf{Round} & \\textbf{Informative} & \\textbf{Uninformative} \\\\
\\hline
Mean order imbalance      & %.4f & %.4f \\\\
Variance order imbalance    & %.4f & %.4f \\\\
Correlation order imbalance-return & %.4f & %.4f \\\\
KS statistic          & \\multicolumn{2}{c}{%.4f} \\\\
KS p-value            & \\multicolumn{2}{c}{%.4g} \\\\
\\hline
\\end{tabular}
\\caption{Comparison of imbalance distributions and their relationship to returns under informative and uninformative order flow.}
\\label{tab:imbalance_comparison}
\\end{table}
",
                       mean_inf, mean_un,
                       var_inf, var_un,
                       cor_inf, cor_un,
                       ks_stat, ks_p
)

##########################################
## Write to file
##########################################

writeLines(latex_table, path)

cat("Saved LaTeX table to:", path, "\n\n")

##########################################
## Also print to console
##########################################

cat(latex_table)