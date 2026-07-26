# Final Project — Distributed Cops-and-Robbers over a Peer-to-Peer Network

Planning workspace for the course final project (Dr. Yoram Segal, "Orchestration of AI Agents",
rules book `police_thief_p2p.pdf` v3.0.0 — bundled in the reference repo
[`rmisegal/Game-P2P-Cop-Chase`](https://github.com/rmisegal/Game-P2P-Cop-Chase) under `docs/`).

| Document | Purpose |
|---|---|
| [`docs/GAP_ANALYSIS.md`](docs/GAP_ANALYSIS.md) | HW6 vs. final-project spec — what carries over, what must be rebuilt |
| [`docs/PRD.md`](docs/PRD.md) | Master product requirements: rules, 55 mandatory-rule map, binding parameters, acceptance criteria |
| [`docs/PRD/PRD-1…7`](docs/PRD/) | Seven stage PRDs — one per build layer (book §10.3): base logic → MCP → strategy → language+scent → tunneling → crypto → reporting/GUI |
| [`docs/PLAN.md`](docs/PLAN.md) | Architecture, ADRs, module tree, HW6 reuse map, strategy/tactics design, milestones, risks |
| [`docs/STRATEGY.md`](docs/STRATEGY.md) | Living tactics doctrine — the book's "core of the grade": brain contract, police/thief doctrine, evaluation protocol |
| [`docs/TODO.md`](docs/TODO.md) | Full task breakdown with binary milestone gates, league ops, submission checklist |

Build order is strict (book §10.4): each stage's gate must be demonstrably green before the next
stage begins.
