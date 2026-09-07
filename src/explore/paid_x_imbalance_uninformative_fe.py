"""
Do forecasts and investment respond to Paid × Imbalance when the data are
genuinely uninformative?  Participant and round fixed effects.

"Genuinely uninformative" is the objective DGP state (informative == 0): the
lagged imbalance is pure noise, so the rational response of both the forecast
and the investment share to it is zero.  Any slope on imbalance is
"trading on noise"; the Paid × Imbalance coefficient asks whether that slope
is steeper when the participant paid the E$5 fee for the data.

Sample: rounds in which the participant actually saw the imbalance
(data_available == 1).  Decliners in paid-data rounds see no chart and cannot
respond to imbalance, so they are excluded rather than mixed into the
"free" comparison group.  In this sample Paid == paid_round.

Specification (main):
  Y_it = β1 (Paid_it × Imb_c) + β2 Paid_it
         + β3 (Choose_it × Imb_c) + β4 Choose_it + β5 Imb_c
         + α_i + γ_t + ε_it

  α_i  participant FE (absorbs treated, quiz, demographics, ...)
  γ_t  display-round FE (round_number).  Chart order is shuffled per
       participant, so the chart c(i,t) — and hence Imb_c — still varies
       within display round and β5 stays identified.
  Robustness adds chart FE (series_round), which absorbs Imb_c and
  Informative_c and leaves only the interactions.

Choose_it (chose to pay this round) and Choose_it × Imb_c are always
included: buyers may respond to imbalance more regardless of whether the
fee was actually charged, and Paid × Imb is identified only net of that.
Both are identified from free-data rounds, where choosers and decliners
both see the chart (in paid-data rounds everyone with data is a chooser).

Imbalance is in raw pp and centred at the estimation-sample mean, so the
`paid` main effect is the level effect at average imbalance.

SEs clustered by participant (59 clusters).

Run from repo root:
  .venv/bin/python src/explore/paid_x_imbalance_uninformative_fe.py
"""

from __future__ import annotations

import json
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

ROOT = Path(__file__).resolve().parents[2]
PANEL = ROOT / "data" / "processed" / "processed_panels.csv"
OUT = ROOT / "src" / "explore" / "results_paid_x_imbalance_uninformative.json"

OUTCOMES = {
    "return_forecast": "Return forecast (pp)",
    "investment_share": "Investment share (%)",
}

BASE_TERMS = "paid:imb + paid + pay_choice:imb + pay_choice"
FE_PART = " + C(participant_code) + C(round_number)"
FE_CHART = " + C(series_round)"

KEYS = [
    "paid:imb",
    "paid",
    "pay_choice:imb",
    "pay_choice",
    "imb",
]
POOLED_KEYS = [
    "paid:imb",
    "paid:imb:informative",
    "paid",
    "paid:informative",
    "pay_choice:imb",
    "pay_choice:imb:informative",
    "pay_choice",
    "pay_choice:informative",
    "imb",
    "imb:informative",
]


def load() -> pd.DataFrame:
    df = pd.read_csv(PANEL)
    df["paid"] = df["paid_dummy"].astype(int)
    df["pay_choice"] = df["pay_for_data"].astype(int)
    df["imb"] = df["last_imbalance_1"]
    df["informative"] = df["informative"].astype(int)
    return df


def fit(y: str, data: pd.DataFrame, rhs: str):
    d = data.dropna(subset=[y, "imb", "paid", "pay_choice"]).reset_index(drop=True)
    d["imb"] = d["imb"] - d["imb"].mean()
    groups = pd.factorize(d["participant_code"])[0]
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        model = smf.ols(f"{y} ~ {rhs}", data=d).fit(
            cov_type="cluster", cov_kwds={"groups": groups}
        )
    model._n_people = d["participant_code"].nunique()
    return model


def stars(p: float) -> str:
    return "***" if p < 0.01 else "**" if p < 0.05 else "*" if p < 0.1 else ""


def print_model(title: str, model, keys):
    print(f"\n{title}")
    print(f"  N={int(model.nobs)}  participants={model._n_people}  R2={model.rsquared:.3f}")
    for k in keys:
        if k in model.params.index:
            b, se, p = model.params[k], model.bse[k], model.pvalues[k]
            if not np.isfinite(se):
                raise RuntimeError(f"non-finite clustered SE for {k}")
            lo, hi = model.conf_int().loc[k]
            print(
                f"  {k:28s} {b:8.3f}  ({se:.3f})  p={p:.3f}{stars(p):3s}"
                f"  95% CI [{lo:.3f}, {hi:.3f}]"
            )


def collect(model, keys) -> dict:
    out = {"N": int(model.nobs), "participants": model._n_people, "R2": model.rsquared}
    for k in keys:
        if k in model.params.index:
            lo, hi = model.conf_int().loc[k]
            out[k] = {
                "coef": float(model.params[k]),
                "se": float(model.bse[k]),
                "p": float(model.pvalues[k]),
                "ci95": [float(lo), float(hi)],
            }
    return out


