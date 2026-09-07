"""
Beliefs-when-uninformative (mistakes) and confidence.

Same controls as the forecast/investment spec:
  Y ~ paid * imbalance + choose_to_pay * imbalance + round FE
SEs clustered by participant.

Beliefs are elicited only when data is visible, so the mistake sample is
uninformative rounds with data_available == 1.

Run from repo root:
  .venv/bin/python src/explore/beliefs_confidence_fe.py
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

ROOT = Path(__file__).resolve().parents[2]
PANEL = ROOT / "data" / "processed" / "processed_panels.csv"
RAW = [
    ("20260824", "2026-08-24"),
    ("20260904", "2026-09-04"),
]


def load() -> pd.DataFrame:
    df = pd.read_csv(PANEL)
    extras = []
    for sid, date in RAW:
        extras.append(
            pd.read_csv(
                ROOT / "data" / "raw" / sid / f"main_{date}.csv",
                usecols=[
                    "participant.code",
                    "player.inner_round_number",
                    "player.forecast_confidence",
                    "player.belief_confidence",
                ],
            ).rename(
                columns={
                    "participant.code": "participant_code",
                    "player.inner_round_number": "round_number",
                    "player.forecast_confidence": "forecast_confidence",
                    "player.belief_confidence": "belief_confidence",
                }
            )
        )
    extra = pd.concat(extras, ignore_index=True).drop_duplicates(
        ["participant_code", "round_number"]
    )
    df = df.merge(extra, on=["participant_code", "round_number"], how="left")
    df["paid"] = df["paid_dummy"].astype(int)
    df["pay_choice"] = df["pay_for_data"].astype(int)
    df["uninformative"] = (1 - df["informative"]).astype(int)
    df["abs_imb"] = df["last_imbalance_1"].abs()
    return df


def fit(y: str, data: pd.DataFrame, formula: str):
    d = data.dropna(
        subset=[y, "paid", "pay_choice", "last_imbalance_1", "round_number"]
    ).reset_index(drop=True)
    groups = np.column_stack(
        [
            pd.factorize(d["participant_code"])[0],
            d["round_number"].to_numpy(),
        ]
    )
    return smf.ols(f"{y} ~ {formula}", data=d).fit(
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
            print(
                f"  {k:32s} {model.params[k]:8.3f}  ({model.bse[k]:.3f})  p={p:.3f}{stars}"
            )


def cells(df: pd.DataFrame, y: str):
    print(f"\n  raw means of {y} by paid × informative:")
    for inf in (0, 1):
        for paid in (0, 1):
            s = df[(df.informative == inf) & (df.paid == paid)][y]
            if len(s) == 0:
                continue
            print(
                f"    informative={inf} paid={paid}:  {s.mean():.3f}  "
                f"(sd={s.std():.3f}, n={len(s)})"
            )


# Saturated: payment (and selection) separately in each DGP state.
# paid = paid:uninformative + paid:informative, so no main paid term.
SPEC = (
    "paid:uninformative + paid:informative"
    " + pay_choice:uninformative + pay_choice:informative"
    " + informative + round_number"
)
KEYS = [
    "paid:uninformative",
    "paid:informative",
    "pay_choice:uninformative",
    "pay_choice:informative",
    "informative",
    "round_number",
]


def main():
    df = load()

    # Beliefs elicited only when the chart is visible.
    seen = df[df["data_available"] == 1].copy()
    print("=== Visible-data rounds; Paid × Uninformative and Paid × Informative ===")
    print(
        f"  rows={len(seen)}  people={seen.participant_code.nunique()}  "
        f"belief informative={seen.belief_informative.mean():.3f}  "
        f"true informative={seen.informative.mean():.3f}"
    )
    print(f"  paid={seen.paid.mean():.3f}  choose={seen.pay_choice.mean():.3f}")
    cells(seen, "belief_informative")
    cells(seen, "belief_confidence")
    cells(seen, "forecast_confidence")

    print_model(
        "Belief informative (LPM)  |  linear round, two-way cluster",
        fit("belief_informative", seen, SPEC),
        KEYS,
    )
    print_model(
        "Belief confidence (1-5)",
        fit("belief_confidence", seen, SPEC),
        KEYS,
    )
    print_model(
        "Forecast confidence (1-5)",
        fit("forecast_confidence", seen, SPEC),
        KEYS,
    )

    for sid, sub in seen.groupby("session_id"):
        print(f"\n--- session {sid}  n={len(sub)} ---")
        print_model("  belief", fit("belief_informative", sub, SPEC), KEYS)
        print_model("  belief conf", fit("belief_confidence", sub, SPEC), KEYS)
        print_model("  forecast conf", fit("forecast_confidence", sub, SPEC), KEYS)


if __name__ == "__main__":
    main()
