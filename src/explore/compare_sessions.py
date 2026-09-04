"""Compare Aug 24 vs Sept 4 lab sessions on the paper's specifications.

Writes src/explore/compare_sessions.json for the canvas.
Run from the repo root:  python src/explore/compare_sessions.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
from scipy import stats

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src" / "build"))

from process_panels import process_panels  # noqa: E402

PANEL = ROOT / "data" / "processed" / "processed_panels.csv"
OUT = Path(__file__).resolve().parent / "compare_sessions.json"

MU = 15.0
SESSION_LABELS = {"9vfoiax5": "20260824", "sttmxluq": "20260904"}
EXTRA_COLS = [
    "participant.code",
    "player.inner_round_number",
    "player.forecast_confidence",
    "player.belief_confidence",
    "player.investment_payoff",
    "player.round_payoff",
    "player.realized_return",
]


def tstars(p: float) -> str:
    return "***" if p < 0.01 else "**" if p < 0.05 else "*" if p < 0.1 else ""


def fmt_coef(coef: float, se: float, p: float, digits: int = 2) -> str:
    return f"{coef:.{digits}f}{tstars(p)} ({se:.{digits}f})"


def coef_pack(model, keys: list[str]) -> dict:
    out = {}
    for k in keys:
        if k in model.params.index:
            out[k] = {
                "coef": float(model.params[k]),
                "se": float(model.bse[k]),
                "p": float(model.pvalues[k]),
                "ci95_lo": float(model.params[k] - 1.96 * model.bse[k]),
                "ci95_hi": float(model.params[k] + 1.96 * model.bse[k]),
            }
    out["nobs"] = int(model.nobs)
    out["r2"] = float(model.rsquared)
    out["n_clusters"] = int(model.n_groups) if hasattr(model, "n_groups") else None
    return out


def iv_2sls(df: pd.DataFrame, y_col: str, endog: list[str], instruments: list[str],
            exog: list[str], cluster_col: str) -> dict:
    cols = [y_col] + endog + instruments + exog + [cluster_col]
    d = df.dropna(subset=[c for c in cols if c in df.columns]).copy()
    y = d[y_col].to_numpy(float)
    X = np.column_stack([d[c].to_numpy(float) for c in endog + exog] + [np.ones(len(d))])
    Z = np.column_stack([d[c].to_numpy(float) for c in instruments + exog] + [np.ones(len(d))])
    names = endog + exog + ["const"]

    ZX = Z.T @ X
    Zy = Z.T @ y
    beta = np.linalg.solve(ZX, Zy)
    e = y - X @ beta

    meat = np.zeros((Z.shape[1], Z.shape[1]))
    for _, idx in d.groupby(cluster_col).indices.items():
        Zg = Z[idx]
        eg = e[idx]
        s = Zg.T @ eg
        meat += np.outer(s, s)
    ZX_inv = np.linalg.inv(ZX)
    V = ZX_inv @ meat @ ZX_inv.T
    G = d[cluster_col].nunique()
    n, k = X.shape
    V *= G / (G - 1) * (n - 1) / (n - k)
    se = np.sqrt(np.diag(V))
    tvals = beta / se
    pvals = 2 * stats.t.sf(np.abs(tvals), df=G - 1)
    out = {
        "names": names,
        "nobs": int(n),
        "n_clusters": int(G),
    }
    for name, b, s, p in zip(names, beta, se, pvals):
        out[name] = {
            "coef": float(b),
            "se": float(s),
            "p": float(p),
            "ci95_lo": float(b - 1.96 * s),
            "ci95_hi": float(b + 1.96 * s),
        }
    return out


def load_extra() -> pd.DataFrame:
    frames = []
    for sid, date in [("20260824", "2026-08-24"), ("20260904", "2026-09-04")]:
        raw = pd.read_csv(
            ROOT / "data" / "raw" / sid / f"main_{date}.csv",
            usecols=lambda c: c in EXTRA_COLS,
        ).rename(
            columns={
                "participant.code": "participant_code",
                "player.inner_round_number": "round_number",
                "player.forecast_confidence": "forecast_confidence",
                "player.belief_confidence": "belief_confidence",
                "player.investment_payoff": "investment_payoff",
                "player.round_payoff": "round_payoff",
                "player.realized_return": "realized_return",
            }
        )
        frames.append(raw)
    return pd.concat(frames, ignore_index=True).drop_duplicates(
        ["participant_code", "round_number"]
    )


def load_data() -> pd.DataFrame:
    df = pd.read_csv(PANEL)
    df["lab_session"] = df["session_id"].map(SESSION_LABELS)
    extra = load_extra()
    df = df.merge(extra, on=["participant_code", "round_number"], how="left")
    df["main_round"] = df["round_number"] - 2
    df["cond_exp_return"] = MU + df["informative"] * df["last_imbalance_1"]
    df["forecast_error"] = (df["return_forecast"] - df["cond_exp_return"]).abs()
    df["paid"] = df["paid_dummy"].astype(int)
    df["pay_choice"] = df["pay_for_data"].astype(int)
    df["uninformative"] = 1 - df["informative"]
    df["paid_x_uninf"] = df["paid"] * df["uninformative"]
    df["pos_imb"] = (df["last_imbalance_1"] > 0).astype(int)
    person = df.groupby("participant_code")["fin_quiz"].first()
    df["high_quiz"] = (df["fin_quiz"] >= person.median()).astype(int)
    return df


def summarize(df: pd.DataFrame) -> dict:
    person = df.groupby("participant_code").agg(
        fin_quiz=("fin_quiz", "first"),
        overconfidence=("overconfidence", "first"),
        age=("age", "first"),
        female=("gender_female", "first"),
        risk_aversion=("risk_aversion", "first"),
        trading_exp=("trading_experience", "first"),
        finance_course=("finance_course", "first"),
        pay_rate=("pay_choice", "mean"),
        treated=("treated", "first"),
    )
    da = df[df["data_available"] == 1]
    acc = (da["belief_informative"] == da["informative"]).mean()
    return {
        "n_participants": int(len(person)),
        "n_obs": int(len(df)),
        "n_treated": int(person["treated"].sum()),
        "share_treated": float(person["treated"].mean()),
        "choose_pay_rate": float(df["pay_choice"].mean()),
        "share_always_pay": float((person["pay_rate"] == 1).mean()),
        "share_never_pay": float((person["pay_rate"] == 0).mean()),
        "mean_invest_share": float(df["investment_share"].mean()),
        "mean_forecast": float(df["return_forecast"].mean()),
        "belief_when_informative": float(
            da.loc[da.informative == 1, "belief_informative"].mean()
        ),
        "belief_when_uninformative": float(
            da.loc[da.informative == 0, "belief_informative"].mean()
        ),
        "belief_gap": float(
            da.loc[da.informative == 1, "belief_informative"].mean()
            - da.loc[da.informative == 0, "belief_informative"].mean()
        ),
        "belief_accuracy": float(acc),
        "mean_fin_quiz": float(person["fin_quiz"].mean()),
        "quiz_median": float(person["fin_quiz"].median()),
        "mean_overconfidence": float(person["overconfidence"].mean()),
        "mean_age": float(person["age"].mean()),
        "share_female": float(person["female"].mean()),
        "share_trading_exp": float(person["trading_exp"].mean()),
        "share_finance_course": float(person["finance_course"].mean()),
        "mean_risk_aversion": float(person["risk_aversion"].mean()),
        "pay_rate_p50": float(person["pay_rate"].median()),
    }


def run_h1(df: pd.DataFrame) -> dict:
    d = df[df["data_available"] == 1].copy()
    f = (
        "belief_informative ~ paid_x_uninf + paid + informative + pay_choice"
        " + main_round + last_return_1 + last_imbalance_1"
    )
    keys = ["paid_x_uninf", "paid", "informative", "pay_choice"]
    m = smf.ols(f, data=d).fit(
        cov_type="cluster", cov_kwds={"groups": d["participant_code"]}
    )
    cells = {}
    for paid in (0, 1):
        for inf in (0, 1):
            sub = d[(d.paid == paid) & (d.informative == inf)]["belief_informative"]
            cells[f"paid{paid}_inf{inf}"] = {
                "mean": float(sub.mean()),
                "se": float(sub.std() / np.sqrt(len(sub))) if len(sub) else None,
                "n": int(len(sub)),
            }
    return {"ols": coef_pack(m, keys), "cells": cells, "n_clusters": int(d.participant_code.nunique())}


def run_h2(df: pd.DataFrame) -> dict:
    d = df[df["data_available"] == 1].copy()
    d["paid_x_imb"] = d["paid"] * d["last_imbalance_1"]
    d["choice_x_imb"] = d["pay_choice"] * d["last_imbalance_1"]
    f = (
        "return_forecast ~ paid_x_imb + last_imbalance_1 + paid + choice_x_imb"
        " + pay_choice + last_return_1 + main_round"
    )
    keys = ["paid_x_imb", "last_imbalance_1", "paid", "choice_x_imb"]
    bel = d[d.belief_informative == 1]
    plc = d[d.belief_informative == 0]
    m = smf.ols(f, data=bel).fit(
        cov_type="cluster", cov_kwds={"groups": bel["participant_code"]}
    )
    m_p = smf.ols(f, data=plc).fit(
        cov_type="cluster", cov_kwds={"groups": plc["participant_code"]}
    )
    return {
        "believers": coef_pack(m, keys),
        "placebo": coef_pack(m_p, keys),
        "n_clusters": int(bel.participant_code.nunique()),
    }


def run_h2b(df: pd.DataFrame) -> dict:
    d = df[(df["data_available"] == 1) & (df["informative"] == 0)].copy()
    f = "forecast_error ~ paid + pay_choice + last_imbalance_1 + last_return_1 + main_round"
    m = smf.ols(f, data=d).fit(
        cov_type="cluster", cov_kwds={"groups": d["participant_code"]}
    )
    cells = {}
    for paid in (0, 1):
        sub = d[d.paid == paid]["forecast_error"]
        cells[f"paid{paid}"] = {
            "mean": float(sub.mean()),
            "se": float(sub.std() / np.sqrt(len(sub))),
            "n": int(len(sub)),
        }
    return {"ols": coef_pack(m, ["paid"]), "cells": cells}


def run_h34(df: pd.DataFrame) -> dict:
    d = df[(df["data_available"] == 1) & (df["belief_informative"] == 1)].copy()
    d["fc_c"] = d["return_forecast"] - d["return_forecast"].mean()
    d["lr_c"] = d["last_return_1"] - d["last_return_1"].mean()
    d["imb_c"] = d["last_imbalance_1"] - d["last_imbalance_1"].mean()
    d["paid_x_imb"] = d["paid"] * d["imb_c"]
    d["forecast_x_paid"] = d["fc_c"] * d["paid"]
    d["lastret_x_paid"] = d["lr_c"] * d["paid"]
    d["return_forecast"] = d["fc_c"]
    d["last_imbalance_1"] = d["imb_c"]
    d["last_return_1"] = d["lr_c"]
    exog = [
        "paid", "pay_choice", "main_round", "last_return_1", "lastret_x_paid",
        "gender_female", "fin_quiz", "overconfidence",
    ]
    res = iv_2sls(
        d,
        y_col="investment_share",
        endog=["return_forecast", "forecast_x_paid"],
        instruments=["last_imbalance_1", "paid_x_imb"],
        exog=exog,
        cluster_col="participant_code",
    )
    cells = {}
    raw = df[(df["data_available"] == 1) & (df["belief_informative"] == 1)]
    for paid in (0, 1):
        s = raw[raw.paid == paid]["investment_share"]
        cells[f"paid{paid}"] = {
            "mean": float(s.mean()),
            "se": float(s.std() / np.sqrt(len(s))),
            "n": int(len(s)),
        }
    return {"iv": res, "cells": cells}


def run_h5(df: pd.DataFrame) -> dict:
    d = df.copy()
    d["oc_std"] = (d["overconfidence"] - d["overconfidence"].mean()) / d["overconfidence"].std()
    d["quiz_std"] = (d["fin_quiz"] - d["fin_quiz"].mean()) / d["fin_quiz"].std()
    d["ra_std"] = (d["risk_aversion"] - d["risk_aversion"].mean()) / d["risk_aversion"].std()
    f = (
        "pay_choice ~ oc_std + quiz_std + ra_std + gender_female + age"
        " + trading_experience + high_education + C(main_round)"
    )
    keys = ["oc_std", "quiz_std", "ra_std", "gender_female"]
    m = smf.ols(f, data=d).fit(
        cov_type="cluster", cov_kwds={"groups": d["participant_code"]}
    )
    d = d.sort_values(["participant_code", "main_round"])
    g = d.groupby("participant_code")
    d["prev_informative"] = g["informative"].shift(1)
    d["prev_paid"] = g["paid"].shift(1)
    d["prev_return"] = g["realized_return"].shift(1)
    d["prev_paid_x_uninf"] = d["prev_paid"] * (1 - d["prev_informative"])
    f_dyn = (
        "pay_choice ~ prev_paid + prev_paid_x_uninf + prev_informative"
        " + prev_return + main_round"
    )
    dd = d.dropna(subset=["prev_paid", "prev_informative", "prev_return", "prev_paid_x_uninf"])
    m_dyn = smf.ols(f_dyn, data=dd).fit(
        cov_type="cluster", cov_kwds={"groups": dd["participant_code"]}
    )
    return {
        "who": coef_pack(m, keys),
        "dynamics": coef_pack(m_dyn, ["prev_paid", "prev_paid_x_uninf", "prev_informative"]),
    }


def round_dynamics(df: pd.DataFrame) -> list[dict]:
    dyn = (
        df.groupby("main_round")
        .agg(
            pay_rate=("pay_choice", "mean"),
            invest=("investment_share", "mean"),
            belief=("belief_informative", "mean"),
        )
        .reset_index()
    )
    return dyn.round(4).to_dict(orient="records")


def analyze_sample(df: pd.DataFrame) -> dict:
    person = df.groupby("participant_code")["fin_quiz"].first()
    d = df.copy()
    d["high_quiz"] = (d["fin_quiz"] >= person.median()).astype(int)
    return {
        "summary": summarize(d),
        "h1": run_h1(d),
        "h2": run_h2(d),
        "h2b": run_h2b(d),
        "h34": run_h34(d),
        "h5": run_h5(d),
        "round_dynamics": round_dynamics(d),
    }


def main():
    print("Rebuilding panels…")
    process_panels()
    df = load_data()
    print(df.groupby("lab_session")["participant_code"].nunique())

    out = {
        "aug": analyze_sample(df[df.lab_session == "20260824"]),
        "sep": analyze_sample(df[df.lab_session == "20260904"]),
        "pooled": analyze_sample(df),
        "prolific": {
            "n_participants": 771,
            "choose_pay_rate": 0.56,
            "mean_invest_share": 45.8,
            "belief_when_informative": 0.75,
            "belief_when_uninformative": 0.68,
            "belief_gap": 0.07,
            "mean_fin_quiz": 0.76,
            "mean_overconfidence": -0.21,
            "mean_age": 45.7,
            "share_female": 0.50,
            "share_trading_exp": 0.64,
            "share_finance_course": 0.33,
            "h1_paid_x_uninf": 0.08,
            "h2_paid_x_imb_rel": 0.31,
            "h2b_paid": 1.08,
            "h3_paid": 7.16,
            "h4_forecast_x_paid": -0.37,
            "h4_forecast": 2.48,
            "h5_oc": 0.05,
        },
    }
    OUT.write_text(json.dumps(out, indent=2, default=float))
    print(f"Wrote {OUT}")

    for name in ("aug", "sep", "pooled"):
        s = out[name]["summary"]
        h1 = out[name]["h1"]["ols"]["paid_x_uninf"]
        h2 = out[name]["h2"]["believers"]
        h3 = out[name]["h34"]["iv"]["paid"]
        h4f = out[name]["h34"]["iv"]["return_forecast"]
        h4x = out[name]["h34"]["iv"]["forecast_x_paid"]
        h5 = out[name]["h5"]["who"]["oc_std"]
        print(
            f"\n{name}: n={s['n_participants']} take-up={s['choose_pay_rate']:.2f} "
            f"gap={s['belief_gap']:.2f} acc={s['belief_accuracy']:.2f}"
        )
        print(f"  H1 Paid×Uninf {fmt_coef(h1['coef'], h1['se'], h1['p'])}")
        print(
            f"  H2 slope {fmt_coef(h2['last_imbalance_1']['coef'], h2['last_imbalance_1']['se'], h2['last_imbalance_1']['p'])}"
            f"  Paid×imb {fmt_coef(h2['paid_x_imb']['coef'], h2['paid_x_imb']['se'], h2['paid_x_imb']['p'])}"
        )
        print(
            f"  H3 Paid {fmt_coef(h3['coef'], h3['se'], h3['p'])}  "
            f"H4 forecast {fmt_coef(h4f['coef'], h4f['se'], h4f['p'])}  "
            f"F×Paid {fmt_coef(h4x['coef'], h4x['se'], h4x['p'])}"
        )
        print(f"  H5 OC {fmt_coef(h5['coef'], h5['se'], h5['p'])}")


if __name__ == "__main__":
    main()
