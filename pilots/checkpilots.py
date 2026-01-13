import pandas as pd

main_name="main_2026-01-12"
session_code="461q1n1d"

data=pd.read_csv(f"{main_name}.csv")

# keep only relevant session
data=data[data["session.code"] == session_code]
# keep only participants who finished
data=data[data['participant._index_in_pages']==data['participant._max_page_index'].mean()]

data[data['player.round_type']=='paid_data'].groupby('player.condition')['player.pay_for_data'].mean()