import numpy as np
import pandas as pd
import pyfixest as pf

main_name = "main_2026-01-14"
post_name = "post_exp_2026-01-14"
pre_name = "intro_2026-01-14"
# session_code="461q1n1d" # January 12, Data price = 4
# session_code = "4pnyq9ay"  # January 13, Data price = 6
# session_code = ["m5x4bbn3"]  # January 13, Data price = 5
session_code = ["461q1n1d", "4pnyq9ay", "m5x4bbn3"]


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
data = data[data["participant._current_page_name"] == "FinalForProlific"]
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
    }
)


# add metadata for the given round
data = data.merge(
    meta[["round_number", "last_imbalance", "last_return", "next_return"]],
    on="round_number",
    how="left",
)

# variable labels
labels = {
    "belief_informative": "Belief informative data",
    "informative": "Informative data",
    "treated": "Treated",
    "pay_for_data": "Chose to pay",
    "paid_round": "Costly data",
    "treated_paychoice": r"Treated $\times$ Choose to pay",
    "treated_payround": r"Treated $\times$ Paid round",
    "round_number": "Round number",
    "last_imbalance": "Order imbalance",
    "last_return": "Lag return",
    "fin_quiz": "Financial quiz",
    "gender_female": "Gender female",
    "finance_course": "Finance course",
    "age": "Age",
    "trading_experience": "Trading experience",
    "risk_aversion": "Risk aversion",
    "self_literacy": "Self assesment",
    "overconfidence": "Overconfidence",
}

controls = (
    "+overconfidence+fin_quiz+gender_female+age+finance_course"
    "+trading_experience+risk_aversion"
)

m1 = pf.feols(
    "belief_informative ~ treated + treated_paychoice + treated_payround + last_imbalance + informative + round_number"
    + controls,
    data=data,
    vcov={"CRV1": "participant_code+round_number"},
)

m2 = pf.feols(
    "belief_informative ~ treated + treated_paychoice + treated_payround + last_imbalance +  informative"
    + controls,
    data=data,
    vcov={"CRV1": "participant_code+round_number"},
)

table = pf.etable(
    [m1, m2],
    type="tex",
    signif_code=[0.01, 0.05, 0.1],
    labels=labels,
    show_se_type=False,
    coef_fmt="b \n (p) ",
    notes=" ",
)
print(table)
with open("table_1.tex", "w") as f:
    f.write(table)
