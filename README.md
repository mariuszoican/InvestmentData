# Data Purchase — analysis

Lab-session registry and payment file for the Data Purchase experiment.

## Layout

```
config/
  sessions.yaml      # lab-session registry (ids, export dates, oTree codes)
  parameters.yaml    # show-up fee, E$→CAD rate, completion pages
data/
  raw/{session_id}/  # immutable oTree dumps — never edit
  payments/          # payments_{session id}.xlsx (lab folder date)
  processed/         # processed_panels.csv
  round_metadata.csv # round-level chart / return metadata
  archive/           # pilots / excluded sessions
src/build/           # process_payments.py, process_panels.py
```

## Setup

```bash
cd datapurchase_analysis
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## How to drop new raw data

1. Create `data/raw/YYYYMMDD/` (add `_AM` / `_PM` if two sessions share a day).
2. Copy the oTree CSVs in, keeping export filenames. `post_exp_YYYY-MM-DD.csv` is required for payments.
3. Register the session in `config/sessions.yaml`:

   ```yaml
   - id: "20260824"
     export_date: "2026-08-24"    # must match CSV filename stamp
     oTree_codes: [9vfoiax5]
     include: true
     notes: "Lab session FNCE 449/668"
   ```

4. Never overwrite an existing raw folder. Never hand-edit files under `data/raw/`.

## Payments

```bash
make payments ID=20260824
```

Writes `data/payments/payments_{session id}.xlsx` using the lab folder date (`20260824`), plus a sidecar `session_log_{session id}.yaml`. Completers are people on `FinalForProlific` or `Payoff`.

| Column | Source |
|---|---|
| `email` | `player.email` |
| `student_id` | `player.student_id` |
| `participation_fee` | `config/parameters.yaml` |
| `experimental_payoff` | `participant.payoff` (E$) × `exchange_rate` |
| `total_payment` | show-up + experimental payoff |

After changing the exchange rate, re-run the same command.

## Analysis panel

```bash
make panels
```

Builds one participant × round file, `data/processed/processed_panels.csv`, from every
`include: true` session in `config/sessions.yaml`. Training rounds are dropped;
completers are the same pages as for payments. Round metadata comes from
`data/round_metadata.csv` and is joined on `series_round` (the shuffled chart id),
not display `round_number`.
