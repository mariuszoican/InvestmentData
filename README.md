# Data Purchase — analysis

Pipeline for the laboratory experiment in the Data Purchase study.
Raw oTree exports are registered per lab session, logged, turned into
payment workbooks, and (later) into analysis panels.

## Layout

```
config/
  sessions.yaml      # lab-session registry (ids, export dates, oTree codes)
  parameters.yaml    # show-up fee, E$→CAD rate, completion pages
data/
  raw/{session_id}/  # immutable oTree dumps — never edit
  interim/           # per-session log, payments, first-pass panels (rebuildable)
  processed/         # concatenated analysis sample (*_full.csv) + payments_{id}.xlsx
  archive/           # pilots / excluded sessions
src/
  build/             # Python: process_session → build_panels
  analyze/           # hypothesis tests (placeholder)
  explore/           # scratch
output/
  tables/
  figures/
```

## Setup

```bash
cd datapurchase_analysis
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## How to drop new raw data

1. **Create a session folder** under `data/raw/` named by the lab calendar day:
   - `YYYYMMDD` for a single session that day
   - `YYYYMMDD_AM` / `YYYYMMDD_PM` when two sessions share a calendar day

2. **Copy the oTree export CSVs into that folder**, keeping the export filenames.
   Expected files (date stamp = oTree export date, `YYYY-MM-DD`):

   | File | Required? |
   |---|---|
   | `intro_YYYY-MM-DD.csv` | yes |
   | `main_YYYY-MM-DD.csv` | yes |
   | `post_exp_YYYY-MM-DD.csv` | yes (payments + completion) |
   | `PageTimes-YYYY-MM-DD.csv` | keep |
   | `all_apps_wide_YYYY-MM-DD.csv` | keep |

3. **Watch the export-date vs folder-date mismatch.**
   Folder = lab day; filename date = when the CSV was exported. They can differ
   if the export ran overnight. Always record the **filename** date in the registry.

4. **Register the session** in `config/sessions.yaml`:

   ```yaml
   - id: "20260824"
     export_date: "2026-08-24"    # must match CSV filename stamp
     oTree_codes: [9vfoiax5]      # session.code values to keep
     include: true                # false → archive / exclude from full panels
     notes: "Lab session 1"
   ```

5. **Never overwrite** an existing raw folder. New export → new folder (or move the
   old one under `data/archive/`).

6. **Do not hand-edit files under `data/raw/`.** Fix logic in `src/build/` instead.

## Analysis flow

```
data/raw/{id}/
      │
      ▼  make session ID=…   or   make panels
data/interim/{id}/
  session_log.yaml
  participant_payments.csv
  payments_{id}.xlsx
  participant_round_panel.csv   # first-pass shell
  participant_panel.csv         # first-pass shell
      │
      ▼  (make panels concatenates include:true sessions)
data/processed/
  *_full.csv
  payments_{id}.xlsx
  session_log.md                # append-only lab log
```

### Commands

| Command | What it does |
|---|---|
| `make panels` | Process every `include: true` session, then write `data/processed/*_full.csv` |
| `make session ID=20260824` | Process one session into `data/interim/` and write `payments_{id}.xlsx` |
| `make payments ID=20260824` | Same as `session` (log + payments + first-pass panels) |
| `make clean-interim` | Delete rebuildable interim panels |

Equivalent without Make:

```bash
export PYTHONPATH=src/build
python src/build/build_panels.py
python src/build/process_session.py --session 20260824
```

## Session logging

Processing a session always writes:

- `data/interim/{id}/session_log.yaml` — counts, payoff range, incomplete codes, data-quality flags
- `data/processed/session_log.md` — append-only human-readable lab log (re-runs are kept)

A participant **completed** if they visited the session and their current page is
`FinalForProlific` or `Payoff`. Started-but-not-finished people are listed on the
Excel `incomplete` sheet and in the log; they are not paid by this script.

## Payments

The lab workbook is `data/processed/payments_{session_id}.xlsx` (copied from interim).

Columns on the `payments` sheet, one row per completer:

| Column | Source |
|---|---|
| `email` | `player.email` |
| `student_id` | `player.student_id` |
| `participation_fee` | `config/parameters.yaml` (CAD 15) |
| `experimental_payoff` | `participant.payoff` (E$) × `exchange_rate` (0.03) |
| `total_payment` | show-up + experimental payoff |

`participant.payoff` is the oTree E$ total (trade + bonuses + quiz + Holt–Laury).
The CAD conversion uses half-up rounding to cents.

## Session registry conventions

- `id` — folder name under `data/raw/` (or `data/archive/` if `raw_root: archive`).
  Always quote it in YAML (`id: "20260824"`) so it is not parsed as an integer.
- `export_date` — `YYYY-MM-DD` substring in the CSV filenames.
- `oTree_codes` — `session.code` values retained; other sessions in the same export are dropped.
- `include: false` — keep raw for provenance but omit from the analysis sample.
- Payment constants live in `config/parameters.yaml`.

## Notes

- Payment workbooks contain email and student ID (PII). Treat `data/processed/payments_*.xlsx` as confidential.
- Round- and participant-level panels in `src/build/process_session.py` are a first pass
  so the pipeline runs; replace them when the analysis spec is ready.
