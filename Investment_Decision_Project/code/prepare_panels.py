# prepare_panels.py

import numpy as np
import pandas as pd

main_name = "main_2026-01-22"
post_name = "post_exp_2026-01-22"
pre_name = "intro_2026-01-22"

session_code = ["tmjewif2"]  # Jan 21 session on Prolific

# Read experiment file
data = pd.read_csv(f"../data/{main_name}.csv")
meta = pd.read_csv("../../simulations/generated_data/round_metadata.csv")  # load seed and imbalance
post_exp = pd.read_csv(f"../data/{post_name}.csv")  # post experimental data
pre_exp = pd.read_csv(f"../data/{pre_name}.csv")  # pre experiment

### Basic Filters
### --------------
# Keep only relevant sessions
data = data[data["session.code"].isin(session_code)]
# Keep only participants who finished
data = data[data["participant._current_page_name"].isin(["FinalForProlific"])]

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

post_exp["high_education"] = np.where(
    post_exp["player.education"].isin(
        [
            "MBA",
            "PhD",
            "master",
            "undergraduate: 1st year",
            "undergraduate: 2nd year",
            "undergraduate: 3rd year",
            "undergraduate: 4th year",
        ]
    ),
    1,
    0,
)

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
            "high_education",
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
data["investment_share"] = (
        100 * data["investment_amount"] / np.where(data["paid_dummy"] == 1, 95, 100)
)

# add metadata for the given round
data = data.merge(
    meta[
        [
            "round_number",
            "last_imbalance",
            "last_return",
            "next_return",
        ]
    ],
    on="round_number",
    how="left",
)

# # standardizations
# for col in [
#     "round_number",
#     "age",
#     "fin_quiz",
#     "overconfidence",
#     "risk_aversion",
#     "last_imbalance_1",
#     "last_return_1",
#     "imb_difference",
#     "return_difference",
# ]:
#     data[col] = (data[col] - data[col].mean()) / data[col].std()

data.to_csv("../generated_data/processed_panels.csv")
