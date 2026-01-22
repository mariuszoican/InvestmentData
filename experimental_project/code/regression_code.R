library(tidyverse)
library(lfe)
library(stargazer)
library(rstudioapi)

# Load data
setwd(dirname(getActiveDocumentContext()$path))
df <- read.csv("../processed_panels.csv")


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
    belief_informative_imbalance = belief_informative * last_imbalance_1,
    rf_x_paid = return_forecast * paid_round,
    z_x_paid = last_imbalance_1 * paid_round,
    r_x_paid = last_return_1 * paid_round
  )  %>%
  group_by(participant_code) %>%
  mutate(share_correct = mean(correct_belief, na.rm = TRUE)) %>%
  ungroup()

controls <- c("overconfidence", "fin_quiz", "gender_female", "age",
              "finance_course", "trading_experience", "risk_aversion")
controls_str <- paste(controls, collapse = " + ")

### Table 1: Beliefs
### ------------------

belief1 <- felm(belief_informative ~ paid_informative +
  paid_uninformative +
  treated +
  informative +
  pay_choice +
  last_return_1 +
  last_imbalance_1 +
  round_number +
  overconfidence +
  fin_quiz +
  gender_female +
  age +
  finance_course +
  trading_experience +
  risk_aversion
  |
  0 |
  0 |
  participant_code + round_number,
                data = df, exactDOF = TRUE)

# ============================================================
# Table 1: Beliefs (matches your 5 reghdfe specs)
# ============================================================

bel1 <- felm(
  as.formula(paste(
    "belief_informative ~ paid_informative + paid_uninformative + treated + informative + pay_choice +",
    "last_return_1 + last_imbalance_1 + round_number +", controls_str,
    "| 0 | 0 | participant_code + round_number"
  )),
  data = df, exactDOF = TRUE
)

bel2 <- felm(
  belief_informative ~ paid_informative + paid_uninformative + treated + informative + pay_choice +
    last_return_1 + last_imbalance_1 + round_number
  | 0 | 0 | participant_code + round_number,
  data = df, exactDOF = TRUE
)

bel3 <- felm(
  belief_informative ~ paid_informative + paid_uninformative + treated + informative + pay_choice
  | 0 | 0 | participant_code + round_number,
  data = df, exactDOF = TRUE
)

bel4 <- felm(
  as.formula(paste(
    "belief_informative ~ paid_round + treated + informative + pay_choice +",
    "last_return_1 + last_imbalance_1 + round_number +", controls_str,
    "| 0 | 0 | participant_code + round_number"
  )),
  data = df, exactDOF = TRUE
)

bel5 <- felm(
  belief_informative ~ paid_round + treated + informative + pay_choice +
    last_return_1 + last_imbalance_1 + round_number
  | 0 | 0 | participant_code + round_number,
  data = df, exactDOF = TRUE
)

bel_tex <- stargazer(
  bel1, bel2, bel3, bel4, bel5,
  title = "Beliefs (FE OLS; Two-way clustered SEs)",
  type = "latex",
  report = "vc*t",              # coef + (clustered) SE + t-stat
  omit.stat = c("LL", "ser", "F"),
  no.space = TRUE,
  dep.var.labels = "Belief: informative (0/1)",
  notes = c("Two-way clustered standard errors (participant and round)"),
  # Keep/order like outreg2 keep(*), but in a clean consistent order:
  order = c(
    "paid_informative", "paid_uninformative",
    "paid_round",
    "treated", "informative", "pay_choice",
    "last_return_1", "last_imbalance_1", "round_number",
    controls
  ),
  covariate.labels = c(
    "Paid $\\times$ Informative", "Paid $\\times$ Uninformative",
    "Paid round",
    "Treated", "Informative", "Choose to pay",
    "Last return", "Last imbalance", "Round number",
    "Overconfidence", "Financial quiz", "Female", "Age",
    "Finance course", "Trading experience", "Risk aversion"
  )
)

writeLines(bel_tex, "../tables/beliefs_table.tex")


# ============================================================
# Table 2: Forecast equation (2 specs)
# ============================================================

for1 <- felm(
  as.formula(paste(
    "return_forecast ~ treated +",
    "paid_informative_imbalance +",
    "belief_informative_imbalance +",
    "pay_choice + choice_imbalance +",
    "paid_round +",
    "last_return_1 + last_imbalance_1 + ",
    controls_str,
    "| 0 | 0 | participant_code + round_number"
  )),
  data = df, exactDOF = TRUE
)

for2 <- felm(
  return_forecast ~ treated +
    paid_informative_imbalance +
    belief_informative_imbalance +
    pay_choice + choice_imbalance + paid_round +
    last_return_1 + last_imbalance_1
  | 0 | 0 | participant_code + round_number,
  data = df, exactDOF = TRUE
)

