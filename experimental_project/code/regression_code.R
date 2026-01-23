library(tidyverse)
library(lfe)
library(stargazer)
library(fixest)
library(modelsummary)
library(rstudioapi)

# Load data
setwd(dirname(getActiveDocumentContext()$path))
df <- read.csv("../processed_panels.csv")

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
    z_x_paid = last_imbalance_1 * paid_round,
    r_x_paid = last_return_1 * paid_round
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
  share_correct = "Share correct predictions"
))


# ============================================================
# Table 1: Beliefs
# ============================================================

bel1 <- feols(
  as.formula(paste(
    "belief_informative ~ paid_uninformative +",
    "paid_round + treated + informative +",
    "pay_choice + round_number +",
    "last_return_1 + last_imbalance_1 +",
    controls_str
  )),
  data = subset(df),
  cluster = ~participant_code + round_number
)

bel2 <- feols(
  as.formula(paste(
    "belief_informative ~ paid_uninformative +",
    "paid_round + treated + informative +",
    "pay_choice + round_number +",
    "last_return_1 + last_imbalance_1"
  )),
  data = subset(df),
  cluster = ~participant_code + round_number
)

bel3 <- feols(
  as.formula(paste(
    "belief_informative ~ paid_uninformative +",
    "paid_round + treated + informative +",
    "pay_choice + round_number +",
    "last_return_1 + last_imbalance_1 +",
    controls_str
  )),
  data = subset(df, fin_quiz >= 0),
  cluster = ~participant_code + round_number
)

bel4 <- feols(
  as.formula(paste(
    "belief_informative ~ paid_uninformative +",
    "paid_round + treated + informative +",
    "pay_choice + round_number +",
    "last_return_1 + last_imbalance_1"
  )),
  data = subset(df, fin_quiz >= 0),
  cluster = ~participant_code + round_number)

bel5 <- feols(
  as.formula(paste(
    "belief_informative ~ paid_uninformative +",
    "paid_round + treated + informative +",
    "pay_choice + round_number +",
    "last_return_1 + last_imbalance_1 +",
    controls_str
  )),
  data = subset(df, fin_quiz < 0),
  cluster = ~participant_code + round_number
)

bel6 <- feols(
  as.formula(paste(
    "belief_informative ~ paid_uninformative +",
    "paid_round + treated + informative +",
    "pay_choice + round_number +",
    "last_return_1 + last_imbalance_1"
  )),
  data = subset(df, fin_quiz < 0),
  cluster = ~participant_code + round_number)


bel_tex <- etable(
  bel1, bel2, bel3, bel4, bel5, bel6,
  title = "Payment for data and beliefs",
  tex = TRUE,
  digits = "r2",
  digits.stats = "r2",
  depvar = TRUE,
  order = c(
    "Paid.*Not informative", "Paid round", "Treated", "Informative round",
    "Choose to pay", "Round number",
    "Last return", "Last imbalance",
    "Overconfidence", "Financial quiz", "Female", "Age",
    "Finance course", "Trading experience", "Risk aversion"
  ),
  headers = list("All quiz scores" = 2, "High quiz scores" = 2, "Low quiz scores" = 2),
  fitstat = c("n", "r2")
)
writeLines(bel_tex, "../tables/beliefs_table.tex")


# ============================================================
# Table 2: Forecast equations
# ============================================================

for1 <- feols(
  as.formula(paste(
    "return_forecast ~ treated +",
    "paid_imbalance +",
    "pay_choice + choice_imbalance +",
    "paid_round +",
    "last_return_1 + last_imbalance_1 +",
    controls_str
  )),
  data = subset(df, belief_informative == 1),
  cluster = ~participant_code + round_number
)


for2 <- feols(
  as.formula(paste(
    "return_forecast ~ treated +",
    "paid_imbalance +",
    "pay_choice + choice_imbalance +",
    "paid_round +",
    "last_return_1 + last_imbalance_1"
  )),
  data = subset(df, belief_informative == 1),
  cluster = ~participant_code + round_number
)

for3 <- feols(
  as.formula(paste(
    "return_forecast ~ treated +",
    "paid_imbalance +",
    "pay_choice + choice_imbalance +",
    "paid_round +",
    "last_return_1 + last_imbalance_1 +",
    controls_str
  )),
  data = subset(df, (belief_informative == 1) & (fin_quiz > 0)),
  cluster = ~participant_code + round_number
)


