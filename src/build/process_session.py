"""
Process one lab session from the registry in config/sessions.yaml.

Reads raw oTree exports, writes a session log, participant payments
(CSV + Excel), and first-pass analysis panels (replaceable later).

Output under data/interim/{session_id}/:
  session_log.yaml
  participant_payments.csv
  payments_{session_id}.xlsx
  participant_round_panel.csv
  participant_panel.csv
"""

from __future__ import annotations

import argparse

import numpy as np
import pandas as pd

from paths import (
    get_session,
    interim_dir_for,
    load_parameters,
    payments_filename,
    raw_dir_for,
)
from process_payments import (
    build_payments,
    copy_payments_to_processed,
    write_payments_csv,
    write_payments_xlsx,
)
from session_log import (
    CSV_READ_KW,
    append_session_log_md,
    build_session_record,
    classify_participants,
    collect_quality_flags,
    format_stdout,
    write_session_log,
)


def load_raw(raw_path, export_date: str, oTree_codes: list[str]) -> tuple:
    """Read CSVs and keep only rows from target sessions."""
    codes = list(oTree_codes)
    intro = pd.read_csv(raw_path / f"intro_{export_date}.csv", **CSV_READ_KW)
    intro = intro[intro["session.code"].isin(codes)]

    post_exp = pd.read_csv(
        raw_path / f"post_exp_{export_date}.csv",
        **CSV_READ_KW,
        dtype={"player.email": "string", "player.student_id": "string"},
    )
    post_exp = post_exp[post_exp["session.code"].isin(codes)]

    main = pd.read_csv(
        raw_path / f"main_{export_date}.csv",
        **CSV_READ_KW,
        usecols=lambda c: c != "player.telemetry_payload",
    )
    main = main[main["session.code"].isin(codes)]

    return intro, post_exp, main


def build_round_panel(main: pd.DataFrame, completed_codes: list[str], params: dict) -> pd.DataFrame:
    """First-pass participant × round panel. Replace with a richer build later."""
    data = main[main["participant.code"].isin(completed_codes)].copy()
    if params.get("drop_training", True) and "player.round_type" in data:
        data = data[data["player.round_type"] != "training"]

    data["treated"] = np.where(data.get("player.condition") == "treatment", 1, 0)
    if "player.round_type" in data:
        data["paid_round"] = np.where(data["player.round_type"] == "paid_data", 1, 0)
    if "player.pay_for_data" in data:
        data["player.pay_for_data"] = data["player.pay_for_data"].fillna(-1)

    data = data.rename(
        columns={
            "session.code": "session_code",
            "participant.code": "participant_code",
            "player.investment_amount": "investment_amount",
            "player.data_available": "data_available",
            "player.pay_for_data": "pay_for_data",
            "player.inner_round_number": "round_number",
            "player.imbalance_was_informative": "informative",
            "player.imbalance_informative": "belief_informative",
            "player.return_forecast": "return_forecast",
            "player.condition": "condition",
            "player.round_type": "round_type",
            "player.realized_return": "realized_return",
            "player.investment_payoff": "investment_payoff",
            "player.round_payoff": "round_payoff",
            "player.forecast_confidence": "forecast_confidence",
            "player.belief_confidence": "belief_confidence",
            "player.cumulative_bonuses": "cumulative_bonuses",
        }
    )
    return data.reset_index(drop=True)


def build_participant_panel(
    post_exp: pd.DataFrame, intro: pd.DataFrame, completed_codes: list[str]
) -> pd.DataFrame:
    """First-pass one-row-per-completer table. Replace with a richer build later."""
    post = post_exp[post_exp["participant.code"].isin(completed_codes)].copy()
    if post.empty:
        return post

    post["fin_quiz"] = pd.to_numeric(
        post.get("player.num_correct_answers"), errors="coerce"
    ) / pd.to_numeric(post.get("player.num_quiz_questions"), errors="coerce")
    post["gender_female"] = np.where(post.get("player.gender") == "Female", 1, 0)
    post["high_education"] = np.where(
        post.get("player.education").isin(
            [
                "MBA",
                "PhD",
                "master",
                "undergraduate: 1st year",
                "undergraduate: 2nd year",
                "undergraduate: 3rd year",
                "undergraduate: 3d year",
                "undergraduate: 4th year",
            ]
        ),
        1,
        0,
    )

    pre = intro[intro["participant.code"].isin(completed_codes)]
    if "player.self_assesment" in pre.columns:
        pre = pre[["participant.code", "player.self_assesment"]].rename(
            columns={"player.self_assesment": "self_literacy"}
        )
        post = post.merge(pre, on="participant.code", how="left")
        post["overconfidence"] = post["self_literacy"] / 10 - post["fin_quiz"]

    post = post.rename(
        columns={
            "session.code": "session_code",
            "participant.code": "participant_code",
            "participant.payoff": "payoff_points",
            "player.hl_switch_point": "risk_aversion",
            "player.course_financial": "finance_course",
            "player.trading_experience": "trading_experience",
            "player.age": "age",
            "player.gender": "gender",
            "player.email": "email",
            "player.student_id": "student_id",
        }
    )
    return post.reset_index(drop=True)


def process_session(session_id: str) -> dict:
    session = get_session(session_id)
    params = load_parameters()
    raw_path = raw_dir_for(session)
    if not raw_path.is_dir():
        raise FileNotFoundError(
            f"Raw folder not found: {raw_path}. "
            "Drop the oTree CSVs under data/raw/{session_id}/ and register the session."
        )

    out_dir = interim_dir_for(session["id"])
    out_dir.mkdir(parents=True, exist_ok=True)

    intro, post_exp, main = load_raw(
        raw_path, session["export_date"], session["oTree_codes"]
    )
    groups = classify_participants(
        post_exp, completed_pages=list(params["completed_pages"])
    )
    completed = groups["completed"]
    completed_codes = completed["participant.code"].tolist()

    payments = build_payments(
        completed,
        exchange_rate=params["exchange_rate"],
        participation_fee=params["participation_fee"],
    )
    payments.insert(0, "session_id", session["id"])
    flags = collect_quality_flags(groups=groups, payments=payments)
    record = build_session_record(
        session=session,
        groups=groups,
        payments=payments,
        params=params,
        flags=flags,
    )

    write_session_log(record, out_dir)
    append_session_log_md(record)

    write_payments_csv(payments, out_dir / "participant_payments.csv")
    xlsx_path = write_payments_xlsx(
        payments,
        out_dir / payments_filename(session["id"]),
        session_id=session["id"],
        record=record,
        incomplete=groups["incomplete"],
    )
    copy_payments_to_processed(xlsx_path, session["id"])

    # First-pass panels — shells to replace once the analysis spec is fixed.
    round_panel = build_round_panel(main, completed_codes, params)
    participant_panel = build_participant_panel(post_exp, intro, completed_codes)
    round_panel.to_csv(out_dir / "participant_round_panel.csv", index=False)
    participant_panel.to_csv(out_dir / "participant_panel.csv", index=False)

    print(format_stdout(record))
    print(
        f"  wrote {len(payments)} payments → {xlsx_path.name} "
        f"and {out_dir}/session_log.yaml"
    )
    return record


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Process one lab session: log, payments, first-pass panels."
    )
    parser.add_argument(
        "--session",
        required=True,
        help="Session id from config/sessions.yaml",
    )
    args = parser.parse_args()
    process_session(args.session)
