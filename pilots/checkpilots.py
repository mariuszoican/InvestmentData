import numpy as np
import pandas as pd
import pyfixest as pf

main_name = "main_2026-01-16"
post_name = "post_exp_2026-01-16"
pre_name = "intro_2026-01-16"
# session_code="461q1n1d" # January 12, Data price = 4
# session_code = "4pnyq9ay"  # January 13, Data price = 6
# session_code = ["m5x4bbn3"]  # January 13, Data price = 5
# session_code = ["461q1n1d", "4pnyq9ay", "m5x4bbn3"]
session_code = ["ccfpv55r", "f59wr1o5"]

# Read experiment file
data = pd.read_csv(f"{main_name}.csv")
meta = pd.read_csv("../simulations/round_metadata.csv")  # load seed and imbalance
post_exp = pd.read_csv(f"{post_name}.csv")  # post experimental data
pre_exp = pd.read_csv(f"{pre_name}.csv")  # pre experiment

### Basic Filters
### --------------
# Keep only relevant sessions
data = data[data["session.code"].isin(session_code)]
# Keep only participants who finished
# data = data[data["participant._current_page_name"] == "FinalForProlific"]
data = data[data["participant._max_page_index"] >= 49]
# Drop training sessions
data = data[data["player.round_type"] != "training"]

# dummy for treatment
data["treated"] = np.where(data["player.condition"] == "treatment", 1, 0)
# dummy for paid rounds (within treatment)
data["paid_round"] = np.where(data["player.round_type"] == "paid_data", 1, 0)
# fill in the active payment column for control group, code as -1.
data["player.pay_for_data"] = data["player.pay_for_data"].fillna(-1)

# interactions of dummies
data["treated_paychoice"] = data["treated"] * data["player.pay_for_data"]
data["treated_payround"] = data["treated"] * data["paid_round"]

# PROCESS POST-EXPERIMENTAL DATA
# ------------------------------
# Keep only post-experimental participants who finished
post_exp = post_exp[
    post_exp["participant.code"].isin(
        data["participant.code"].drop_duplicates().tolist()
    )
]

# financial quiz score
post_exp["fin_quiz"] = (
    post_exp["player.num_correct_answers"] / post_exp["player.num_quiz_questions"]
)
post_exp["gender_female"] = np.where(post_exp["player.gender"] == "Female", 1, 0)
post_exp["finance_course"] = post_exp["player.course_financial"]
post_exp["age"] = post_exp["player.age"]
post_exp["trading_experience"] = post_exp["player.trading_experience"]
post_exp["risk_aversion"] = post_exp["player.hl_switch_point"]

pre_exp = pre_exp[
    pre_exp["participant.code"].isin(
        data["participant.code"].drop_duplicates().tolist()
    )
]
pre_exp["self_literacy"] = pre_exp["player.self_assesment"]

data = data.merge(
    post_exp[
        [
            "participant.code",
            "fin_quiz",
            "gender_female",
            "finance_course",
            "age",
            "trading_experience",
            "risk_aversion",
        ]
    ],
    on="participant.code",
    how="left",
)

data = data.merge(
    pre_exp[["participant.code", "self_literacy"]], on="participant.code", how="left"
)

data["overconfidence"] = data["self_literacy"] / 10 - data["fin_quiz"]

# rename columns for inclusion in regression
data = data.rename(
    columns={
        "participant.code": "participant_code",
        "player.investment_amount": "investment_amount",
        "player.data_available": "data_available",
        "player.pay_for_data": "pay_for_data",
        "player.inner_round_number": "round_number",
        "player.imbalance_was_informative": "informative",
        "player.imbalance_informative": "belief_informative",
        "player.return_forecast": "return_forecast",
    }
)

data["paid_dummy"] = np.where(
    (data["paid_round"] == 1) & (data["pay_for_data"] == 1), 1, 0
)
data["investment_share"] = data["investment_amount"] / np.where(
    data["paid_dummy"] == 1, 95, 100
)

# add metadata for the given round
data = data.merge(
    meta[
        [
            "round_number",
            "last_imbalance_1",
            "last_return_1",
            "last_imbalance_2",
            "last_return_2",
            "last_imbalance_3",
            "last_return_3",
            "next_return",
        ]
    ],
    on="round_number",
    how="left",
)

data["imb_difference"] = data["last_imbalance_1"] - data["last_imbalance_2"]
data["return_difference"] = data["last_return_1"] - data["last_return_2"]


# standardizations
for col in [
    "round_number",
    "age",
    "fin_quiz",
    "overconfidence",
    "risk_aversion",
    "last_imbalance_1",
    "last_return_1",
    "imb_difference",
    "return_difference",
]:
    data[col] = (data[col] - data[col].mean()) / data[col].std()