def raw_slopes(seen: pd.DataFrame, y: str) -> dict:
    """OLS slope of y on imbalance by (informative, paid) cell, no FE."""
    res = {}
    print(f"\n  raw slope of {y} on imbalance (no FE):")
    for inf in (0, 1):
        for paid in (0, 1):
            d = seen[(seen.informative == inf) & (seen.paid == paid)]
            b = np.polyfit(d["imb"], d[y], 1)[0]
            res[f"informative={inf},paid={paid}"] = {"slope": float(b), "n": int(len(d))}
            print(f"    informative={inf} paid={paid}:  {b:7.3f}  (n={len(d)})")
    return res


def main():
    df = load()
    seen = df[df["data_available"] == 1].copy()
    uninf = seen[seen["informative"] == 0].copy()
    inf = seen[seen["informative"] == 1].copy()

    print("=== Sample: rounds with visible data ===")
    print(
        f"  all: rows={len(seen)} people={seen.participant_code.nunique()} "
        f"paid={seen.paid.mean():.3f} choose={seen.pay_choice.mean():.3f}"
    )
    print(
        f"  uninformative: rows={len(uninf)} people={uninf.participant_code.nunique()} "
        f"paid={uninf.paid.mean():.3f}  "
        f"people with both paid & free noise rounds="
        f"{int((uninf.groupby('participant_code').paid.nunique() == 2).sum())}"
    )
    print(
        f"  imbalance in noise rounds: sd={uninf.imb.std():.2f}  "
        f"range=[{uninf.imb.min():.1f}, {uninf.imb.max():.1f}]"
    )
    print(f"  sessions: {seen.groupby('session_id').participant_code.nunique().to_dict()}")

    results: dict = {"sample": {"seen": len(seen), "uninformative": len(uninf)}}

    for y, label in OUTCOMES.items():
        print(f"\n\n################  {label}  ################")
        results[y] = {}
        results[y]["raw_slopes"] = raw_slopes(seen, y)

        # (1) Main: uninformative rounds, participant + display-round FE
        m1 = fit(y, uninf, BASE_TERMS + " + imb" + FE_PART)
        print_model(
            "(1) Uninformative rounds | participant + round FE", m1, KEYS
        )
        results[y]["uninf_part_round_fe"] = collect(m1, KEYS)

        # (2) Robustness: add chart FE (absorbs imbalance main effect)
        m2 = fit(y, uninf, BASE_TERMS + FE_PART + FE_CHART)
        print_model(
            "(2) Uninformative rounds | participant + round + chart FE", m2, KEYS
        )
        results[y]["uninf_part_round_chart_fe"] = collect(m2, KEYS)

        # (3) Benchmark: informative rounds, same spec as (1)
        m3 = fit(y, inf, BASE_TERMS + " + imb" + FE_PART)
        print_model(
            "(3) Informative rounds (benchmark) | participant + round FE", m3, KEYS
        )
        results[y]["inf_part_round_fe"] = collect(m3, KEYS)

        # (4) Pooled with triple interaction: is Paid × Imb different in noise vs signal?
        pooled_rhs = (
            "paid:imb + paid:imb:informative + paid + paid:informative"
            " + pay_choice:imb + pay_choice:imb:informative"
            " + pay_choice + pay_choice:informative"
            " + imb + imb:informative + informative" + FE_PART
        )
        m4 = fit(y, seen, pooled_rhs)
        print_model(
            "(4) All visible rounds, pooled | participant + round FE\n"
            "    ('paid:imb' = effect in noise rounds; "
            "'paid:imb:informative' = difference for signal rounds)",
            m4,
            POOLED_KEYS,
        )
        results[y]["pooled_part_round_fe"] = collect(m4, POOLED_KEYS)

        # (5) Uninformative rounds split by the participant's own belief.
        #     Belief is elicited after seeing the data and could itself
        #     respond to payment, so this is descriptive, not causal.
        for bel, tag in ((1, "believes informative"), (0, "believes noise")):
            sub = uninf[uninf["belief_informative"] == bel]
            m5 = fit(y, sub, BASE_TERMS + " + imb" + FE_PART)
            print_model(
                f"(5) Uninformative rounds, {tag} | participant + round FE",
                m5,
                KEYS,
            )
            results[y][f"uninf_belief{bel}_part_round_fe"] = collect(m5, KEYS)

        # (6) By session, main spec
        for sid, sub in uninf.groupby("session_id"):
            m6 = fit(y, sub, BASE_TERMS + " + imb" + FE_PART)
            print_model(
                f"(6) Uninformative rounds, session {sid} | participant + round FE",
                m6,
                KEYS,
            )
            results[y][f"uninf_session_{sid}"] = collect(m6, KEYS)

    OUT.write_text(json.dumps(results, indent=2))
    print(f"\nWrote {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
