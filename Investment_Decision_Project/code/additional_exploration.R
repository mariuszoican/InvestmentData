# additional_exploration.R

library(tidyverse)
library(lfe)
library(stargazer)
library(fixest)
library(modelsummary)
library(rstudioapi)
library(ggplot2)
library(ggfixest)
library(cowplot)
library(latex2exp)

# Load data
setwd(dirname(getActiveDocumentContext()$path))
df <- read.csv("../generated_data/processed_panels.csv")

# Save raw versions before standardizing
df <- df %>%
  mutate(
    round_number_raw = round_number,
    age_raw = age,
    fin_quiz_raw = fin_quiz,
    overconfidence_raw = overconfidence,
    risk_aversion_raw = risk_aversion,
    last_imbalance_1_raw = last_imbalance_1,
    last_return_1_raw = last_return_1,
    imb_difference_raw = imb_difference,
    return_difference_raw = return_difference
  )

# Standardize
df <- df %>%
  mutate(
    across(
      c(round_number, age, fin_quiz, overconfidence, risk_aversion,
        last_imbalance_1, last_return_1, imb_difference, return_difference),
      ~(. - mean(., na.rm = TRUE)) / sd(., na.rm = TRUE)
    )
  )

# Create variables
df <- df %>%
  mutate(
    correct_belief = as.integer(belief_informative == informative),
    pay_choice = treated * pay_for_data,
    choice_imbalance = pay_choice * last_imbalance_1,
    paid_informative = paid_round * informative,
    paid_uninformative = paid_round * (1 - informative),
    paid_belief_informative = paid_round * belief_informative,
    paid_belief_uninformative = paid_round * (1 - belief_informative),
    paid_informative_imbalance = paid_round *
      belief_informative *
      last_imbalance_1,
    paid_uninformative_imbalance = paid_round *
      (1 - belief_informative) *
      last_imbalance_1,
    paid_imbalance = paid_round * last_imbalance_1,
    belief_informative_imbalance = belief_informative * last_imbalance_1,
    rf_x_paid = return_forecast * paid_round,
    rf_x_unpaid = return_forecast * (1 - paid_round),
    z_x_paid = last_imbalance_1 * paid_round,
    z_x_unpaid = last_imbalance_1 * (1 - paid_round),
    r_x_paid = last_return_1 * paid_round,
    correct_forecast = 15 + last_imbalance_1_raw * informative,
    forecast_error = abs(return_forecast - correct_forecast)
  ) %>%
  group_by(participant_code) %>%
  mutate(share_correct = mean(correct_belief, na.rm = TRUE)) %>%
  ungroup()

controls <- c("overconfidence", "fin_quiz", "gender_female", "age",
              "finance_course", "trading_experience", "risk_aversion")
controls_str <- paste(controls, collapse = " + ")

setFixest_dict(c(
  treated = "Treated",
  return_forecast = "Return forecast",
  paid_imbalance = "Paid $\\times$ Imbalance",
  paid_informative = "Paid $\\times$ Informative",
  paid_uninformative = "Paid $\\times$ Not informative",
  last_imbalance_1 = "Last imbalance",
  pay_choice = "Choose to pay",
  choice_imbalance = "Choose to pay $\\times$ Imbalance",
  paid_round = "Paid round",
  informative = "Informative round",
  last_return_1 = "Last return",
  overconfidence = "Overconfidence",
  fin_quiz = "Financial quiz",
  rf_x_paid = "Return forecast $\\times$ Paid round",
  r_x_paid = "Last return $\\times$ Paid round",
  investment_amount = "Investment amount (E\\$)",
  investment_share = "Investment share (\\%)",
  gender_female = "Female",
  age = "Age",
  finance_course = "Finance course",
  trading_experience = "Trading experience",
  high_education = "College education",
  risk_aversion = "Risk aversion",
  participant_code = "Participant",
  round_number = "Round number",
  belief_informative = "Belief informative",
  share_correct = "Share correct predictions",
  forecast_error = "Forecast error (\\%)"
))

# ============================================================
# Table 2: Forecast equations
# ============================================================

for1 <- feols(
  as.formula(paste(
    "forecast_error ~ ",
    "paid_round + treated +",
    "pay_choice + round_number +",
    "last_return_1 + last_imbalance_1 +",
    controls_str
  )),
  data = subset(df, informative == 0),
  cluster = ~participant_code + round_number
)


for2 <- feols(
  as.formula(paste(
    "forecast_error ~ ",
    "paid_round + treated +",
    "pay_choice + round_number +",
    "last_return_1 + last_imbalance_1"
  )),
  data = subset(df, informative == 0),
  cluster = ~participant_code + round_number
)

for3 <- feols(
  as.formula(paste(
    "forecast_error ~ ",
    "paid_round + treated +",
    "pay_choice + round_number +",
    "last_return_1 + last_imbalance_1 +",
    controls_str
  )),
  data = subset(df, (informative == 0) & (fin_quiz > 0)),
  cluster = ~participant_code + round_number
)


