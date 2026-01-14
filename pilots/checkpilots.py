import numpy as np
import pandas as pd
import pyfixest as pf

main_name = "main_2026-01-13"
# session_code="461q1n1d" # January 12, Data price = 4
# session_code = "4pnyq9ay"  # January 13, Data price = 6
session_code = ["m5x4bbn3"]  # January 13, Data price = 5
# #session_code = ["461q1n1d", "4pnyq9ay", "m5x4bbn3"]


# Read experiment file
data = pd.read_csv(f"{main_name}.csv")
meta = pd.read_csv("../simulations/round_metadata.csv")  # load seed and imbalance

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
}

m1 = pf.feols(
    "belief_informative ~ treated + treated_paychoice + treated_payround + last_imbalance + informative + round_number",
    data=data,
    vcov={"CRV3": "participant_code+round_number"},
)

m2 = pf.feols(
    "belief_informative ~ treated + treated_paychoice + treated_payround + last_imbalance +  informative",
    data=data,
    vcov={"CRV3": "participant_code+round_number"},
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
