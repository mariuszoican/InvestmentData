
# merge_roundnumber_seed.py
import pandas as pd

df = pd.read_csv("consolidated_simulation_results.csv", index_col=0)


roundnumber_seed = {
    1: 22,
    2: 33,
    3: 154,
    4: 260,
    5: 49,
    6: 58,
    7: 320,
    8: 60,
    9: 101,
    10: 334,
    11: 174,
    12: 418,
    13: 429,
    14: 190,
}
round_df = pd.DataFrame(
    list(roundnumber_seed.items()), columns=["round_number", "seed"]
)
df_merged = pd.merge(df, round_df, on="seed", how="left")
df_merged = df_merged.dropna()
df_merged["round_number"] = df_merged["round_number"].astype(int)
df_merged.to_csv("round_metadata.csv")
