# `scripts` folder

This folder contains **helper scripts** for the monorepo: development automation, maintenance utilities, repetitive tasks (setup, lint, migrations, data generation, etc.), and internal tooling.

- **Main purpose**: group support tools that do not belong to a specific app, agent, or pipeline but make the team’s work easier.
- **Recommendation**: document each script (what it does, parameters, requirements, usage examples) and keep them reproducible (and safe) across environments.

> _Spanish version: [README.es.md](./README.es.md)._

## Scripts

| Script | What it does |
| --- | --- |
| [`analyze.py`](./analyze.py) | Analyses the support helpdesk CSV export: validates each ticket, prints the metrics to the console and, if confirmed, writes `results.csv` (one metric per row) in the folder it is run from |
| [`sync_contexts.py`](./sync_contexts.py) | Syncs `docs/contexts/` from the course syllabus |

### `analyze.py`

```bash
python scripts/analyze.py scripts/incidents-nexova.csv
```

- **Required argument:** the path to the CSV. Without it, the script prints its usage and exits.
- **Requirements:** Python 3.11 or later. No dependencies: the logic lives in
  [`packages/incident-analysis`](../packages/incident-analysis/), the same code the API uses.
- [`incidents-nexova.csv`](./incidents-nexova.csv) is the briefing's test file:
  100 records, 96 valid and 4 invalid.
- `results.csv` is in `.gitignore`: it is an output, not versioned.
- Customer emails never appear in any output, not even in errors.