# interactions
data["willing_imbalance"] = (
    data["treated"] * data["pay_for_data"] * data["last_imbalance_1"]
)
data["paid_imbalance"] = data["treated"] * data["paid_round"] * data["last_imbalance_1"]
data["treated_imbalance"] = data["treated"] * data["last_imbalance_1"]
data["willing_return"] = data["treated"] * data["pay_for_data"] * data["last_return_1"]
data["paid_return"] = data["treated"] * data["paid_round"] * data["last_return_1"]

# variable labels
labels = {
    "belief_informative": "Belief informative data",
    "informative": "Informative data",
    "treated": "Treated",
    "pay_for_data": "Chose to pay",
    "paid_round": "Costly data",
    "return_forecast": "Return forecast",
    "treated_paychoice": r"Treated $\times$ Choose to pay",
    "treated_payround": r"Treated $\times$ Paid round",
    "investment_amount": "Investment amount",
    "investment_share": "Investment share",
    "willing_imbalance": r"Treated $\times$ Choose to pay $\times$ Imbalance",
    "paid_imbalance": r"Treated $\times$ Paid round $\times$ Imbalance",
    "willing_return": r"Treated $\times$ Choose to pay $\times$ Lag return",
    "paid_return": r"Treated $\times$ Paid round $\times$ Lag return",
    "round_number": "Round number",
    "last_imbalance_1": "Order imbalance",
    "last_return_1": "Lag return",
    "fin_quiz": "Financial quiz",
    "gender_female": "Gender female",
    "finance_course": "Finance course",
    "age": "Age",
    "trading_experience": "Trading experience",
    "risk_aversion": "Risk aversion",
    "self_literacy": "Self assessment",
    "overconfidence": "Overconfidence",
}

controls = (
    "+overconfidence+fin_quiz+gender_female+age+finance_course"
    "+trading_experience+risk_aversion"
)


### Beliefs that order flow data is informative
### --------------------------------------------
h1_1 = pf.feols(
    "belief_informative ~ treated + treated_paychoice + treated_payround + last_imbalance_1 + last_return_1 + informative + round_number"
    + controls,
    data=data,
    vcov={"CRV3": "participant_code+round_number"},
)
h1_2 = pf.feols(
    "belief_informative ~ treated + treated_paychoice + treated_payround + last_imbalance_1 + last_return_1 + informative"
    + controls,
    data=data,
    vcov={"CRV3": "participant_code+round_number"},
)

table_h1 = pf.etable(
    [h1_1, h1_2],
    type="tex",
    signif_code=[0.01, 0.05, 0.1],
    labels=labels,
    show_se_type=False,
    coef_fmt="b \n (p) ",
    notes=" ",
)
print(table_h1)
with open("table_h1.tex", "w") as f:
    f.write(table_h1)

### Forecast endowment effect
### --------------------------------------------
h2_1 = pf.feols(
    "return_forecast ~ willing_imbalance + paid_imbalance + treated + treated_paychoice + treated_payround + last_imbalance_1 + last_return_1 "
    + controls,
    data=data[(data["data_available"] == 1) & (data["belief_informative"] == 1)],
    vcov={"CRV3": "participant_code+round_number"},
)
h2_2 = pf.feols(
    "return_forecast ~ willing_imbalance + paid_imbalance + treated + treated_paychoice + treated_payround + last_imbalance_1 + last_return_1 + informative + round_number"
    + controls,
    data=data[(data["data_available"] == 1) & (data["belief_informative"] == 1)],
    vcov={"CRV3": "participant_code+round_number"},
)
h2_3 = pf.feols(
    "return_forecast ~ willing_imbalance + paid_imbalance + treated + treated_paychoice + treated_payround + last_imbalance_1 + last_return_1 ",
    data=data[(data["data_available"] == 1) & (data["belief_informative"] == 0)],
    vcov={"CRV3": "participant_code+round_number"},
)
h2_4 = pf.feols(
    "return_forecast ~ willing_imbalance + paid_imbalance + treated + treated_paychoice + treated_payround + last_imbalance_1 + last_return_1 + informative + round_number"
    + controls,
    data=data[(data["data_available"] == 1) & (data["belief_informative"] == 0)],
    vcov={"CRV3": "participant_code+round_number"},
)
h2_5 = pf.feols(
    "return_forecast ~ willing_imbalance + paid_imbalance + treated + treated_paychoice + treated_payround + last_imbalance_1 + last_return_1",
    data=data[(data["data_available"] == 1)],
    vcov={"CRV3": "participant_code+round_number"},
)
h2_6 = pf.feols(
    "return_forecast ~ willing_imbalance + paid_imbalance + treated + treated_paychoice + treated_payround + last_imbalance_1 + last_return_1 + informative + round_number"
    + controls,
    data=data[(data["data_available"] == 1)],
    vcov={"CRV3": "participant_code+round_number"},
)