for4 <- feols(
  as.formula(paste(
    "return_forecast ~ treated +",
    "paid_imbalance +",
    "pay_choice + choice_imbalance +",
    "paid_round +",
    "last_return_1 + last_imbalance_1"
  )),
  data = subset(df, (belief_informative == 1) & (fin_quiz > 0)),
  cluster = ~participant_code + round_number
)

for5 <- feols(
  as.formula(paste(
    "return_forecast ~ treated +",
    "paid_imbalance +",
    "pay_choice + choice_imbalance +",
    "paid_round +",
    "last_return_1 + last_imbalance_1 +",
    controls_str
  )),
  data = subset(df, belief_informative == 0),
  cluster = ~participant_code + round_number
)


for6 <- feols(
  as.formula(paste(
    "return_forecast ~ treated +",
    "paid_imbalance +",
    "pay_choice + choice_imbalance +",
    "paid_round +",
    "last_return_1 + last_imbalance_1"
  )),
  data = subset(df, belief_informative == 0),
  cluster = ~participant_code + round_number
)

for_tex <- etable(
  for1, for2, for3, for4, for5, for6,
  title = "Payment for data and return forecasts",
  tex = TRUE,
  digits = "r2",
  digits.stats = "r2",
  depvar = TRUE,
  order = c(
    "Paid.*Imbalance", "Last imbalance", "Treated",
    "Choose to pay", "Choose to pay.*Imbalance",
    "Paid round",
    "Last return",
    "Overconfidence", "Financial quiz", "Female", "Age",
    "Finance course", "Trading experience", "Risk aversion"
  ),
  headers = list(list(
    "Belief informative" = 4,
    "Belief uninformative" = 2
  ), list("All quiz scores" = 2, "High quiz scores" = 2, "All quiz scores" = 2)),
  fitstat = c("n", "r2")
)
writeLines(for_tex, "../tables/forecasts_table.tex")


# ============================================================
# Table 3: Pass-through equations (IV)
# ============================================================

iv1 <- feols(
  as.formula(paste(
    "investment_share ~ treated + paid_round + pay_choice + round_number + last_return_1 + r_x_paid +",
    controls_str,
    "| 0 | return_forecast + rf_x_paid ~ last_imbalance_1 + z_x_paid"
  )),
  data = subset(df, belief_informative == 1),
  cluster = ~participant_code + round_number
)
iv2 <- feols(
  as.formula(paste(
    "investment_share ~ treated + paid_round + pay_choice + round_number + last_return_1 + r_x_paid",
    "| 0 | return_forecast + rf_x_paid ~ last_imbalance_1 + z_x_paid"
  )),
  data = subset(df, belief_informative == 1),
  cluster = ~participant_code + round_number
)
iv3 <- feols(
  as.formula(paste(
    "investment_share ~ treated + paid_round + pay_choice + round_number + last_return_1 + r_x_paid +",
    controls_str,
    "| 0 | return_forecast + rf_x_paid ~ last_imbalance_1 + z_x_paid"
  )),
  data = subset(df, (belief_informative == 1) & (fin_quiz > 0)),
  cluster = ~participant_code + round_number
)
iv4 <- feols(
  as.formula(paste(
    "investment_share ~ treated + paid_round + pay_choice + round_number + last_return_1 + r_x_paid",
    "| 0 | return_forecast + rf_x_paid ~ last_imbalance_1 + z_x_paid"
  )),
  data = subset(df, (belief_informative == 1) & (fin_quiz > 0)),
  cluster = ~participant_code + round_number
)
iv5 <- feols(
  as.formula(paste(
    "investment_share ~ treated + paid_round + pay_choice + round_number + last_return_1 + r_x_paid +",
    controls_str,
    "| 0 | return_forecast + rf_x_paid ~ last_imbalance_1 + z_x_paid"
  )),
  data = subset(df, (belief_informative == 1) & (fin_quiz <= 0)),
  cluster = ~participant_code + round_number
)
iv6 <- feols(
  as.formula(paste(
    "investment_share ~ treated + paid_round + pay_choice + round_number + last_return_1 + r_x_paid",
    "| 0 | return_forecast + rf_x_paid ~ last_imbalance_1 + z_x_paid"
  )),
  data = subset(df, (belief_informative == 1) & (fin_quiz <= 0)),
  cluster = ~participant_code + round_number
)


