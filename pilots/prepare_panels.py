import numpy as np
import pandas as pd
import pyfixest as pf

main_name = "main_2026-01-18"
post_name = "post_exp_2026-01-18"
pre_name = "intro_2026-01-18"
# session_code="461q1n1d" # January 12, Data price = 4
# session_code = "4pnyq9ay"  # January 13, Data price = 6
# session_code = ["m5x4bbn3"]  # January 13, Data price = 5
# session_code = ["461q1n1d", "4pnyq9ay", "m5x4bbn3"]

# session_code = ["ccfpv55r", "f59wr1o5"]  # Jan 16, new graphs
# session_code = ["151ug4w3"]  # Jan 17, new graphs and new volatility
session_code = ["8aeypvgw"]  # Jan 17, desktop only

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
data = data[
    data["participant._current_page_name"].isin(["FinalForProlific", "Demographics"])
]
# data = data[data["participant._max_page_index"] >= 49]
# Drop training sessions
data = data[data["player.round_type"] != "training"]

# dummy for treatment
data["treated"] = np.where(data["player.condition"] == "treatment", 1, 0)
# dummy for paid rounds (within treatment)
data["paid_round"] = np.where(data["player.round_type"] == "paid_data", 1, 0)
# fill in the active payment column for control group, code as -1.
data["player.pay_for_data"] = data["player.pay_for_data"].fillna(-1)

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

data.to_csv("processed_data_pilots.csv")