for4 <- feols(
  as.formula(paste(
    "forecast_error ~ ",
    "paid_round + treated +",
    "pay_choice + round_number +",
    "last_return_1 + last_imbalance_1"
  )),
  data = subset(df, (informative == 0) & (fin_quiz > 0)),
  cluster = ~participant_code + round_number
)

for5 <- feols(
  as.formula(paste(
    "forecast_error ~ ",
    "paid_round + treated +",
    "pay_choice + round_number +",
    "last_return_1 + last_imbalance_1 +",
    controls_str
  )),
  data = subset(df, (informative == 0) & (fin_quiz <= 0)),
  cluster = ~participant_code + round_number
)


for6 <- feols(
  as.formula(paste(
    "forecast_error ~ ",
    "paid_round + treated +",
    "pay_choice + round_number +",
    "last_return_1 + last_imbalance_1"
  )),
  data = subset(df, (informative == 0) & (fin_quiz <= 0)),
  cluster = ~participant_code + round_number
)

for_tex <- etable(
  for1, for2, for3, for4, for5, for6,
  title = "Payment for data and return forecast errors",
  tex = TRUE,
  digits = "r2",
  digits.stats = "r2",
  depvar = TRUE,
  order = c(
    "Paid round", "Treated",
    "Choose to pay",
    "Last imbalance",
    "Last return",
    "Overconfidence", "Financial quiz", "Female", "Age",
    "Finance course", "Trading experience", "Risk aversion"
  ),
  headers = list("All quiz scores" = 2, "High quiz scores" = 2, "Low quiz scores" = 2),
  fitstat = c("n", "r2")
)
writeLines(for_tex, "../tables/forecastserror_table.tex")

# ============================================================
# Table 3b: IV with Heckman selection correction
# ============================================================

# Step 1a: Full probit (for columns with controls)
sel_probit <- glm(
  belief_informative ~ paid_uninformative +
    paid_round +
    treated +
    informative +
    pay_choice +
    round_number +
    last_return_1 +
    last_imbalance_1 +
    overconfidence +
    fin_quiz +
    gender_female +
    age +
    finance_course +
    trading_experience +
    risk_aversion,
  data = df,
  family = binomial(link = "probit")
)

xb <- predict(sel_probit, newdata = df, type = "link")
df$imr <- dnorm(xb) / pnorm(xb)

# Step 1b: Lean probit (for columns without controls)
sel_probit_lean <- glm(
  belief_informative ~ paid_uninformative +
    paid_round +
    treated +
    informative +
    pay_choice +
    round_number +
    last_return_1 +
    last_imbalance_1,
  data = df,
  family = binomial(link = "probit")
)

xb_lean <- predict(sel_probit_lean, newdata = df, type = "link")
df$imr_lean <- dnorm(xb_lean) / pnorm(xb_lean)

# Step 2: IV regressions — full controls use imr, no controls use imr_lean

# All participants
iv1h <- feols(
  as.formula(paste(
    "investment_share ~ treated + paid_round + pay_choice + round_number +",
    "last_return_1 + r_x_paid + imr +",
    controls_str,
    "| 0 | return_forecast + rf_x_paid ~ last_imbalance_1 + z_x_paid"
  )),
  data = subset(df, belief_informative == 1),
  cluster = ~participant_code + round_number
)

iv2h <- feols(
  as.formula(paste(
    "investment_share ~ treated + paid_round + pay_choice + round_number +",
    "last_return_1 + r_x_paid + imr_lean",
    "| 0 | return_forecast + rf_x_paid ~ last_imbalance_1 + z_x_paid"
  )),
  data = subset(df, belief_informative == 1),
  cluster = ~participant_code + round_number
)

# High quiz
iv3h <- feols(
  as.formula(paste(
    "investment_share ~ treated + paid_round + pay_choice + round_number +",
    "last_return_1 + r_x_paid + imr +",
    controls_str,
    "| 0 | return_forecast + rf_x_paid ~ last_imbalance_1 + z_x_paid"
  )),
  data = subset(df, (belief_informative == 1) & (fin_quiz > 0)),
  cluster = ~participant_code + round_number
)

iv4h <- feols(
  as.formula(paste(
    "investment_share ~ treated + paid_round + pay_choice + round_number +",
    "last_return_1 + r_x_paid + imr_lean",
    "| 0 | return_forecast + rf_x_paid ~ last_imbalance_1 + z_x_paid"
  )),
  data = subset(df, (belief_informative == 1) & (fin_quiz > 0)),
  cluster = ~participant_code + round_number
)

# Low quiz
iv5h <- feols(
  as.formula(paste(
    "investment_share ~ treated + paid_round + pay_choice + round_number +",
    "last_return_1 + r_x_paid + imr +",
    controls_str,
    "| 0 | return_forecast + rf_x_paid ~ last_imbalance_1 + z_x_paid"
  )),
  data = subset(df, (belief_informative == 1) & (fin_quiz <= 0)),
  cluster = ~participant_code + round_number
)

iv6h <- feols(
  as.formula(paste(
    "investment_share ~ treated + paid_round + pay_choice + round_number +",
    "last_return_1 + r_x_paid + imr_lean",
    "| 0 | return_forecast + rf_x_paid ~ last_imbalance_1 + z_x_paid"
  )),
  data = subset(df, (belief_informative == 1) & (fin_quiz <= 0)),
  cluster = ~participant_code + round_number
)

