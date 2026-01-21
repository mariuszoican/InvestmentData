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
  )

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

# IV regressions with felm
# Syntax: y ~ exog | FEs | (endog ~ instruments) | cluster

iv1 <- felm(as.formula(paste("investment_amount~treated+paid_round+pay_choice+round_number+last_return_1+r_x_paid+", paste(controls, collapse = " + "),
                             "| 0 | (return_forecast | rf_x_paid ~ last_imbalance_1 + z_x_paid) | participant_code+round_number")),
            data = subset(df, belief_informative == 1), exactDOF = TRUE)
iv2 <- felm(as.formula(paste("investment_amount~treated+paid_round+pay_choice+round_number+last_return_1+r_x_paid",
                             "| 0 | (return_forecast | rf_x_paid ~ last_imbalance_1 + z_x_paid) | participant_code+round_number")),
            data = subset(df, belief_informative == 1), exactDOF = TRUE)
iv1a <- felm(as.formula(paste("investment_amount~treated+paid_round+pay_choice+round_number+last_return_1+r_x_paid+", paste(controls, collapse = " + "),
                              "| 0 | (return_forecast | rf_x_paid ~ last_return_1 + r_x_paid) | participant_code+round_number")),
             data = subset(df, belief_informative == 0), exactDOF = TRUE)
iv2a <- felm(as.formula(paste("investment_amount~treated+paid_round+pay_choice+round_number+last_return_1+r_x_paid",
                              "| 0 | (return_forecast | rf_x_paid ~ last_return_1 + r_x_paid) | participant_code+round_number")),
             data = subset(df, belief_informative == 0), exactDOF = TRUE)


# Output table
tex_output <- stargazer(iv1, iv2, iv1a, iv2a,
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