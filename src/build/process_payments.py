"""Build participant payment files from a completed-session post_exp table."""

from __future__ import annotations

import csv
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

import pandas as pd

from paths import PROCESSED_DIR, payments_filename
from session_log import nonempty


def money(value) -> float:
    """Round half-up to cents."""
    return float(
        Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    )


def build_payments(
    completed: pd.DataFrame,
    *,
    exchange_rate: float,
    participation_fee: float,
) -> pd.DataFrame:
    """One row per completer with contact info and CAD amounts."""
    df = completed.copy()
    if df.empty:
        return pd.DataFrame(
            columns=[
                "participant_code",
                "session_code",
                "email",
                "student_id",
                "experimental_payoff_points",
                "experimental_payoff",
                "participation_fee",
                "total_payment",
            ]
        )

    out = pd.DataFrame(
        {
            "participant_code": df["participant.code"],
            "session_code": df["session.code"],
            "email": df["player.email"].astype(str).str.strip(),
            "student_id": df["player.student_id"]
            .astype(str)
            .str.strip()
            .str.replace(r"\.0$", "", regex=True),
            "experimental_payoff_points": pd.to_numeric(
                df["participant.payoff"], errors="coerce"
            ),
        }
    )
    keep = nonempty(out["email"]) | nonempty(out["student_id"])
    out = out.loc[keep].copy()
    out["experimental_payoff"] = out["experimental_payoff_points"].map(
        lambda pts: money(float(pts) * exchange_rate) if pd.notna(pts) else None
    )
    out["participation_fee"] = money(participation_fee)
    out["total_payment"] = out.apply(
        lambda r: money(r["participation_fee"] + r["experimental_payoff"])
        if pd.notna(r["experimental_payoff"])
        else None,
        axis=1,
    )
    out = out.sort_values(["email", "student_id"], kind="mergesort").reset_index(
        drop=True
    )
    return out


def write_payments_csv(payments: pd.DataFrame, dest: Path) -> Path:
    dest.parent.mkdir(parents=True, exist_ok=True)
    payments.to_csv(dest, index=False, quoting=csv.QUOTE_NONNUMERIC)
    return dest


def write_payments_xlsx(
    payments: pd.DataFrame,
    dest: Path,
    *,
    session_id: str,
    record: dict | None = None,
    incomplete: pd.DataFrame | None = None,
) -> Path:
    dest.parent.mkdir(parents=True, exist_ok=True)
    lab = payments[
        ["email", "student_id", "participation_fee", "experimental_payoff", "total_payment"]
    ].copy()

    with pd.ExcelWriter(dest, engine="openpyxl") as writer:
        lab.to_excel(writer, sheet_name="payments", index=False)
        pay_ws = writer.sheets["payments"]
        _autosize(pay_ws)
        _text_column(pay_ws, column="B", n_rows=len(lab))
        _currency_columns(
            pay_ws,
            columns=("C", "D", "E"),
            n_rows=len(lab),
        )

        summary_rows = _summary_rows(session_id, payments, record)
        summary = pd.DataFrame(summary_rows, columns=["field", "value"])
        summary.to_excel(writer, sheet_name="session", index=False)
        _autosize(writer.sheets["session"])

        if incomplete is not None and not incomplete.empty:
            cols = [
                c
                for c in (
                    "participant.code",
                    "participant._current_app_name",
                    "participant._current_page_name",
                    "participant._index_in_pages",
                    "participant.time_started_utc",
                    "participant.payoff",
                )
                if c in incomplete.columns
            ]
            incomplete[cols].to_excel(writer, sheet_name="incomplete", index=False)
            _autosize(writer.sheets["incomplete"])

    return dest


def copy_payments_to_processed(src: Path, session_id: str) -> Path:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    dest = PROCESSED_DIR / payments_filename(session_id)
    dest.write_bytes(src.read_bytes())
    return dest


def _summary_rows(
    session_id: str, payments: pd.DataFrame, record: dict | None
) -> list[tuple]:
    rows = [
        ("session_id", session_id),
        ("n_paid", len(payments)),
        (
            "experimental_payoff_cad_sum",
            float(payments["experimental_payoff"].sum()) if not payments.empty else 0,
        ),
        (
            "participation_fee_cad_sum",
            float(payments["participation_fee"].sum()) if not payments.empty else 0,
        ),
        (
            "total_payment_cad_sum",
            float(payments["total_payment"].sum()) if not payments.empty else 0,
        ),
    ]
    if record:
        rows.extend(
            [
                ("oTree_codes", ", ".join(record.get("oTree_codes") or [])),
                ("export_date", record.get("export_date")),
                ("processed_at", record.get("processed_at")),
                ("n_started", record["counts"]["started"]),
                ("n_completed", record["counts"]["completed"]),
                ("n_incomplete", record["counts"]["incomplete"]),
                ("flags", "; ".join(record.get("flags") or [])),
            ]
        )
    return rows


def _autosize(ws) -> None:
    for column in ws.columns:
        letter = column[0].column_letter
        width = min(
            48,
            max(10, max(len(str(cell.value)) if cell.value is not None else 0 for cell in column) + 2),
        )
        ws.column_dimensions[letter].width = width
    ws.auto_filter.ref = ws.dimensions
    ws.freeze_panes = "A2"


def _currency_columns(ws, *, columns: tuple[str, ...], n_rows: int) -> None:
    for col in columns:
        for row in range(2, n_rows + 2):
            ws[f"{col}{row}"].number_format = '"$"#,##0.00'


def _text_column(ws, *, column: str, n_rows: int) -> None:
    for row in range(2, n_rows + 2):
        cell = ws[f"{column}{row}"]
        if cell.value is not None:
            cell.value = str(cell.value)
        cell.number_format = "@"