for_tex <- stargazer(
  for1, for2,
  title = "Return Forecasts (FE OLS; Two-way clustered SEs)",
  type = "latex",
  report = "vc*t",
  omit.stat = c("LL", "ser", "F"),
  no.space = TRUE,
  dep.var.labels = "Return forecast",
  notes = c("Two-way clustered standard errors (participant and round)"),
  order = c(
    "treated",
    "paid_informative_imbalance", "belief_informative_imbalance",
    "pay_choice", "choice_imbalance",
    "paid_round",
    "last_return_1", "last_imbalance_1",
    controls
  ),
  covariate.labels = c(
    "Treated",
    "Paid $\\times$ Belief informative $\\times$ Imbalance", "Belief informative $\\times$ Imbalance",
    "Choose to pay", "Choose to pay $\\times$ Imbalance",
    "Paid round",
    "Last return", "Last imbalance",
    "Overconfidence", "Financial quiz", "Female", "Age",
    "Finance course", "Trading experience", "Risk aversion"
  )
)

writeLines(for_tex, "../tables/forecasts_table.tex")

# IV regressions with felm
# Syntax: y ~ exog | FEs | (endog ~ instruments) | cluster

iv1 <- felm(as.formula(paste("investment_amount~treated+paid_round+pay_choice+round_number+last_return_1+r_x_paid+", paste(controls, collapse = " + "),
                             "| 0 | (return_forecast | rf_x_paid ~ last_imbalance_1 + z_x_paid) | participant_code+round_number")),
            data = subset(df, belief_informative == 1), exactDOF = TRUE)
iv2 <- felm(as.formula(paste("investment_amount~treated+paid_round+pay_choice+round_number+last_return_1+r_x_paid",
                             "| 0 | (return_forecast | rf_x_paid ~ last_imbalance_1 + z_x_paid) | participant_code+round_number")),
            data = subset(df, belief_informative == 1), exactDOF = TRUE)
iv1a <- felm(as.formula(paste("investment_share~treated+paid_round+pay_choice+round_number+last_return_1+r_x_paid+", paste(controls, collapse = " + "),
                             "| 0 | (return_forecast | rf_x_paid ~ last_imbalance_1 + z_x_paid) | participant_code+round_number")),
            data = subset(df, belief_informative == 1), exactDOF = TRUE)
iv2a <- felm(as.formula(paste("investment_share~treated+paid_round+pay_choice+round_number+last_return_1+r_x_paid",
                             "| 0 | (return_forecast | rf_x_paid ~ last_imbalance_1 + z_x_paid) | participant_code+round_number")),
            data = subset(df, belief_informative == 1), exactDOF = TRUE)
iv3 <- felm(as.formula(paste("investment_amount~treated+paid_round+pay_choice+round_number+last_imbalance_1+z_x_paid+", paste(controls, collapse = " + "),
                             "| 0 | (return_forecast | rf_x_paid ~ last_return_1 + r_x_paid ) | participant_code+round_number")),
            data = subset(df, belief_informative == 0), exactDOF = TRUE)
iv4 <- felm(as.formula(paste("investment_amount~treated+paid_round+pay_choice+round_number+last_imbalance_1+z_x_paid",
                             "| 0 | (return_forecast | rf_x_paid ~ last_return_1 + r_x_paid ) | participant_code+round_number")),
            data = subset(df, belief_informative == 0), exactDOF = TRUE)

# Output table
tex_output <- stargazer(iv1, iv2, iv1a, iv2a, iv3, iv4,
                        title = "Investment and Return Forecasts (IV Estimates)",
                        dep.var.labels = c("Investment (E\\$)", "Investment (\\%)"),
                        report = "vc*t",
                        order = c("return_forecast", "rf_x_paid", "treated", "paid_round", "pay_choice",
                                  "round_number", "last_return_1", "r_x_paid", "overconfidence", "fin_quiz", "gender_female", "age",
                                  "finance_course", "trading_experience", "risk_aversion"),
                        covariate.labels = c("Return forecast", "Return forecast $\\times$ Paid", "Treated", "Paid round",
                                             "Choose to pay", "Round number", "Last return", "Last return $\\times$ Paid",
                                             "Overconfidence", "Financial quiz", "Female", "Age",
                                             "Finance course", "Trading experience", "Risk aversion"),
                        multicolumn = TRUE,
                        omit.stat = c("LL", "ser", "F"),
                        ci = FALSE,
                        single.row = FALSE,
                        no.space = TRUE,
                        notes = c("Two-way clustered standard errors (participant and round)")
)
writeLines(tex_output, "../tables/iv_table.tex")

# ============================================================
# Selection regression: pay_for_data, treated==1
# ============================================================

sel1 <- felm(
  pay_for_data ~ overconfidence + fin_quiz + gender_female + age +
    finance_course + trading_experience + risk_aversion + round_number
  | 0 | 0 | participant_code + round_number,
  data = subset(df, treated == 1), exactDOF = TRUE
)

sel_tex <- stargazer(
  sel1,
  title = "Selection into Paying for Data (Treated only; Two-way clustered SEs)",
  type = "latex",
  report = "vc*t",
  omit.stat = c("LL", "ser", "F"),
  no.space = TRUE,
  dep.var.labels = "Pay for data (0/1)",
  notes = c("Sample restricted to treated==1. Two-way clustered standard errors (participant and round)."),
  order = c("overconfidence", "fin_quiz", "gender_female", "age",
            "finance_course", "trading_experience", "risk_aversion", "round_number"),
  covariate.labels = c("Overconfidence", "Financial quiz", "Female", "Age",
                       "Finance course", "Trading experience", "Risk aversion", "Round number")
)

writeLines(sel_tex, "../tables/selection_table.tex")