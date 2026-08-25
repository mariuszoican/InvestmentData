"""Session logging: classify participants, write YAML + append-only markdown."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import yaml

from paths import PROCESSED_DIR


CSV_READ_KW = dict(encoding="utf-8-sig")


def nonempty(series: pd.Series) -> pd.Series:
    return series.notna() & series.astype(str).str.strip().ne("") & series.astype(
        str
    ).str.strip().str.lower().ne("nan")


def classify_participants(
    post_exp: pd.DataFrame, *, completed_pages: list[str]
) -> dict[str, pd.DataFrame]:
    """Split an oTree post_exp table into completed / incomplete / never_started."""
    visited = post_exp["participant.visited"].fillna(0).astype(int).eq(1)
    page = post_exp["participant._current_page_name"].fillna("").astype(str).str.strip()
    completed = visited & page.isin(completed_pages)
    incomplete = visited & ~page.isin(completed_pages)
    never_started = ~visited
    return {
        "completed": post_exp.loc[completed].copy(),
        "incomplete": post_exp.loc[incomplete].copy(),
        "never_started": post_exp.loc[never_started].copy(),
    }


def _row_summaries(df: pd.DataFrame) -> list[dict]:
    rows = []
    for _, r in df.iterrows():
        rows.append(
            {
                "participant_code": r.get("participant.code"),
                "page": r.get("participant._current_page_name") or None,
                "app": r.get("participant._current_app_name") or None,
                "index_in_pages": _as_int(r.get("participant._index_in_pages")),
                "time_started_utc": r.get("participant.time_started_utc") or None,
                "payoff_points": _as_float(r.get("participant.payoff")),
            }
        )
    return rows


def _as_int(value):
    try:
        if pd.isna(value) or value == "":
            return None
        return int(float(value))
    except (TypeError, ValueError):
        return None


def _as_float(value):
    try:
        if pd.isna(value) or value == "":
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def build_session_record(
    *,
    session: dict,
    groups: dict[str, pd.DataFrame],
    payments: pd.DataFrame | None,
    params: dict,
    flags: list[str],
    processed_at: str | None = None,
) -> dict:
    completed = groups["completed"]
    incomplete = groups["incomplete"]
    never = groups["never_started"]
    payoffs = pd.to_numeric(completed.get("participant.payoff"), errors="coerce")

    record = {
        "session_id": session["id"],
        "export_date": session["export_date"],
        "oTree_codes": list(session["oTree_codes"]),
        "include": bool(session.get("include", False)),
        "notes": session.get("notes", ""),
        "processed_at": processed_at or datetime.now(timezone.utc).isoformat(),
        "counts": {
            "slots_in_export": int(
                len(completed) + len(incomplete) + len(never)
            ),
            "started": int(len(completed) + len(incomplete)),
            "completed": int(len(completed)),
            "incomplete": int(len(incomplete)),
            "never_started": int(len(never)),
            "paid": int(len(payments)) if payments is not None else 0,
        },
        "payoffs_points": {
            "n": int(payoffs.notna().sum()),
            "min": None if payoffs.dropna().empty else float(payoffs.min()),
            "max": None if payoffs.dropna().empty else float(payoffs.max()),
            "mean": None if payoffs.dropna().empty else float(payoffs.mean()),
        },
        "payments": {
            "participation_fee_cad": params["participation_fee"],
            "exchange_rate": params["exchange_rate"],
            "experimental_payoff_cad_sum": (
                None
                if payments is None or payments.empty
                else float(payments["experimental_payoff"].sum())
            ),
            "total_payment_cad_sum": (
                None
                if payments is None or payments.empty
                else float(payments["total_payment"].sum())
            ),
        },
        "incomplete": _row_summaries(incomplete),
        "flags": flags,
    }
    return record


def write_session_log(record: dict, interim_dir: Path) -> Path:
    interim_dir.mkdir(parents=True, exist_ok=True)
    path = interim_dir / "session_log.yaml"
    with open(path, "w") as f:
        yaml.safe_dump(record, f, sort_keys=False, allow_unicode=True)
    return path


def append_session_log_md(record: dict, path: Path | None = None) -> Path:
    """Append a human-readable block to the running lab log."""
    path = path or (PROCESSED_DIR / "session_log.md")
    path.parent.mkdir(parents=True, exist_ok=True)
    c = record["counts"]
    p = record["payments"]
    flags = record.get("flags") or ["none"]
    incomplete_lines = []
    for row in record.get("incomplete") or []:
        incomplete_lines.append(
            f"  - `{row['participant_code']}` on {row['app']}/{row['page']} "
            f"(page {row['index_in_pages']})"
        )
    if not incomplete_lines:
        incomplete_lines = ["  - (none)"]

    block = "\n".join(
        [
            f"## {record['session_id']} — processed {record['processed_at']}",
            "",
            f"- oTree codes: `{', '.join(record['oTree_codes'])}`",
            f"- export date: {record['export_date']}",
            f"- notes: {record.get('notes') or '(none)'}",
            f"- slots / started / completed / incomplete: "
            f"{c['slots_in_export']} / {c['started']} / {c['completed']} / {c['incomplete']}",
            f"- paid: {c['paid']}",
            f"- experimental payoff (CAD): {p['experimental_payoff_cad_sum']}",
            f"- total payments (CAD, incl. ${p['participation_fee_cad']:.2f} show-up): "
            f"{p['total_payment_cad_sum']}",
            f"- flags: {', '.join(flags)}",
            "- incomplete:",
            *incomplete_lines,
            "",
        ]
    )
    header = "# Session processing log\n\n"
    existing = path.read_text() if path.exists() else header
    if not existing.startswith("#"):
        existing = header + existing
    path.write_text(existing.rstrip() + "\n\n" + block + "\n")
    return path


def format_stdout(record: dict) -> str:
    c = record["counts"]
    p = record["payments"]
    lines = [
        f"Session {record['session_id']}  (oTree {', '.join(record['oTree_codes'])})",
        f"  started {c['started']}  completed {c['completed']}  "
        f"incomplete {c['incomplete']}  unused slots {c['never_started']}",
        f"  paid {c['paid']}  experimental CAD {p['experimental_payoff_cad_sum']}  "
        f"total CAD {p['total_payment_cad_sum']}",
    ]
    if record.get("flags"):
        lines.append("  flags: " + "; ".join(record["flags"]))
    for row in record.get("incomplete") or []:
        lines.append(
            f"  incomplete: {row['participant_code']}  {row['app']}/{row['page']}"
        )
    return "\n".join(lines)


def collect_quality_flags(
    *,
    groups: dict[str, pd.DataFrame],
    payments: pd.DataFrame,
) -> list[str]:
    flags: list[str] = []
    completed = groups["completed"]
    if completed.empty:
        flags.append("no completers")
        return flags

    email = completed["player.email"] if "player.email" in completed else pd.Series(dtype=str)
    sid = (
        completed["player.student_id"]
        if "player.student_id" in completed
        else pd.Series(dtype=str)
    )
    n_email = int(nonempty(email).sum()) if len(email) else 0
    n_sid = int(nonempty(sid).sum()) if len(sid) else 0
    if n_email < len(completed):
        flags.append(f"{len(completed) - n_email} completers missing email")
    if n_sid < len(completed):
        flags.append(f"{len(completed) - n_sid} completers missing student_id")

    if "player.payoff_for_trade" in completed:
        trade = pd.to_numeric(completed["player.payoff_for_trade"], errors="coerce")
        if trade.fillna(0).eq(0).all():
            flags.append(
                "player.payoff_for_trade is 0 for every completer "
                "(using participant.payoff for experimental earnings)"
            )

    if not payments.empty:
        dup_email = payments["email"].astype(str).str.lower().duplicated(keep=False)
        dup_sid = payments["student_id"].astype(str).duplicated(keep=False)
        if dup_email.any():
            flags.append("duplicate emails in payment file")
        if dup_sid.any():
            flags.append("duplicate student_ids in payment file")

    return flags
