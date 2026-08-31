"""
Preliminary exploration of the 2026-08-24 lab session (FNCE 449/668).

Session facts: 37 completers, ALL in the treatment condition (no control group),
2 training + 18 main rounds each, exactly 9 paid-data and 9 free-data rounds per
participant (random order), data fee E$5, endowment E$100, 50% of rounds
objectively informative (correlation ~0.75 between lagged imbalance and next
return in informative rounds).

Tests the paper's five hypotheses on this new sample:
  H1  Payment inflates perceived informativeness (esp. of uninformative data).
  H2  Payment raises forecast sensitivity to imbalance (belief=informative);
      corollary: larger forecast errors in objectively uninformative rounds.
  H3  Payment raises investment levels (sunk cost).
  H4  Payment attenuates investment pass-through of forecasts (IV).
  H5  Overconfidence / financial literacy / risk aversion predict data purchase.

Also explores: belief discrimination by literacy, learning dynamics, confidence
responses (belief & forecast confidence, collected but not used in the paper),
positive/negative imbalance asymmetry, and realized payoff consequences.

Outputs:
  - printed summary of every model
  - output/figures/explore/fig*.png
  - src/explore/results_20260824.json  (machine-readable numbers for the
    report and the canvas)

Run from the repo root:  .venv/bin/python src/explore/explore_session_20260824.py
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[2]
PANEL = ROOT / "data" / "processed" / "processed_panels.csv"
RAW_MAIN = ROOT / "data" / "raw" / "20260824" / "main_2026-08-24.csv"
FIG_DIR = ROOT / "output" / "figures" / "explore"
RESULTS_JSON = Path(__file__).resolve().parent / "results_20260824.json"

MU = 15.0  # unconditional mean return (%)
FEE = 5.0  # data fee (E$), session.config.fee_amount

results: dict = {}


# --------------------------------------------------------------------------- #
# Data assembly
# --------------------------------------------------------------------------- #
def load_data() -> pd.DataFrame:
    df = pd.read_csv(PANEL)

    raw = pd.read_csv(
        RAW_MAIN,
        usecols=[
            "participant.code",
            "player.inner_round_number",
            "player.forecast_confidence",
            "player.belief_confidence",
            "player.investment_payoff",
            "player.round_payoff",
            "player.realized_return",
        ],
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
    df = df.merge(raw, on=["participant_code", "round_number"], how="left")

    # Display round 1..18 (panel round_number includes the 2 training rounds)
    df["main_round"] = df["round_number"] - 2

    # Conditional expected return given the true DGP
    df["cond_exp_return"] = MU + df["informative"] * df["last_imbalance_1"]
    df["forecast_error"] = (df["return_forecast"] - df["cond_exp_return"]).abs()

    # Convenience flags
    df["paid"] = df["paid_dummy"].astype(int)  # paid & saw data this round
    df["pay_choice"] = df["pay_for_data"].astype(int)
    df["uninformative"] = 1 - df["informative"]
    df["paid_x_uninf"] = df["paid"] * df["uninformative"]
    df["pos_imb"] = (df["last_imbalance_1"] > 0).astype(int)

    # Participant-level literacy split (median of the 37 quiz scores)
    person = df.groupby("participant_code")["fin_quiz"].first()
    med = person.median()
    df["high_quiz"] = (df["fin_quiz"] >= med).astype(int)
    results["quiz_median"] = float(med)

    return df


def _vars_in(formula: str, data: pd.DataFrame) -> list[str]:
    toks = (
        formula.replace("~", " ").replace("+", " ").replace("*", " ").replace(":", " ").split()
    )
    return [t for t in dict.fromkeys(toks) if t in data.columns]


def coef_dict(model, keys: list[str]) -> dict:
    out = {}
    for k in keys:
        if k in model.params.index:
            out[k] = {
                "coef": float(model.params[k]),
                "se": float(model.bse[k]),
                "p": float(model.pvalues[k]),
            }
    out["nobs"] = int(model.nobs)
    out["r2"] = float(model.rsquared)
    return out


def tstars(p: float) -> str:
    return "***" if p < 0.01 else "**" if p < 0.05 else "*" if p < 0.1 else ""


def print_model(title: str, model, keys: list[str]):
    print(f"\n--- {title} (N={int(model.nobs)}, R2={model.rsquared:.3f}) ---")
    for k in keys:
        if k in model.params.index:
            print(
                f"  {k:38s} {model.params[k]:8.3f} ({model.bse[k]:.3f}) "
                f"p={model.pvalues[k]:.3f}{tstars(model.pvalues[k])}"
            )


# --------------------------------------------------------------------------- #
# 2SLS with cluster-robust SEs (just-identified)
# --------------------------------------------------------------------------- #
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

    # cluster-robust sandwich
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
    V *= G / (G - 1) * (n - 1) / (n - k)  # small-sample correction
    se = np.sqrt(np.diag(V))
    from scipy import stats

    tvals = beta / se
    pvals = 2 * stats.t.sf(np.abs(tvals), df=G - 1)
    return {
        "names": names,
        "coef": dict(zip(names, map(float, beta))),
        "se": dict(zip(names, map(float, se))),
        "p": dict(zip(names, map(float, pvals))),
        "nobs": int(n),
        "n_clusters": int(G),
    }


def print_iv(title: str, res: dict, keys: list[str]):
    print(f"\n--- {title} (N={res['nobs']}, clusters={res['n_clusters']}) ---")
    for k in keys:
        if k in res["coef"]:
            print(
                f"  {k:38s} {res['coef'][k]:8.3f} ({res['se'][k]:.3f}) "
                f"p={res['p'][k]:.3f}{tstars(res['p'][k])}"
            )


# --------------------------------------------------------------------------- #
# Analyses
# --------------------------------------------------------------------------- #
def summary_stats(df: pd.DataFrame):
    person = df.groupby("participant_code").agg(
        fin_quiz=("fin_quiz", "first"),
        overconfidence=("overconfidence", "first"),
        age=("age", "first"),
        female=("gender_female", "first"),
        risk_aversion=("risk_aversion", "first"),
        trading_exp=("trading_experience", "first"),
        finance_course=("finance_course", "first"),
        pay_rate=("pay_choice", "mean"),
    )
    s = {
        "n_participants": int(len(person)),
        "n_rounds_pp": int(df.groupby("participant_code").size().iloc[0]),
        "n_obs": int(len(df)),
        "share_paid_rounds": float(df["paid_round"].mean()),
        "choose_pay_rate": float(df["pay_choice"].mean()),
        "paid_and_saw": int(df["paid"].sum()),
        "declined_paid_round_no_data": int((1 - df["data_available"]).sum()),
        "mean_invest_share": float(df["investment_share"].mean()),
        "mean_forecast": float(df["return_forecast"].mean()),
        "belief_informative_rate": float(df["belief_informative"].mean()),
        "belief_rate_when_informative": float(
            df.loc[df.informative == 1, "belief_informative"].mean()
        ),
        "belief_rate_when_uninformative": float(
            df.loc[df.informative == 0, "belief_informative"].mean()
        ),
        "mean_fin_quiz": float(person["fin_quiz"].mean()),
        "mean_overconfidence": float(person["overconfidence"].mean()),
        "mean_age": float(person["age"].mean()),
        "share_female": float(person["female"].mean()),
        "share_trading_exp": float(person["trading_exp"].mean()),
        "share_finance_course": float(person["finance_course"].mean()),
        "mean_risk_aversion_switchpoint": float(person["risk_aversion"].mean()),
        "pay_rate_distribution": person["pay_rate"].describe().to_dict(),
        "share_always_pay": float((person["pay_rate"] == 1).mean()),
        "share_never_pay": float((person["pay_rate"] == 0).mean()),
    }
    results["summary"] = s
    print("\n=== SUMMARY (37-participant lab session, all treated) ===")
    for k, v in s.items():
        if not isinstance(v, dict):
            print(f"  {k:38s} {v}")


def h1_beliefs(df: pd.DataFrame):
    """Beliefs observed only when data is available (580 rounds)."""
    d = df[df["data_available"] == 1].copy()

    f = (
        "belief_informative ~ paid_x_uninf + paid + informative + pay_choice"
        " + main_round + last_return_1 + last_imbalance_1"
    )
    m = smf.ols(f, data=d).fit(
        cov_type="cluster", cov_kwds={"groups": d["participant_code"]}
    )
    keys = ["paid_x_uninf", "paid", "informative", "pay_choice"]
    print_model("H1: Belief informative (OLS, cluster by participant)", m, keys)
    results["h1_all"] = coef_dict(m, keys)

    # Participant fixed effects (within-person sunk-cost identification)
    f_fe = (
        "belief_informative ~ paid_x_uninf + paid + informative + pay_choice"
        " + main_round + last_return_1 + last_imbalance_1 + C(participant_code)"
    )
    m_fe = smf.ols(f_fe, data=d).fit(
        cov_type="cluster", cov_kwds={"groups": d["participant_code"]}
    )
    print_model("H1: with participant FE", m_fe, keys)
    results["h1_fe"] = coef_dict(m_fe, keys)

    # Literacy splits
    for label, sub in [("high", d[d.high_quiz == 1]), ("low", d[d.high_quiz == 0])]:
        ms = smf.ols(f, data=sub).fit(
            cov_type="cluster", cov_kwds={"groups": sub["participant_code"]}
        )
        print_model(f"H1: {label} quiz", ms, keys)
        results[f"h1_{label}"] = coef_dict(ms, keys)

    # Raw means for figure / canvas
    cells = {}
    for paid in (0, 1):
        for inf in (0, 1):
            sub = d[(d.paid == paid) & (d.informative == inf)]["belief_informative"]
            cells[f"paid{paid}_inf{inf}"] = {
                "mean": float(sub.mean()),
                "se": float(sub.std() / np.sqrt(len(sub))),
                "n": int(len(sub)),
            }
    # selection cells: free rounds only, by pay choice
    fr = d[d.paid_round == 0]
    for pc in (0, 1):
        for inf in (0, 1):
            sub = fr[(fr.pay_choice == pc) & (fr.informative == inf)]["belief_informative"]
            cells[f"choice{pc}_inf{inf}"] = {
                "mean": float(sub.mean()),
                "se": float(sub.std() / np.sqrt(len(sub))),
                "n": int(len(sub)),
            }
    results["h1_cells"] = cells


def h2_forecasts(df: pd.DataFrame):
    d = df[(df["data_available"] == 1)].copy()
    d["paid_x_imb"] = d["paid"] * d["last_imbalance_1"]
    d["choice_x_imb"] = d["pay_choice"] * d["last_imbalance_1"]

    f = (
        "return_forecast ~ paid_x_imb + last_imbalance_1 + paid + choice_x_imb"
        " + pay_choice + last_return_1 + main_round"
    )
    keys = ["paid_x_imb", "last_imbalance_1", "paid", "choice_x_imb", "pay_choice", "last_return_1"]

    bel = d[d.belief_informative == 1]
    m = smf.ols(f, data=bel).fit(
        cov_type="cluster", cov_kwds={"groups": bel["participant_code"]}
    )
    print_model("H2: Forecast ~ imbalance (belief=informative)", m, keys)
    results["h2_believers"] = coef_dict(m, keys)

    plc = d[d.belief_informative == 0]
    m_p = smf.ols(f, data=plc).fit(
        cov_type="cluster", cov_kwds={"groups": plc["participant_code"]}
    )
    print_model("H2 placebo: belief=uninformative", m_p, keys)
    results["h2_placebo"] = coef_dict(m_p, keys)

    for label, sub in [("high", bel[bel.high_quiz == 1]), ("low", bel[bel.high_quiz == 0])]:
        ms = smf.ols(f, data=sub).fit(
            cov_type="cluster", cov_kwds={"groups": sub["participant_code"]}
        )
        print_model(f"H2: {label} quiz (believers)", ms, keys)
        results[f"h2_{label}"] = coef_dict(ms, keys)

    # Asymmetry: split by sign of imbalance (residualized means for figure)
    resid_model = smf.ols(
        "return_forecast ~ last_return_1 + main_round + pay_choice", data=bel
    ).fit()
    bel = bel.copy()
    bel["forecast_resid"] = resid_model.resid + bel["return_forecast"].mean()
    cells = {}
    for paid in (0, 1):
        for pos in (0, 1):
            sub = bel[(bel.paid == paid) & (bel.pos_imb == pos)]["forecast_resid"]
            cells[f"paid{paid}_pos{pos}"] = {
                "mean": float(sub.mean()),
                "se": float(sub.std() / np.sqrt(len(sub))),
                "n": int(len(sub)),
            }
    results["h2_cells"] = cells


def h2b_forecast_errors(df: pd.DataFrame):
    d = df[(df["data_available"] == 1) & (df["informative"] == 0)].copy()
    f = (
        "forecast_error ~ paid + pay_choice + last_imbalance_1 + last_return_1"
        " + main_round"
    )
    keys = ["paid", "pay_choice", "last_imbalance_1", "last_return_1"]
    m = smf.ols(f, data=d).fit(
        cov_type="cluster", cov_kwds={"groups": d["participant_code"]}
    )
    print_model("H2b: |forecast error| in uninformative rounds", m, keys)
    results["h2b_all"] = coef_dict(m, keys)

    for label, sub in [("high", d[d.high_quiz == 1]), ("low", d[d.high_quiz == 0])]:
        ms = smf.ols(f, data=sub).fit(
            cov_type="cluster", cov_kwds={"groups": sub["participant_code"]}
        )
        print_model(f"H2b: {label} quiz", ms, keys)
        results[f"h2b_{label}"] = coef_dict(ms, keys)

    cells = {}
    for paid in (0, 1):
        sub = d[d.paid == paid]["forecast_error"]
        cells[f"paid{paid}"] = {
            "mean": float(sub.mean()),
            "se": float(sub.std() / np.sqrt(len(sub))),
            "n": int(len(sub)),
        }
    # informative rounds too, for contrast
    di = df[(df["data_available"] == 1) & (df["informative"] == 1)]
    for paid in (0, 1):
        sub = di[di.paid == paid]["forecast_error"]
        cells[f"inf_paid{paid}"] = {
            "mean": float(sub.mean()),
            "se": float(sub.std() / np.sqrt(len(sub))),
            "n": int(len(sub)),
        }
    results["h2b_cells"] = cells


def h34_investment(df: pd.DataFrame):
    d = df[(df["data_available"] == 1) & (df["belief_informative"] == 1)].copy()
    # Center interacted continuous variables at the estimation-sample mean so
    # the `paid` main effect is the H3 level effect at average forecast/return
    # (uncentered, it is an out-of-sample extrapolation to forecast = 0).
    d["fc_c"] = d["return_forecast"] - d["return_forecast"].mean()
    d["lr_c"] = d["last_return_1"] - d["last_return_1"].mean()
    d["imb_c"] = d["last_imbalance_1"] - d["last_imbalance_1"].mean()
    d["paid_x_imb"] = d["paid"] * d["imb_c"]
    d["forecast_x_paid"] = d["fc_c"] * d["paid"]
    d["lastret_x_paid"] = d["lr_c"] * d["paid"]
    d["return_forecast"] = d["fc_c"]
    d["last_imbalance_1"] = d["imb_c"]
    d["last_return_1"] = d["lr_c"]

    exog = ["paid", "pay_choice", "main_round", "last_return_1", "lastret_x_paid",
            "gender_female", "fin_quiz", "overconfidence"]
    spec = dict(
        y_col="investment_share",
        endog=["return_forecast", "forecast_x_paid"],
        instruments=["last_imbalance_1", "paid_x_imb"],
        exog=exog,
        cluster_col="participant_code",
    )
    keys = ["return_forecast", "forecast_x_paid", "paid", "pay_choice",
            "last_return_1", "lastret_x_paid", "fin_quiz", "gender_female"]

    res = iv_2sls(d, **spec)
    print_iv("H3/H4: IV investment share (believers)", res, keys)
    results["h34_all"] = res

    for label, sub in [("high", d[d.high_quiz == 1]), ("low", d[d.high_quiz == 0])]:
        r = iv_2sls(sub, **spec)
        print_iv(f"H3/H4: {label} quiz", r, keys)
        results[f"h34_{label}"] = r

    # First stage strength
    fs = smf.ols(
        "return_forecast ~ last_imbalance_1 + paid_x_imb + paid + pay_choice"
        " + main_round + last_return_1 + lastret_x_paid + gender_female"
        " + fin_quiz + overconfidence",
        data=d,
    ).fit(cov_type="cluster", cov_kwds={"groups": d["participant_code"]})
    results["h34_first_stage"] = coef_dict(fs, ["last_imbalance_1", "paid_x_imb"])
    print_model("H3/H4 first stage", fs, ["last_imbalance_1", "paid_x_imb"])

    # OLS analogue for reference
    m_ols = smf.ols(
        "investment_share ~ return_forecast + forecast_x_paid + paid + pay_choice"
        " + main_round + last_return_1 + lastret_x_paid + gender_female"
        " + fin_quiz + overconfidence",
        data=d,
    ).fit(cov_type="cluster", cov_kwds={"groups": d["participant_code"]})
    results["h34_ols"] = coef_dict(m_ols, ["return_forecast", "forecast_x_paid", "paid"])
    print_model("H3/H4 OLS analogue", m_ols, ["return_forecast", "forecast_x_paid", "paid"])

    # Raw means: investment share paid vs free among believers, by literacy
    cells = {}
    for grp, sub in [("all", d), ("high", d[d.high_quiz == 1]), ("low", d[d.high_quiz == 0])]:
        for paid in (0, 1):
            s = sub[sub.paid == paid]["investment_share"]
            cells[f"{grp}_paid{paid}"] = {
                "mean": float(s.mean()),
                "se": float(s.std() / np.sqrt(len(s))),
                "n": int(len(s)),
            }
    results["h34_cells"] = cells


def h5_selection(df: pd.DataFrame):
    d = df.copy()
    d["oc_std"] = (d["overconfidence"] - d["overconfidence"].mean()) / d["overconfidence"].std()
    d["quiz_std"] = (d["fin_quiz"] - d["fin_quiz"].mean()) / d["fin_quiz"].std()
    d["ra_std"] = (d["risk_aversion"] - d["risk_aversion"].mean()) / d["risk_aversion"].std()

    f = (
        "pay_choice ~ oc_std + quiz_std + ra_std + gender_female + age"
        " + trading_experience + high_education + C(main_round)"
    )
    keys = ["oc_std", "quiz_std", "ra_std", "gender_female", "age", "trading_experience"]
    m = smf.ols(f, data=d).fit(
        cov_type="cluster", cov_kwds={"groups": d["participant_code"]}
    )
    print_model("H5: Who pays? (OLS, std. coefficients)", m, keys)
    results["h5"] = coef_dict(m, keys)

    # Dynamics of pay choice: response to previous round outcomes
    d = d.sort_values(["participant_code", "main_round"])
    g = d.groupby("participant_code")
    d["prev_informative"] = g["informative"].shift(1)
    d["prev_paid"] = g["paid"].shift(1)
    d["prev_return"] = g["realized_return"].shift(1)
    d["prev_belief_correct"] = (
        g["belief_informative"].shift(1) == g["informative"].shift(1)
    ).astype(float)
    d.loc[g["belief_informative"].shift(1).isna(), "prev_belief_correct"] = np.nan
    d["prev_paid_x_uninf"] = d["prev_paid"] * (1 - d["prev_informative"])

    f_dyn = (
        "pay_choice ~ prev_paid + prev_paid_x_uninf + prev_informative"
        " + prev_return + main_round"
    )
    m_dyn = smf.ols(f_dyn, data=d).fit(
        cov_type="cluster",
        cov_kwds={"groups": d.dropna(subset=_vars_in(f_dyn, d))["participant_code"]},
    )
    print_model("H5+: pay choice dynamics", m_dyn,
                ["prev_paid", "prev_paid_x_uninf", "prev_informative", "prev_return"])
    results["h5_dynamics"] = coef_dict(
        m_dyn, ["prev_paid", "prev_paid_x_uninf", "prev_informative", "prev_return"]
    )

    # person-level cells for figure
    person = df.groupby("participant_code").agg(
        pay_rate=("pay_choice", "mean"),
        fin_quiz=("fin_quiz", "first"),
        overconfidence=("overconfidence", "first"),
        high_quiz=("high_quiz", "first"),
    )
    oc_med = person["overconfidence"].median()
    cells = {}
    for label, mask in [
        ("quiz_high", person.high_quiz == 1),
        ("quiz_low", person.high_quiz == 0),
        ("oc_high", person.overconfidence >= oc_med),
        ("oc_low", person.overconfidence < oc_med),
    ]:
        s = person[mask]["pay_rate"]
        cells[label] = {"mean": float(s.mean()), "se": float(s.std() / np.sqrt(len(s))), "n": int(len(s))}
    results["h5_cells"] = cells
    results["h5_person"] = [
        {
            "quiz": float(r.fin_quiz),
            "oc": float(r.overconfidence),
            "pay_rate": float(r.pay_rate),
        }
        for r in person.itertuples()
    ]


def extra_patterns(df: pd.DataFrame):
    d = df.copy()

    # Confidence: does payment raise stated confidence? (novel, not in paper)
    da = d[d["data_available"] == 1]
    m_bc = smf.ols(
        "belief_confidence ~ paid + pay_choice + informative + main_round",
        data=da,
    ).fit(cov_type="cluster", cov_kwds={"groups": da["participant_code"]})
    print_model("Extra: belief confidence (1-5)", m_bc, ["paid", "pay_choice", "informative"])
    results["extra_belief_conf"] = coef_dict(m_bc, ["paid", "pay_choice", "informative"])

    m_fc = smf.ols(
        "forecast_confidence ~ paid + pay_choice + informative + main_round",
        data=da,
    ).fit(cov_type="cluster", cov_kwds={"groups": da["participant_code"]})
    print_model("Extra: forecast confidence (1-5)", m_fc, ["paid", "pay_choice", "informative"])
    results["extra_forecast_conf"] = coef_dict(m_fc, ["paid", "pay_choice", "informative"])

    # Belief accuracy: correct classification rate
    da = da.copy()
    da["belief_correct"] = (da["belief_informative"] == da["informative"]).astype(int)
    acc = {
        "all": float(da["belief_correct"].mean()),
        "high_quiz": float(da[da.high_quiz == 1]["belief_correct"].mean()),
        "low_quiz": float(da[da.high_quiz == 0]["belief_correct"].mean()),
        "paid": float(da[da.paid == 1]["belief_correct"].mean()),
        "free": float(da[da.paid == 0]["belief_correct"].mean()),
    }
    results["belief_accuracy"] = acc
    print("\nBelief classification accuracy:", {k: round(v, 3) for k, v in acc.items()})

    # Round dynamics for figure
    dyn = (
        d.groupby("main_round")
        .agg(
            pay_rate=("pay_choice", "mean"),
            invest=("investment_share", "mean"),
            belief=("belief_informative", "mean"),
            forecast_err=("forecast_error", "mean"),
        )
        .reset_index()
    )
    results["round_dynamics"] = dyn.round(4).to_dict(orient="records")

    # Payoff consequences: investment payoff net of fee, paid vs free rounds
    d["net_payoff"] = d["investment_payoff"]
    cells = {}
    for paid in (0, 1):
        s = d[(d.paid == paid) & (d.data_available == 1)]["net_payoff"]
        cells[f"paid{paid}"] = {
            "mean": float(s.mean()),
            "se": float(s.std() / np.sqrt(len(s))),
            "n": int(len(s)),
        }
    # decliners in paid rounds (no data)
    s = d[d.data_available == 0]["net_payoff"]
    cells["nodata"] = {
        "mean": float(s.mean()),
        "se": float(s.std() / np.sqrt(len(s))),
        "n": int(len(s)),
    }
    results["payoff_cells"] = cells
    print("Round investment payoff (E$):", {k: round(v["mean"], 2) for k, v in cells.items()})

    # Does payment raise investment even among non-believers? (sunk cost breadth)
    nb = d[(d["data_available"] == 1) & (d["belief_informative"] == 0)]
    m_nb = smf.ols(
        "investment_share ~ paid + pay_choice + main_round + last_return_1",
        data=nb,
    ).fit(cov_type="cluster", cov_kwds={"groups": nb["participant_code"]})
    print_model("Extra: investment among non-believers", m_nb, ["paid", "pay_choice"])
    results["extra_invest_nonbelievers"] = coef_dict(m_nb, ["paid", "pay_choice"])


# --------------------------------------------------------------------------- #
# Figures
# --------------------------------------------------------------------------- #
def make_figures(df: pd.DataFrame):
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update({
        "figure.dpi": 150, "font.size": 9, "axes.spines.top": False,
        "axes.spines.right": False, "axes.grid": True, "grid.alpha": 0.25,
    })
    c_free, c_paid = "#4878CF", "#D65F5F"

    # Fig 1: beliefs
    cells = results["h1_cells"]
    fig, axes = plt.subplots(1, 2, figsize=(8, 3.2), sharey=True)
    x = np.arange(2)
    w = 0.35
    for ax, (k0, k1, lbl) in zip(
        axes,
        [("paid0", "paid1", "Paid data round"), ("choice0", "choice1", "Chose to pay")],
    ):
        m0 = [cells[f"{k0}_inf{i}"]["mean"] for i in (0, 1)]
        e0 = [1.96 * cells[f"{k0}_inf{i}"]["se"] for i in (0, 1)]
        m1 = [cells[f"{k1}_inf{i}"]["mean"] for i in (0, 1)]
        e1 = [1.96 * cells[f"{k1}_inf{i}"]["se"] for i in (0, 1)]
        ax.bar(x - w / 2, m0, w, yerr=e0, capsize=3, color=c_free, label="No")
        ax.bar(x + w / 2, m1, w, yerr=e1, capsize=3, color=c_paid, label="Yes")
        ax.set_xticks(x, ["Uninformative", "Informative"])
        ax.set_xlabel("Round truly informative")
        ax.legend(title=lbl, fontsize=8)
    axes[0].set_ylabel("Share believing data informative")
    axes[0].set_title("(A) Payment effect (within payers)", fontsize=9)
    axes[1].set_title("(B) Selection effect (free rounds only)", fontsize=9)
    fig.suptitle("Beliefs about data informativeness — lab session 2026-08-24", fontsize=10)
    fig.tight_layout()
    fig.savefig(FIG_DIR / "fig1_beliefs.png", bbox_inches="tight")
    plt.close(fig)

    # Fig 2: forecast sensitivity (residualized means by imbalance sign)
    cells = results["h2_cells"]
    fig, ax = plt.subplots(figsize=(4.5, 3.2))
    x = np.arange(2)
    m0 = [cells[f"paid0_pos{i}"]["mean"] for i in (0, 1)]
    e0 = [1.96 * cells[f"paid0_pos{i}"]["se"] for i in (0, 1)]
    m1 = [cells[f"paid1_pos{i}"]["mean"] for i in (0, 1)]
    e1 = [1.96 * cells[f"paid1_pos{i}"]["se"] for i in (0, 1)]
    ax.bar(x - 0.18, m0, 0.35, yerr=e0, capsize=3, color=c_free, label="Free")
    ax.bar(x + 0.18, m1, 0.35, yerr=e1, capsize=3, color=c_paid, label="Paid")
    ax.set_xticks(x, ["Negative", "Positive"])
    ax.set_xlabel("Last order-flow imbalance sign")
    ax.set_ylabel("Return forecast (%, residualized)")
    ax.set_title("Forecasts by imbalance sign and payment\n(belief = informative)", fontsize=9)
    ax.legend(title="Data round", fontsize=8)
    fig.tight_layout()
    fig.savefig(FIG_DIR / "fig2_forecast_sensitivity.png", bbox_inches="tight")
    plt.close(fig)

    # Fig 3: forecast errors
    cells = results["h2b_cells"]
    fig, ax = plt.subplots(figsize=(4.5, 3.2))
    labels = ["Uninformative\nfree", "Uninformative\npaid", "Informative\nfree", "Informative\npaid"]
    keys = ["paid0", "paid1", "inf_paid0", "inf_paid1"]
    means = [cells[k]["mean"] for k in keys]
    errs = [1.96 * cells[k]["se"] for k in keys]
    colors = [c_free, c_paid, c_free, c_paid]
    ax.bar(labels, means, yerr=errs, capsize=3, color=colors)
    ax.set_ylabel("Mean |forecast − E[r | DGP]| (pp)")
    ax.set_title("Forecast errors by round type and payment", fontsize=9)
    fig.tight_layout()
    fig.savefig(FIG_DIR / "fig3_forecast_errors.png", bbox_inches="tight")
    plt.close(fig)

    # Fig 4: investment share paid vs free by literacy (believers)
    cells = results["h34_cells"]
    fig, ax = plt.subplots(figsize=(5, 3.2))
    grps = ["all", "high", "low"]
    lbls = ["All", "High quiz", "Low quiz"]
    x = np.arange(3)
    m0 = [cells[f"{g}_paid0"]["mean"] for g in grps]
    e0 = [1.96 * cells[f"{g}_paid0"]["se"] for g in grps]
    m1 = [cells[f"{g}_paid1"]["mean"] for g in grps]
    e1 = [1.96 * cells[f"{g}_paid1"]["se"] for g in grps]
    ax.bar(x - 0.18, m0, 0.35, yerr=e0, capsize=3, color=c_free, label="Free")
    ax.bar(x + 0.18, m1, 0.35, yerr=e1, capsize=3, color=c_paid, label="Paid")
    ax.set_xticks(x, lbls)
    ax.set_ylabel("Investment share (% of investable)")
    ax.set_title("Investment share, paid vs free rounds (believers)", fontsize=9)
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(FIG_DIR / "fig4_investment.png", bbox_inches="tight")
    plt.close(fig)

    # Fig 5: who pays
    cells = results["h5_cells"]
    fig, ax = plt.subplots(figsize=(5, 3.2))
    keys = ["quiz_low", "quiz_high", "oc_low", "oc_high"]
    lbls = ["Quiz\nbelow med", "Quiz\nabove med", "Overconf.\nbelow med", "Overconf.\nabove med"]
    means = [cells[k]["mean"] for k in keys]
    errs = [1.96 * cells[k]["se"] for k in keys]
    ax.bar(lbls, means, yerr=errs, capsize=3,
           color=["#9ecae1", "#3182bd", "#fdd0a2", "#e6550d"])
    ax.set_ylabel("Mean individual pay rate")
    ax.set_title("Data purchase rate by participant type", fontsize=9)
    fig.tight_layout()
    fig.savefig(FIG_DIR / "fig5_who_pays.png", bbox_inches="tight")
    plt.close(fig)

    # Fig 6: dynamics
    dyn = pd.DataFrame(results["round_dynamics"])
    fig, axes = plt.subplots(1, 3, figsize=(9.5, 3))
    axes[0].plot(dyn.main_round, dyn.pay_rate, "-o", ms=3, color="#333")
    axes[0].set_title("Share choosing to pay", fontsize=9)
    axes[1].plot(dyn.main_round, dyn.invest, "-o", ms=3, color=c_paid)
    axes[1].set_title("Mean investment share (%)", fontsize=9)
    axes[2].plot(dyn.main_round, dyn.belief, "-o", ms=3, color=c_free)
    axes[2].set_title("Share believing informative", fontsize=9)
    for ax in axes:
        ax.set_xlabel("Main round (1–18)")
    fig.suptitle("Within-session dynamics", fontsize=10)
    fig.tight_layout()
    fig.savefig(FIG_DIR / "fig6_dynamics.png", bbox_inches="tight")
    plt.close(fig)

    print(f"\nFigures written to {FIG_DIR}")


def main():
    df = load_data()
    summary_stats(df)
    h1_beliefs(df)
    h2_forecasts(df)
    h2b_forecast_errors(df)
    h34_investment(df)
    h5_selection(df)
    extra_patterns(df)
    make_figures(df)
    RESULTS_JSON.write_text(json.dumps(results, indent=2, default=float))
    print(f"Results JSON → {RESULTS_JSON}")


if __name__ == "__main__":
    main()
