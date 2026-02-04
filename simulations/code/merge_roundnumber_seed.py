# merge_roundnumber_seed.py

from pathlib import Path
import pandas as pd

ROOT = Path.cwd().parent
DATA = ROOT / "generated_data"

df = pd.read_csv(DATA / "consolidated_simulation_results.csv", index_col=0)

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

round_df = pd.DataFrame(list(roundnumber_seed.items()), columns=["round_number", "seed"])

df_merged = pd.merge(df, round_df, on="seed", how="left")
df_merged = df_merged.dropna()
df_merged["round_number"] = df_merged["round_number"].astype(int)

# output
output_file = DATA / "round_metadata.csv"
df_merged.to_csv(output_file, index=False)

print("Saved:", output_file)
