import pandas as pd

post_name = "post_exp_2026-01-21"
session_code = ["tmjewif2"]  # Jan 17, desktop only

data = pd.read_csv(f"../data/{post_name}.csv")  # post experimental data
# Keep only relevant sessions
data = data[data["session.code"].isin(session_code)]
# Keep only participants who finished
data = data[data["participant._current_page_name"].isin(["FinalForProlific"])]

data["final_payoff"] = data["player.payoff"] + data["player.payoff_for_quiz"]

payoffs = data[["participant.label", "final_payoff"]]
rate = 0.03
payoffs["payoff_gbp"] = payoffs["final_payoff"] * rate
