# `scripts` folder

This folder contains **helper scripts** for the monorepo: development automation, maintenance utilities, repetitive tasks (setup, lint, migrations, data generation, etc.), and internal tooling.

- **Main purpose**: group support tools that do not belong to a specific app, agent, or pipeline but make the team’s work easier.
- **Recommendation**: document each script (what it does, parameters, requirements, usage examples) and keep them reproducible (and safe) across environments.

> _Spanish version: [README.es.md](./README.es.md)._

## Scripts

| Script | What it does |
| --- | --- |
| [`analyze.py`](./analyze.py) | Analyses the support helpdesk CSV export: validates each ticket, prints the metrics to the console and, if confirmed, writes `results.csv` (one metric per row) in the folder it is run from |
| [`seed_incidents.py`](./seed_incidents.py) | Loads the history in that same CSV into the incident manager (`origin: customer`, `branch: central`). Lists the rejected rows in the console and can be rerun without duplicating |
| [`sync_contexts.py`](./sync_contexts.py) | Syncs `docs/contexts/` from the course syllabus |

### `analyze.py`

```bash
python scripts/analyze.py scripts/incidents-nexova.csv
```

- **Required argument:** the path to the CSV. Without it, the script prints its usage and exits.
- **Requirements:** Python 3.11 or later. No dependencies: the logic lives in
  [`packages/shared/incident-analysis`](../packages/shared/incident-analysis/), the same code the API uses.
- [`incidents-nexova.csv`](./incidents-nexova.csv) is the briefing's test file:
  100 records, 96 valid and 4 invalid.
- `results.csv` is in `.gitignore`: it is an output, not versioned.
- Customer emails never appear in any output, not even in errors.

### `seed_incidents.py`

From the repository root:

```bash
uv run --project services/api python scripts/seed_incidents.py
```

- **Optional argument:** the path to the CSV. Defaults to [`incidents-nexova.csv`](./incidents-nexova.csv).
- **Requirements:** the API environment (`uv sync` in [`services/api`](../services/api/)). `--project services/api`
  uses it without activating it. It is needed because the seed stores data with TinyDB and the API's `Incident` model.
- **Where it writes:** to the same file the API reads, `services/api/storage/incidents.json`, or to
  `NEXOVA_API_INCIDENTS_DB_PATH` if it is set.
- **What it loads:** the briefing's transformations come from the shared package
  (`incident_analysis.plan_seed_file`), with the same validation as `analyze.py`. From the briefing CSV, 96
  incidents go in: 27 `open`, 56 `resolved` and 13 `discarded`.
- **Idempotent:** each loaded `ticket_id` is recorded in the `seed_imports` table, so the second run inserts 0.
  The `ticket_id` is not stored in the incident.
- **Rejected rows:** all of them are listed, with their line and `ticket_id`, never with the email.


## Errors

All three scripts follow the same rule: **an error is a message on `stderr` and exit code `1`, never a traceback**.
That way a scheduled task or a pipeline that runs them stops and knows why.

- **`analyze.py` and `seed_incidents.py`:** a file that does not exist or cannot be opened, a malformed CSV, invalid
  configuration, a corrupt or read-only database, and `results.csv` open in another program (Excel locks it).
- **`sync_contexts.py`:** network, timeout, a GitHub response without the tree (rate limit exhausted) and every
  download or write that fails. If any fails, it carries on with the rest and ends in "Incompleto" with code `1`,
  not "Listo".
