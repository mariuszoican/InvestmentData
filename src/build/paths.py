"""Repo paths and session-registry helpers."""

from __future__ import annotations

from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
CONFIG_DIR = REPO_ROOT / "config"
DATA_DIR = REPO_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
PAYMENTS_DIR = DATA_DIR / "payments"
PROCESSED_DIR = DATA_DIR / "processed"
ARCHIVE_DIR = DATA_DIR / "archive"
ROUND_METADATA = DATA_DIR / "round_metadata.csv"


def load_sessions(path: Path | None = None) -> list[dict]:
    cfg = path or (CONFIG_DIR / "sessions.yaml")
    with open(cfg) as f:
        return yaml.safe_load(f)["sessions"]


def load_parameters(path: Path | None = None) -> dict:
    cfg = path or (CONFIG_DIR / "parameters.yaml")
    with open(cfg) as f:
        return yaml.safe_load(f)


def get_session(session_id: str) -> dict:
    session_id = str(session_id)
    for s in load_sessions():
        if str(s["id"]) == session_id:
            s = dict(s)
            s["id"] = str(s["id"])
            return s
    raise KeyError(f"Session {session_id!r} not found in config/sessions.yaml")


def raw_dir_for(session: dict) -> Path:
    root = ARCHIVE_DIR if session.get("raw_root") == "archive" else RAW_DIR
    return root / str(session["id"])


def payments_xlsx_path(session_id: str) -> Path:
    """Lab-facing file: data/payments/payments_{session_id}.xlsx."""
    return PAYMENTS_DIR / f"payments_{session_id}.xlsx"


def session_log_path(session_id: str) -> Path:
    return PAYMENTS_DIR / f"session_log_{session_id}.yaml"


def panel_path() -> Path:
    return PROCESSED_DIR / "processed_panels.csv"
