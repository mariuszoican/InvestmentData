import pandas as pd
import numpy as np

data = pd.read_csv("../data/pricing_2026-07-02.csv")
data = data[data["session.code"] == "cbctgbhm"]
data = data[data["participant._current_page_name"] == "FinalForProlific"]

payoffs = data[["participant.label", "participant.payoff"]].reset_index(drop=True)
payoffs["payoff_gbp"] = payoffs["participant.payoff"] * 0.02

payoffs["prolific"] = (
    payoffs["participant.label"]
    + ", "
    + payoffs["payoff_gbp"].apply(lambda x: round(x, 2)).map(str)
)

payoffs["prolific"].to_csv(f"../data/bonuses.csv", index=False)

data = data.rename(
    columns={
        "session.code": "session_code",
        "participant.code": "participant_code",
        "player.offer_price": "offer_price",
        "player.transaction_price": "transaction_price",
        "player.discount": "discount",
        "player.purchased": "purchased",
        "player.last_return": "last_return",
        "player.last_imbalance": "last_imbalance",
        "player.imbalance_was_informative": "informative",
        "player.imbalance_informative": "belief_informative",
        "player.belief_confidence": "belief_confidence",
        "player.return_forecast": "return_forecast",
        "player.forecast_confidence": "forecast_confidence",
        "player.investment_amount": "investment_amount",
        "player.age": "age",
        "player.gender": "gender",
        "player.education": "education",
        "player.finance_course": "finance_course",
        "player.fin_literacy_score": "fin_literacy_score",
    }
)

data["gender_female"] = np.where(data["gender"] == "female", 1, 0)
data["graduate_education"] = np.where(data["education"] == "graduate", 1, 0)

cols = [
    "session_code",
    "participant_code",
    "offer_price",
    "transaction_price",
    "discount",
    "purchased",
    "last_return",
    "last_imbalance",
    "informative",
    "belief_informative",
    "belief_confidence",
    "return_forecast",
    "forecast_confidence",
    "investment_amount",
    "age",
    "gender",
    "gender_female",
    "graduate_education",
    "education",
    "finance_course",
    "fin_literacy_score",
]

data = data[cols]

data.to_csv(f"../data/processed_data.csv", index=False)
