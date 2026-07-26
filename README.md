# p2p-pursuit — Distributed Cops-and-Robbers over a Peer-to-Peer Network

Final project for Dr. Yoram Segal's **"Orchestration of AI Agents"** course (rules book
`police_thief_p2p.pdf` **v3.0.0**, bundled in the reference repo
[`rmisegal/Game-P2P-Cop-Chase`](https://github.com/rmisegal/Game-P2P-Cop-Chase)).

Two fully autonomous, symmetric AI peers — a **Police** and a **Thief** — chase each other on a
7×7 grid with **no referee and no central server**. Each peer is simultaneously a **FastMCP
server and client**. Neither side ever sees the opponent: each fuses the opponent's decaying
**pheromone field** with free-language **hints that may lie** into a **Bayesian belief map**.
Honesty is enforced by mathematics: every step is sealed with **SHA-256 commit → acknowledge →
reveal → mutual audit**; any tampering is a technical loss, no appeal.

**Team `ahk-yosi`** — Yosef Shanaa (`213314859`) · Ahmad Kaiss (`325811255`).

## Status

| Layer (book §10.3) | State |
|---|---|
| 1. Base logic — board, 4-orthogonal moves, barriers, capture, scoring | ✅ implemented + tested |
| 2. FastMCP P2P infra — peer server+client, state machine, deadline tracker, watchdog | ✅ |
| 3. Strategy module — `BrainBase` plug-in, police/thief doctrine, sim lab | ✅ |
| 4. Language + scent — emission/decay, belief map, trust model, 4 banter providers | ✅ |
| 5. Cloud exposure — public-URL config, smoke probe, [`docs/RUNBOOK.md`](docs/RUNBOOK.md), CI chaos drills (latency / dead link / silence) | ✅ code / ☐ live tunnel drill |
| 6. Crypto — commit-reveal, nonces, mutual audit, step-0 declaration, locks | ✅ |
| 7. Reporting + GUI — 4 JSON artifacts, Gatekeeper, Gmail (draft/send), live GUI, replay verifier | ✅ |

**Quality gate:** 89 tests, coverage ≥94% (gate 85%), Ruff clean, CI on every push.
**Strategy (v3, see [`docs/STRATEGY.md`](docs/STRATEGY.md)):** scent-trail interception police +
risk-aware juking thief — cross-version validated; police captures a random walker 27/30,
thief survives a random police 30/30 (both CI-gated).
League play vs. real opposing teams and the two-repo submission split are still ahead
(see [`docs/TODO.md`](docs/TODO.md) §8–9).

## Installation

**System requirements:** Python ≥ 3.13, [`uv`](https://docs.astral.sh/uv/) (the only package
manager used — never pip/venv directly), Linux/WSL2/macOS/Windows; Tk only for the GUIs
(headless works everywhere); no LLM, key or network needed for the default game.

```bash
git clone https://github.com/yosefshanaa/final_Project && cd final_Project
uv sync                     # core + dev from the lockfile
uv sync --extra gmail       # + Google libs (only for real report sending)
uv sync --extra llm         # + anthropic SDK (only for claude_api banter)
uv sync --extra analysis    # + matplotlib (only for the sweep charts)
```

**Environment variables:** copy `.env-example` → `.env` and fill in only what you use
(`ANTHROPIC_API_KEY` for `claude_api` banter; nothing for the default template mode).

**Troubleshooting:** `Address already in use` → a stale peer holds 8801/8802, kill it or change
`my_port`; GUI fails under WSL → run `--no-gui` (or install an X server); Gmail
`invalid_grant` → rerun `uv run p2p-pursuit authorize` (Testing-mode refresh tokens expire);
opponent unreachable → `uv run p2p-pursuit smoke <their-url>` and check the tunnel.

## Usage

```bash
# In-process series (tactics lab / demo) - 6 sub-games, artifacts + result JSON:
uv run p2p-pursuit sim --seed 42

# Two real peers over FastMCP HTTP (two terminals; start order doesn't matter):
uv run p2p-pursuit peer --role thief  --no-gui   # terminal 1 (port 8801)
uv run p2p-pursuit peer --role police --no-gui   # terminal 2 (port 8802)
# drop --no-gui for the live Tkinter belief-heatmap GUI (turn banner, hints feed)

# Verify + view a sealed log (green "Verified OK" / red TAMPERED; exit 3 on tamper):
uv run p2p-pursuit replay --log results/sim-*/log_*_g01.json --no-gui

# Probe a (remote) peer endpoint / one-time Gmail consent:
uv run p2p-pursuit smoke http://127.0.0.1:8801/mcp
uv run p2p-pursuit authorize
```

Flags: `--games N` (dev override; counted matches force 6), `--seed` (reproducibility),
`--counted --prior-counted K` (league match + truthful game-count declaration), `--out DIR`
(artifact location), `--config-dir DIR` (non-default role directory). Typical league workflow:
warm-up → negotiate constitution → `peer --counted` → archive artifacts → both teams' reports
go out automatically ([`docs/RUNBOOK.md`](docs/RUNBOOK.md) is the step-by-step).

## Configuration guide

| File | Role | Key parameters |
|---|---|---|
| `config/<role>/game.json` | **shared constitution** — byte-identical for both teams, SHA-256-locked at handshake | board/starts/first-mover; barrier quota 14; move cap + survival 35; scoring 20/5, 5/10, tie 2; pheromone constants (fixed); league + timer params |
| `config/<role>/game.toml` | private per-peer, never crosses the wire | `my_port`, `opponent_url`, `turn_timeout_seconds`; `[strategy]` brain classes; `[trash_talk] provider/every_n_steps`; `[llm]`; `[email] recipient/mode` |
| `config/<role>/rate_limits.json` | versioned Gatekeeper defaults (constitution section overrides) | rpm 30, retries, queue depth 100, daily quota |
| `config/logging_config.json` | Python logging tree | level, format |

Shared values are negotiated per match (minimums may only rise); a per-match copy of the agreed
constitution is written into the artifacts and archived under `matches/`.

## How a turn works

**observe** (opponent's served scent + hint) → **belief update** (scent likelihood → motion
diffusion → trust-weighted hint) → **brain decides** move / barrier + hint + intent →
**commit** (SHA-256 of the sealed record) → opponent **ack** → **reveal** (public projection
only: hint, scent, barrier declarations — moves stay sealed until the audit) → **log**. After
both moved, every scent field decays (ρ=0.10). Capture claims ride inside the reveal and get
a cryptographically bound truthful answer; barrier-capture and enclosure force honest
confessions; survival at 35 steps ends the sub-game. After every sub-game both peers exchange
full sealed logs (nonces included) and **audit each other** — one mismatch = `TAMPERED` = 0/0.

## Layout

```
src/p2p_pursuit/
  sdk/        PursuitSDK - single business-logic entry point (CLI/GUI go through it)
  domain/     board, rules, scoring, scent, belief, trust, hints,
              crypto, protocol, audit, declarations, negotiation, brains_base
  strategy/   police_brain, thief_brain, pathing, talk_template, talk_llm
  peer/       engine_state, turn_engine, service, runtime(+reports), local_match,
              state_machine, deadline, watchdog, log_manager, audit_bridge
  infra/      mcp_server, mcp_client, transport, email_sender
  report/     artifacts (declaration/config/log/result), results
  gui/        live_view (belief heatmap + banner), replay_view, replay_data, view_model
  shared/     config (JSON constitution + private TOML), gatekeeper, rate_limiter, sysinfo
config/police/  config/thief/   # byte-identical game.json + role-private game.toml
tests/unit/  tests/integration/ # 89 tests incl. real MCP round-trip + cheat harness
docs/        PRD, PRD/1..7, PLAN, TODO, STRATEGY, GAP_ANALYSIS
```

## Documentation

| Doc | What |
|---|---|
| [`docs/PRD.md`](docs/PRD.md) + [`docs/PRD/`](docs/PRD/) | Master requirements, 55-rule map, binding parameters, seven stage PRDs |
| [`docs/PLAN.md`](docs/PLAN.md) | Architecture, ADRs, reuse map, milestones, risks |
| [`docs/STRATEGY.md`](docs/STRATEGY.md) | The graded core: doctrine + evaluation numbers |
| [`docs/TODO.md`](docs/TODO.md) | Task tracking with milestone gates |
| [`docs/GAP_ANALYSIS.md`](docs/GAP_ANALYSIS.md) | HW6 vs. final-project spec |
| [`docs/RUNBOOK.md`](docs/RUNBOOK.md) | Tunnel + league match operations, interop with reference-derived peers |
| [`docs/PROMPT_BOOK.md`](docs/PROMPT_BOOK.md) | Prompt-engineering log (guidelines §8.3) |
| [`docs/COST_ANALYSIS.md`](docs/COST_ANALYSIS.md) | LLM token/cost model per banter provider |

## Interpretation log (academic freedom, book p. 5)

Decisions where the book under-specifies or contradicts itself — documented as required:

1. **Per-step Reveal discloses the public projection only** (hint, served scent field, barrier
   declaration). Moves, positions, intent and nonces are revealed at the **sub-game audit**.
   Figure 6's "Reveal: Move + Hint" read literally would make positions fully computable from
   the known starts and collapse the partial-observability premise of ch. 1/4/6; the
   lecturer's reference implementation resolves it the same way.
2. **First mover = thief**, agreed at handshake (the book never fixes it).
3. **Capture-claim semantics**: the police's claim is a query ("I am at X — are you here?");
   only the thief's sealed truthful answer constitutes the capture event. The claim itself
   legitimately leaks the police position — its strategic price. Claims ride inside the reveal
   so cross-peer record ordering can never race.
4. **Scent serving is pre-emission**: each step serves the field *before* that step's deposit,
   so the freshest visible cell is ≈0.81 — exactly the book's ch. 4.4 worked example — and the
   opponent sees where you *were*, never where you are.
5. **τ is clamped to [0, 0.9]** (the book's stated range) since additive re-emission would
   otherwise exceed the focal cap; decay ticks are applied per own-step (equivalent to
   full-turn decay under strict alternation, and exactly reproducible in the audit).

## Secrets & Gmail

`credentials.json` / `token.json` (Gmail OAuth, send-only scope) are git-ignored and never
committed. The client credentials are reused from HW6; the refresh token needs a **one-time
interactive consent**:

```bash
uv run p2p-pursuit authorize     # browser consent -> writes token.json
```

Then set `[email] mode = "send"` in `config/<role>/game.toml` for league matches. Without a
valid token (or in `draft` mode) the reporter runs dry-run and says so - a send-only scope
cannot create real Gmail drafts, so `draft` means "build the MIME locally, do not call Gmail".

## Contributing

Quality gates every change must keep green (CI enforces): `uv run ruff check` — zero violations
(E/F/W/I/N/UP/B/C4/SIM); `uv run pytest --cov` — coverage ≥ 85%; every source/test file ≤ 150
code lines (split, never compress); TDD — a new module ships with its `tests/` mirror; all
business logic behind the `PursuitSDK` facade; every external call behind the Gatekeeper; all
tunables from `config/` — nothing hard-coded; English-only comments explaining *why*, not *what*.
Branch off `master`, keep commits scoped, update `docs/` with the change.

## License & credits

MIT (see `pyproject.toml`). Assignment and rules book: **Dr. Yoram Segal**, "Orchestration of
AI Agents", University of Haifa; public reference simulation:
[`rmisegal/Game-P2P-Cop-Chase`](https://github.com/rmisegal/Game-P2P-Cop-Chase) (studied as a
learning aid per its license — our implementation and strategies are original). Third-party
libraries under their own licenses: [FastMCP](https://gofastmcp.com/), Google API client +
auth libs (Gmail), optional [Anthropic SDK](https://github.com/anthropics/anthropic-sdk-python)
/ [Ollama](https://ollama.com), and the toolchain — [uv](https://docs.astral.sh/uv/),
[Ruff](https://docs.astral.sh/ruff/), [pytest](https://pytest.org/),
[Matplotlib](https://matplotlib.org/) (analysis extra). Built with Claude Code; the full
prompt-engineering log is in [`docs/PROMPT_BOOK.md`](docs/PROMPT_BOOK.md).
