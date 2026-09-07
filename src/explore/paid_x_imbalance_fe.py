"""
Forecast and investment on Paid × Imbalance among choosers in informative rounds.

Full main-round sample; informative is a control, not a sample restriction.

Paid is 1 only when the participant both chose to pay and the round is a
binding paid-data draw. Participants who declined in a paid-data round do
not see imbalance.

Specification:
  Y_it = β1 (Paid_it × Imbalance_t) + β2 Imbalance_t + β3 Paid_it
         + β4 (Choose_it × Imbalance_t) + β5 Choose_it
         + β6 Informative_t + γ_t + ε_it

Display-round FE (γ_t) only. SEs clustered by participant.

Y ∈ {return_forecast, investment_share}.

Run from repo root:
  .venv/bin/python src/explore/paid_x_imbalance_fe.py
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

ROOT = Path(__file__).resolve().parents[2]
PANEL = ROOT / "data" / "processed" / "processed_panels.csv"


def fit(y: str, data: pd.DataFrame, extra: str = ""):
    formula = (
        f"{y} ~ paid * last_imbalance_1 + pay_choice * last_imbalance_1"
        " + informative + round_number"
        + extra
    )
    groups = np.column_stack(
        [
            pd.factorize(data["participant_code"])[0],
            data["round_number"].to_numpy(),
        ]
    )
    return smf.ols(formula, data=data).fit(
        cov_type="cluster",
        cov_kwds={"groups": groups},
    )


def print_model(title: str, model, keys):
    print(f"\n{title}")
    print(f"  N={int(model.nobs)}  R2={model.rsquared:.3f}")
    for k in keys:
        if k in model.params.index:
            p = model.pvalues[k]
            stars = "***" if p < 0.01 else "**" if p < 0.05 else "*" if p < 0.1 else ""
            print(f"  {k:32s} {model.params[k]:8.3f}  ({model.bse[k]:.3f})  p={p:.3f}{stars}")


def data_n_clusters(model) -> int:
    return int(model.n_groups) if hasattr(model, "n_groups") else int(
        getattr(model, "_cluster_nobs", 0) or 0
    )


def main():
    df = pd.read_csv(PANEL)
    df["paid"] = df["paid_dummy"].astype(int)
    df["pay_choice"] = df["pay_for_data"].astype(int)

    sample = df.copy()
    print("=== Sample: all main rounds; informative as control ===")
    print(f"  rows={len(sample)}  participants={sample.participant_code.nunique()}")
    print(f"  paid share={sample.paid.mean():.3f}")
    print(f"  data available={sample.data_available.mean():.3f}")
    print(f"  chose to pay={sample.pay_choice.mean():.3f}")
    print(f"  informative={sample.informative.mean():.3f}")
    print(f"  sessions: {sample.groupby('session_id').participant_code.nunique().to_dict()}")
    print(
        f"  imbalance: mean={sample.last_imbalance_1.mean():.2f}  "
        f"sd={sample.last_imbalance_1.std():.2f}"
    )

    keys = [
        "paid:last_imbalance_1",
        "pay_choice:last_imbalance_1",
        "last_imbalance_1",
        "paid",
        "pay_choice",
        "informative",
        "round_number",
    ]

    m_fc = fit("return_forecast", sample)
    print_model("Return forecast  |  linear round, two-way cluster", m_fc, keys)
    print(f"  clusters={sample.participant_code.nunique()}")

    m_inv = fit("investment_share", sample)
    print_model("Investment share (%)  |  linear round, two-way cluster", m_inv, keys)
    print(f"  clusters={sample.participant_code.nunique()}")

    # Same spec + last return (paper control)
    m_fc2 = fit("return_forecast", sample, " + last_return_1")
    print_model("Return forecast  |  + last return", m_fc2, keys + ["last_return_1"])

    m_inv2 = fit("investment_share", sample, " + last_return_1")
    print_model("Investment share  |  + last return", m_inv2, keys + ["last_return_1"])

    # By session
    for sid, sub in sample.groupby("session_id"):
        print(f"\n--- session {sid}  n={len(sub)} people={sub.participant_code.nunique()} ---")
        print_model("  forecast", fit("return_forecast", sub), keys)
        print_model("  investment", fit("investment_share", sub), keys)


if __name__ == "__main__":
    main()