table_h2 = pf.etable(
    [h2_1, h2_2, h2_3, h2_4, h2_5, h2_6],
    type="tex",
    signif_code=[0.01, 0.05, 0.1],
    labels=labels,
    show_se_type=False,
    model_heads=[
        "Perceived informative",
        "Perceived informative",
        "Perceived useless",
        "Perceived useless",
        "Full sample",
        "Full sample",
    ],
    coef_fmt="b \n (p) ",
    notes=" ",
)
print(table_h2)
with open("table_h2.tex", "w") as f:
    f.write(table_h2)

### Investment endowment effect
### --------------------------------------------
h3_1 = pf.feols(
    "investment_share ~ willing_imbalance + paid_imbalance + treated + treated_paychoice + treated_payround + last_imbalance_1 + last_return_1 "
    + controls,
    data=data[(data["data_available"] == 1) & (data["belief_informative"] == 1)],
    vcov={"CRV3": "participant_code+round_number"},
)
h3_2 = pf.feols(
    "investment_share ~ willing_imbalance + paid_imbalance + treated + treated_paychoice + treated_payround + last_imbalance_1 + last_return_1 + informative + round_number"
    + controls,
    data=data[(data["data_available"] == 1) & (data["belief_informative"] == 1)],
    vcov={"CRV3": "participant_code+round_number"},
)
h3_3 = pf.feols(
    "investment_share ~ willing_imbalance + paid_imbalance + treated + treated_paychoice + treated_payround + last_imbalance_1 + last_return_1",
    data=data[(data["data_available"] == 1) & (data["belief_informative"] == 0)],
    vcov={"CRV3": "participant_code+round_number"},
)
h3_4 = pf.feols(
    "investment_share ~ willing_imbalance + paid_imbalance + treated + treated_paychoice + treated_payround + last_imbalance_1 + last_return_1 + informative + round_number"
    + controls,
    data=data[(data["data_available"] == 1) & (data["belief_informative"] == 0)],
    vcov={"CRV3": "participant_code+round_number"},
)
h3_5 = pf.feols(
    "investment_share ~ willing_imbalance + paid_imbalance + treated + treated_paychoice + treated_payround + last_imbalance_1 + last_return_1",
    data=data[(data["data_available"] == 1)],
    vcov={"CRV3": "participant_code+round_number"},
)
h3_6 = pf.feols(
    "investment_share ~ willing_imbalance + paid_imbalance + treated + treated_paychoice + treated_payround + last_imbalance_1 + last_return_1 + informative + round_number"
    + controls,
    data=data[(data["data_available"] == 1)],
    vcov={"CRV3": "participant_code+round_number"},
)

table_h3 = pf.etable(
    [h3_1, h3_2, h3_3, h3_4, h3_5, h3_6],
    type="tex",
    signif_code=[0.01, 0.05, 0.1],
    labels=labels,
    show_se_type=False,
    model_heads=[
        "Perceived informative",
        "Perceived informative",
        "Perceived useless",
        "Perceived useless",
        "Full sample",
        "Full sample",
    ],
    coef_fmt="b \n (p) ",
    notes=" ",
)
print(table_h3)
with open("table_h3.tex", "w") as f:
    f.write(table_h3)


### Belief pass-through
### -------------------
h4 = pf.feols(
    "investment_share ~ treated + treated_paychoice + treated_payround + round_number"
    + controls
    + "| return_forecast ~ last_imbalance_1 + last_return_1",  # IV step
    data=data[(data["data_available"] == 1) & (data["belief_informative"] == 1)],
    vcov={"CRV1": "participant_code+round_number"},
)


### Selection
### --------
data["risk_aversion2"] = data["risk_aversion"] ** 2
h7 = pf.feols(
    "pay_for_data ~ overconfidence + fin_quiz + risk_aversion +  risk_aversion2 + round_number"
    + controls,
    data=data[(data["treated"] == 1)],
    vcov={"CRV3": "participant_code+round_number"},
)

### Noise overfitting
### ------------------
data["forecast_error_abs"] = np.abs(data["return_forecast"] - data["next_return"])
h9 = pf.feols(
    "forecast_error_abs ~ treated + treated_paychoice + treated_payround + last_imbalance_1 + last_return_1 + round_number"
    + controls,
    data=data[(data["informative"] == 0)],
    vcov={"CRV3": "participant_code+round_number"},
)

### Learning from data
### ------------------
data["forecast_error_abs"] = np.abs(data["return_forecast"] - data["next_return"])
h10 = pf.feols(
    "forecast_error_abs ~ fin_quiz * data_available" + controls,
    data=data[(data["informative"] == 1)],
    vcov={"CRV3": "participant_code+round_number"},
)

data.to_csv("processed_data_pilots.csv")