iv_tex <- etable(
  iv1, iv2, iv3, iv4, iv5, iv6,
  title = "Payment for data and investments",
  tex = TRUE,
  digits = "r2",
  digits.stats = "r2",
  depvar = TRUE,
  order = c(
    "return_forecast", "rf_x_paid", "paid_round", "treated",
    "pay_choice", "choice_imbalance",
    "last_return_1", "r_x_paid",
    "overconfidence", "fin_quiz", "gender_female", "age",
    "finance_course", "trading_experience", "risk_aversion", "round_number"
  ),
  headers = list("All quiz scores" = 2, "High quiz scores" = 2, "Low quiz scores" = 2),
  fitstat = c("n", "ar2")
)
writeLines(iv_tex, "../tables/iv_table.tex")


# ============================================================
# Table 4: Selection
# ============================================================

sel1 <- feols(
  as.formula(paste(
    "pay_choice ~ overconfidence + fin_quiz + high_education + gender_female + age +
     trading_experience + risk_aversion"
  )),
  data = subset(df, treated == 1),
  cluster = ~participant_code + round_number)
sel2 <- feols(
  as.formula(paste(
    "pay_choice ~ overconfidence + fin_quiz + high_education | round_number"
  )),
  data = subset(df, treated == 1),
  cluster = ~participant_code + round_number
)
sel3 <- feols(
  as.formula(paste(
    "pay_choice ~ overconfidence + fin_quiz + high_education + gender_female + age +
     trading_experience + risk_aversion | round_number"
  )),
  data = subset(df, treated == 1),
  cluster = ~participant_code + round_number
)
sel4 <- feglm(
  as.formula(paste(
    "pay_choice ~ overconfidence + fin_quiz + high_education + gender_female + age +
     trading_experience + risk_aversion"
  )),
  data = subset(df, treated == 1),
  cluster = ~participant_code + round_number,
  family = binomial(link = "probit")
)
sel5 <- feglm(
  as.formula(paste(
    "pay_choice ~ overconfidence + fin_quiz + high_education | round_number"
  )),
  data = subset(df, treated == 1),
  cluster = ~participant_code + round_number,
  family = binomial(link = "probit")
)
sel6 <- feglm(
  as.formula(paste(
    "pay_choice ~ overconfidence + fin_quiz + high_education + gender_female + age +
     trading_experience + risk_aversion | round_number"
  )),
  data = subset(df, treated == 1),
  cluster = ~participant_code + round_number,
  family = binomial(link = "probit")
)


sel_tex <- etable(
  sel1, sel2, sel3, sel4, sel5, sel6,
  title = "Determinants of data payment choice",
  tex = TRUE,
  digits = "r2",
  digits.stats = "r2",
  depvar = TRUE,
  order = c(
    "overconfidence", "fin_quiz", "finance_course", "trading_experience", "gender_female", "age",
    "risk_aversion", "round_number"),
  # headers = list("All quiz scores" = 2, "High quiz scores" = 2, "Low quiz scores" = 2),
  fitstat = c("n", "pr2")
)
writeLines(sel_tex, "../tables/selection_table.tex")


sum_vars <- df %>%
  mutate(pay_choice = if_else(treated == 1, pay_choice, NA_real_),
         belief_informative_when_informative = if_else(informative == 1, belief_informative, NA_real_),
         belief_informative_when_uninformative = if_else(informative == 0, belief_informative, NA_real_)) %>%
  select(
    return_forecast, investment_share, belief_informative, belief_informative_when_informative,
    belief_informative_when_uninformative, pay_choice,
    overconfidence_raw, fin_quiz_raw, gender_female, age_raw,
    finance_course, high_education, trading_experience
  )

stargazer(
  as.data.frame(sum_vars),
  type = "latex",
  title = "Summary Statistics",
  digits = 2,
  summary.stat = c("mean", "sd", "p25", "median", "p75", "min", "max"),
  covariate.labels = c(
    "Return forecast", "Investment share (\\%)", "Belief informative", "Belief informative | informative",
    "Belief informative | uninformative ", "Choose to pay",
    "Overconfidence", "Financial quiz", "Female", "Age",
    "Finance course", "College education", "Trading experience", "Risk aversion"
  ),
  out = "../tables/summary_stats.tex"
)

# Coefficient plot for key variables
coefplot(
  list(iv1, iv3, iv5),
  keep = c("return_forecast", "rf_x_paid"),
  main = "Effect of Forecasts on Investment (IV)",
  xlab = "Coefficient",
  dict = c(
    return_forecast = "Return forecast",
    rf_x_paid = "Forecast × Paid round"
  )
)