# Step 3: Dictionary
setFixest_dict(c(imr = "Inverse Mills ratio", imr_lean = "Inverse Mills ratio"))

# Step 4: Output table
ivh_tex <- etable(
  iv1h, iv2h, iv3h, iv4h, iv5h, iv6h,
  title = "Payment for data and investments (Heckman selection correction)",
  tex = TRUE,
  digits = "r2",
  digits.stats = "r2",
  depvar = TRUE,
  order = c(
    "return_forecast", "rf_x_paid", "paid_round", "treated",
    "pay_choice",
    "last_return_1", "r_x_paid",
    "imr", "imr_lean",
    "overconfidence", "fin_quiz", "gender_female", "age",
    "finance_course", "trading_experience", "risk_aversion", "round_number"
  ),
  headers = list("All quiz scores" = 2, "High quiz scores" = 2, "Low quiz scores" = 2),
  fitstat = c("n", "ar2")
)
writeLines(ivh_tex, "../tables/iv_heckman_table.tex")

# ============================================================
# Table 2b: Forecasts with Heckman selection correction
# ============================================================

# IMR already computed from before; add reverse IMR for placebo columns
df$imr_0 <- -dnorm(predict(sel_probit, newdata = df, type = "link")) /
  (1 - pnorm(predict(sel_probit, newdata = df, type = "link")))

df$imr_0_lean <- -dnorm(predict(sel_probit_lean, newdata = df, type = "link")) /
  (1 - pnorm(predict(sel_probit_lean, newdata = df, type = "link")))

# Belief informative — all participants
for1h <- feols(
  as.formula(paste(
    "return_forecast ~ treated +",
    "paid_imbalance +",
    "pay_choice + choice_imbalance +",
    "paid_round +",
    "last_return_1 + last_imbalance_1 + imr +",
    controls_str
  )),
  data = subset(df, belief_informative == 1),
  cluster = ~participant_code + round_number
)

for2h <- feols(
  as.formula(paste(
    "return_forecast ~ treated +",
    "paid_imbalance +",
    "pay_choice + choice_imbalance +",
    "paid_round +",
    "last_return_1 + last_imbalance_1 + imr_lean"
  )),
  data = subset(df, belief_informative == 1),
  cluster = ~participant_code + round_number
)

# Belief informative — high quiz
for3h <- feols(
  as.formula(paste(
    "return_forecast ~ treated +",
    "paid_imbalance +",
    "pay_choice + choice_imbalance +",
    "paid_round +",
    "last_return_1 + last_imbalance_1 + imr +",
    controls_str
  )),
  data = subset(df, (belief_informative == 1) & (fin_quiz > 0)),
  cluster = ~participant_code + round_number
)

for4h <- feols(
  as.formula(paste(
    "return_forecast ~ treated +",
    "paid_imbalance +",
    "pay_choice + choice_imbalance +",
    "paid_round +",
    "last_return_1 + last_imbalance_1 + imr_lean"
  )),
  data = subset(df, (belief_informative == 1) & (fin_quiz > 0)),
  cluster = ~participant_code + round_number
)

# Belief uninformative (placebo) — reverse IMR
for5h <- feols(
  as.formula(paste(
    "return_forecast ~ treated +",
    "paid_imbalance +",
    "pay_choice + choice_imbalance +",
    "paid_round +",
    "last_return_1 + last_imbalance_1 + imr_0 +",
    controls_str
  )),
  data = subset(df, belief_informative == 0),
  cluster = ~participant_code + round_number
)

for6h <- feols(
  as.formula(paste(
    "return_forecast ~ treated +",
    "paid_imbalance +",
    "pay_choice + choice_imbalance +",
    "paid_round +",
    "last_return_1 + last_imbalance_1 + imr_0_lean"
  )),
  data = subset(df, belief_informative == 0),
  cluster = ~participant_code + round_number
)

# Dictionary
setFixest_dict(c(imr_0 = "Inverse Mills ratio", imr_0_lean = "Inverse Mills ratio"))

# Output table
forh_tex <- etable(
  for1h, for2h, for3h, for4h, for5h, for6h,
  title = "Payment for data and return forecasts (Heckman selection correction)",
  tex = TRUE,
  digits = "r2",
  digits.stats = "r2",
  depvar = TRUE,
  order = c(
    "Paid.*Imbalance", "Last imbalance", "Treated",
    "Choose to pay", "Choose to pay.*Imbalance",
    "Paid round",
    "Last return",
    "imr", "imr_lean", "imr_0", "imr_0_lean",
    "Overconfidence", "Financial quiz", "Female", "Age",
    "Finance course", "Trading experience", "Risk aversion"
  ),
  headers = list(list(
    "Belief informative" = 4,
    "Belief uninformative" = 2
  ), list("All quiz scores" = 2, "High quiz scores" = 2, "All quiz scores" = 2)),
  fitstat = c("n", "r2")
)
writeLines(forh_tex, "../tables/forecasts_heckman_table.tex")
