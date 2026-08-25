"""
Build the participant × round analysis panel for every include:true session.

Reads data/raw/{id}/ plus data/round_metadata.csv and writes
data/processed/processed_panels.csv.
"""

from __future__ import annotations

import argparse

import numpy as np
import pandas as pd

from paths import (
    ROUND_METADATA,
    get_session,
    load_parameters,
    load_sessions,
    panel_path,
    raw_dir_for,
)
from session_log import CSV_READ_KW

HIGH_EDUCATION = [
    "MBA",
    "PhD",
    "master",
    "undergraduate: 1st year",
    "undergraduate: 2nd year",
    "undergraduate: 3rd year",
    "undergraduate: 3d year",
    "undergraduate: 4th year",
]

META_WANTED = [
    "round_number",
    "last_imbalance_1",
    "last_return_1",
    "last_imbalance_2",
    "last_return_2",
    "last_imbalance_3",
    "last_return_3",
    "next_return",
    "last_imbalance",
    "last_return",
    "informative",
    "seed",
]

PANEL_COLUMNS = [
    "session_id",
    "participant_code",
    "round_number",
    "series_round",
    "treated",
    "paid_round",
    "pay_for_data",
    "paid_dummy",
    "data_available",
    "investment_amount",
    "investment_share",
    "return_forecast",
    "belief_informative",
    "informative",
    "fin_quiz",
    "self_literacy",
    "overconfidence",
    "gender_female",
    "finance_course",
    "age",
    "trading_experience",
    "risk_aversion",
    "high_education",
    "last_imbalance_1",
    "last_return_1",
    "last_imbalance_2",
    "last_return_2",
    "last_imbalance_3",
    "last_return_3",
    "imb_difference",
    "return_difference",
    "next_return",
    "seed",
]


def load_metadata(path=ROUND_METADATA) -> pd.DataFrame:
    meta = pd.read_csv(path)
    if "last_imbalance_1" not in meta.columns and "last_imbalance" in meta.columns:
        meta["last_imbalance_1"] = meta["last_imbalance"]
    if "last_return_1" not in meta.columns and "last_return" in meta.columns:
        meta["last_return_1"] = meta["last_return"]
    keep = [c for c in META_WANTED if c in meta.columns]
    return meta[keep].drop_duplicates("round_number")


def process_one(session: dict, params: dict, meta: pd.DataFrame) -> pd.DataFrame:
    raw_path = raw_dir_for(session)
    date = session["export_date"]
    codes = list(session["oTree_codes"])
    completed_pages = list(params["completed_pages"])

    data = pd.read_csv(
        raw_path / f"main_{date}.csv",
        **CSV_READ_KW,
        usecols=lambda c: c != "player.telemetry_payload",
    )
    post_exp = pd.read_csv(raw_path / f"post_exp_{date}.csv", **CSV_READ_KW)
    pre_exp = pd.read_csv(raw_path / f"intro_{date}.csv", **CSV_READ_KW)

    data = data[data["session.code"].isin(codes)]
    data = data[data["participant._current_page_name"].isin(completed_pages)]
    data = data[data["player.round_type"] != "training"]

    data["treated"] = np.where(data["player.condition"] == "treatment", 1, 0)
    data["paid_round"] = np.where(data["player.round_type"] == "paid_data", 1, 0)
    data["player.pay_for_data"] = data["player.pay_for_data"].fillna(-1)

    finished = data["participant.code"].drop_duplicates().tolist()
    post_exp = post_exp[post_exp["participant.code"].isin(finished)].copy()
    pre_exp = pre_exp[pre_exp["participant.code"].isin(finished)].copy()

    post_exp["fin_quiz"] = (
        pd.to_numeric(post_exp["player.num_correct_answers"], errors="coerce")
        / pd.to_numeric(post_exp["player.num_quiz_questions"], errors="coerce")
    )
    post_exp["gender_female"] = np.where(post_exp["player.gender"] == "Female", 1, 0)
    post_exp["finance_course"] = post_exp["player.course_financial"]
    post_exp["age"] = post_exp["player.age"]
    post_exp["trading_experience"] = post_exp["player.trading_experience"]
    post_exp["risk_aversion"] = post_exp["player.hl_switch_point"]
    post_exp["high_education"] = np.where(
        post_exp["player.education"].isin(HIGH_EDUCATION), 1, 0
    )
    pre_exp["self_literacy"] = pre_exp["player.self_assesment"]

    data = data.merge(
        post_exp[
            [
                "participant.code",
                "fin_quiz",
                "gender_female",
                "finance_course",
                "age",
                "trading_experience",
                "risk_aversion",
                "high_education",
            ]
        ],
        on="participant.code",
        how="left",
    )
    data = data.merge(
        pre_exp[["participant.code", "self_literacy"]],
        on="participant.code",
        how="left",
    )
    data["overconfidence"] = data["self_literacy"] / 10 - data["fin_quiz"]

    data = data.rename(
        columns={
            "session.code": "session_code",
            "participant.code": "participant_code",
            "player.investment_amount": "investment_amount",
            "player.data_available": "data_available",
            "player.pay_for_data": "pay_for_data",
            "player.inner_round_number": "round_number",
            "player.series_round": "series_round",
            "player.imbalance_was_informative": "informative",
            "player.imbalance_informative": "belief_informative",
            "player.return_forecast": "return_forecast",
        }
    )

    data["paid_dummy"] = np.where(
        (data["paid_round"] == 1) & (data["pay_for_data"] == 1), 1, 0
    )
    data["investment_share"] = (
        100 * data["investment_amount"] / np.where(data["paid_dummy"] == 1, 95, 100)
    )

    # Display order is shuffled; the chart/seed is series_round, not round_number.
    meta_join = meta.rename(columns={"round_number": "series_round"})
    data = data.merge(meta_join, on="series_round", how="left", suffixes=("", "_meta"))
    if "last_imbalance_1" in data.columns and "last_imbalance_2" in data.columns:
        data["imb_difference"] = data["last_imbalance_1"] - data["last_imbalance_2"]
    if "last_return_1" in data.columns and "last_return_2" in data.columns:
        data["return_difference"] = data["last_return_1"] - data["last_return_2"]

    data["session_id"] = data["session_code"]
    keep = [c for c in PANEL_COLUMNS if c in data.columns]
    return data[keep].reset_index(drop=True)


def process_panels(*, only: list[str] | None = None) -> pd.DataFrame:
    params = load_parameters()
    meta = load_metadata()
    sessions = [s for s in load_sessions() if s.get("include", False)]
    if only:
        only_set = set(only)
        sessions = [s for s in sessions if str(s["id"]) in only_set]
    if not sessions:
        raise SystemExit("No included sessions to build (check config/sessions.yaml).")

    frames = []
    for s in sessions:
        s = get_session(s["id"])
        print(f"Panel {s['id']} (export {s['export_date']}, oTree {s['oTree_codes']})…")
        frame = process_one(s, params, meta)
        n_people = frame["participant_code"].nunique()
        n_meta = int(frame["next_return"].notna().sum()) if "next_return" in frame else 0
        print(f"  {len(frame):,} rows, {n_people} completers, {n_meta:,} with metadata")
        frames.append(frame)

    panel = pd.concat(frames, ignore_index=True)
    dest = panel_path()
    dest.parent.mkdir(parents=True, exist_ok=True)
    panel.to_csv(dest, index=False)
    print(f"Wrote {len(panel):,} rows → {dest}")
    return panel


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--only",
        nargs="+",
        help="Restrict to these session ids (still must have include: true)",
    )
    args = parser.parse_args()
    process_panels(only=args.only)
