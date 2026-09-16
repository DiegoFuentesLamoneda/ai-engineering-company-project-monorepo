# `docs` folder

This folder holds **cross-cutting documentation** for the monorepo: architecture guides, technical decisions, conventions, processes, and any material shared across applications, pipelines, agents, and workflows.

- **Main purpose**: provide a single place for “global” project documentation (not tied to one app or agent only).
- **Recommendation**: organize docs by topic (architecture, deployment, data, security, observability, etc.) and keep links from each component’s README to these guides.

> _Spanish version: [README.es.md](./README.es.md)._

## What lives here

| Document | What it is |
| --- | --- |
| [`ARCHITECTURE_PROPOSAL.md`](./ARCHITECTURE_PROPOSAL.md) | Backend architecture proposal: chosen pattern, structure of `services/nexova-api/`, router organisation, frontend/backend coexistence, technical decisions and risks. Milestone 5 |
| [`contexts/`](./contexts/) | Syllabus contexts synced with [`scripts/sync_contexts.py`](../scripts/sync_contexts.py). **Not edited by hand** |
| `contexts-archive/` | Contexts for the other companies in the track. **Never read, never searched** — see [`AGENTS.md`](../AGENTS.md) |
