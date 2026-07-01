import pandas as pd

post_name = "post_exp_2026-07-01"
session_code = ["4ovtf4e6"]  # Jan 17, desktop only

data = pd.read_csv(f"../raw_data/{post_name}.csv")  # post experimental raw_data
# Keep only relevant sessions
data = data[data["session.code"].isin(session_code)]
# Keep only participants who finished
data = data[data["participant._current_page_name"].isin(["FinalForProlific"])]

data["final_payoff"] = data["player.payoff"] + data["player.payoff_for_quiz"]

payoffs = data[["participant.label", "final_payoff"]]
rate = 0.03
payoffs["payoff_gbp"] = payoffs["final_payoff"] * rate
payoffs["prolific"] = (
    payoffs["participant.label"]
    + ", "
    + payoffs["payoff_gbp"].apply(lambda x: round(x, 2)).map(str)
)

payoffs["prolific"].to_csv(f"../processed_data/bonuses.csv", index=False)
