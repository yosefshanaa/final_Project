# TODO — Distributed Cops-and-Robbers over P2P

Tracks execution of [`PLAN.md`](PLAN.md); requirements in [`PRD.md`](PRD.md) + [`docs/PRD/`](PRD/).
Rule: **a milestone gate must be demonstrably green before the next stage starts.**
Legend: `[ ]` todo · `[~]` in progress · `[x]` done.

## 0. Project bootstrap
- [ ] Create workspace repo + `uv init` (Python 3.13), Ruff, pytest, coverage gate ≥85%, file-length lint
- [ ] Create the two GitHub repos `p2p-police-agent` / `p2p-thief-agent` (private, shared with `rmisegal@gmail.com`) — or public; decide with partner
- [ ] `.gitignore` **first commit**: `credentials.json`, `token.json`, `.env`, `*.pem`, `*.key`, `logs/`, `results/`
- [ ] Two-repo sync script (workspace → both repos, secrets excluded)
- [ ] CI (lint + tests) on both repos
- [ ] Copy this docs set (PRD, PRD/, PLAN, TODO, GAP_ANALYSIS) into both repos (mandatory content, rule #50)
- [ ] Choose 8-char group code (no spaces) with partner; record here: `________`
- [ ] Skim reference repo `docs/STRATEGY.md` + sample artifacts; extract interop contract notes
- [ ] Obtain the course-intro file "Recommendations for writing & submitting software with AI agents" and audit our repos against it (it is the stated grading rubric)
- [ ] Start the README **interpretation log** (academic-freedom decisions: first mover = thief; capture-claim query semantics; + anything found later)

## 1. Stage 1 — Base logic (PRD-1)
- [ ] `domain/board.py` — grid, coordinates, occupancy (config-driven size ≥7×7)
- [ ] `domain/rules.py` — N/S/E/W/STAY validator (no diagonals, off-board, barrier cells); apply(); events
- [ ] Barriers: no-move turn placement, own/4-adjacent target, quota (14), permanence
- [ ] Capture paths: police lands on thief · barrier onto thief (#46) · enclosure (#47)
- [ ] `domain/scoring.py` — 20/5, 5/10, 0/0, tie 2/2 from config (#48)
- [ ] `shared/config.py` — shared `game.json` (schema + canonical `config_sha256`) + private `game.toml`; JSON-overrides-TOML
- [ ] Step/turn accounting + move-cap/survival-threshold cutoffs; full-turn boundary event
- [ ] Dev-only text board printer (quarantined module)
- [ ] Unit tests per PRD-1 · **GATE M1 demo recorded**

## 2. Stage 2 — MCP infrastructure (PRD-2)
- [ ] `peer/runtime.py` skeleton — `--role police|thief`, config dir per role
- [ ] `infra/mcp_server.py` — FastMCP tools: handshake, receive_commit, acknowledge, receive_reveal, capture_claim, audit_exchange, game_status, health
- [ ] `infra/mcp_client.py` — retry-until-up connect; stamped, deadline-tracked calls
- [ ] `peer/orchestrator.py` — single-gateway wiring (#3)
- [ ] `peer/state_machine.py` — transition table + rejection (#4–5)
- [ ] `peer/deadline.py` (#6) + `peer/watchdog.py` (persist + controlled shutdown) (#7)
- [ ] `peer/log_manager.py` — per-step JSON records (crypto fields reserved)
- [ ] Chaos tests: kill opponent, freeze main loop, latency injection
- [ ] Integration: scripted geometric turns across two subprocesses · **GATE M2 demo recorded**

## 3. Stage 3 — Blind strategy (PRD-3)
- [ ] `domain/brains_base.py` — `BrainBase`, `[strategy]` TOML plug-in loading (`package.module:Class`)
- [ ] Safe-fallback wrapper (illegal brain output → legal move; never forfeit on our bug)
- [ ] `strategy/pathing.py` — barrier-aware BFS/Manhattan
- [ ] `strategy/police_brain.py` v1 — pursuit + barrier v1 + flood-fill self-trap veto
- [ ] `strategy/thief_brain.py` v1 — distance × mobility evasion
- [ ] Sim-runner (seeded headless brain-vs-brain tournaments + stats)
- [ ] Regression bounds vs random baselines in CI · **GATE M3 demo recorded**

## 4. Stage 4 — Language + scent (PRD-4)
- [ ] `domain/scent.py` — 5×5 emission (τ₀=0.9), radial falloff, decay ρ=0.10; golden-matrix tests (incl. 0.9→0.81)
- [ ] Scent served to opponent / opponent's field ingested (own field never read for self)
- [ ] Scent-model lock document (formula + numeric example) → canonical hash export (for #23)
- [ ] `domain/belief.py` — motion diffusion ⊕ scent likelihood ⊕ hint likelihood; normalized heatmap; entropy/argmax API
- [ ] `domain/trust.py` — trust coefficient; contradiction detector (book's north/SE case as unit test)
- [ ] Hint parsing (rule-based free-text; direction/landmark/distance; garbage-tolerant)
- [ ] Hint generation: `template` provider (0 tokens, word-cap, `[map area]` landmarks) + intent flag
- [ ] Optional providers: `ollama`, `claude_api`, `claude_cli` + `every_n_steps` + fallback-to-template
- [ ] Token metering vs budget (~200k) → result artifact feed (#54)
- [ ] Brains v2 under fog (belief-driven; police corridors; thief scent-aware pathing + scent-consistent lies)
- [ ] Fog sim-runner stats + regression bounds · **GATE M4 demo recorded**

## 5. Stage 5 — Cloud & tunneling (PRD-5)
- [ ] ngrok (or Localtonet) account + runbook (`docs/RUNBOOK.md`): bring-up, URL rotation, teardown
- [ ] Public-URL config wiring (bind 0.0.0.0; `opponent_url` in TOML)
- [ ] `handshake` negotiation for real: constitution agreement, `config_sha256` exchange, refuse-on-mismatch (#11–12); per-match config copy persisted under unique name
- [ ] WAN resilience pass: timeouts under latency, reconnect-within-window, tunnel-kill ⇒ clean technical loss
- [ ] `smoke <url>` probe tool
- [ ] Two-machine full sub-game over tunnels · **GATE M5 demo recorded**

## 6. Stage 6 — Crypto (PRD-6)
- [ ] `domain/crypto.py` — `canonical_bytes`, commit(record)→(H,nonce) with `secrets`, verify (`compare_digest`); cross-platform golden vectors
- [ ] Sealed record = {state, move, intent, hint, verdict, step, role, sub_game, nonce}
- [ ] Protocol wiring: COMMIT (hash only) → ACK → REVEAL (nonce withheld) → VERIFYING (legality + consistency)
- [ ] `domain/audit.py` — final nonce exchange, full-log re-hash, `Verified OK` / `TAMPERED` verdict (#19)
- [ ] Capture-claim truthful-answer path; sealed barrier declarations (#15–16, #21–22)
- [ ] `domain/declarations.py` — step-0 `declaration_<game_id>.json`: both teams + members, 4 repo URLs, both MCP URLs, hardware (OS/CPU/RAM/GPU), LLM model, agreed token cap, code version, **git commit hash** (→ `github_commit` in result), game number, start/end times — signed, exchanged (#24, #53)
- [ ] Constitution + scent-model cryptographic lock exchange (#23)
- [ ] Adversarial cheat-harness (each tamper class must be caught) 
- [ ] Full remote series with clean mutual audit · **GATE M6 demo recorded**

## 7. Stage 7 — Reporting, GUI, replay (PRD-7)
- [ ] `gui/live_view.py` — belief heatmap + own state + scent view + hint feed (LOCAL TRUTH ONLY, #8–9); `--no-gui`
- [ ] Turn banner: green `YOUR TURN` / gray `LOCKED`; input lockout while committed
- [ ] `gui/replay_view.py` — load log, step/play controls, live re-hash per step, `Verified OK` stamp / `TAMPERED` banner (#20)
- [ ] `report/artifacts.py` — declaration / config / log / result files, shared `game_uid`, jsonschema validation; result carries 4 repo links + per-sub-game commit hash + token totals
- [ ] Gmail OAuth per Appendix A (send-only scope, #30); mockable transport; draft/send modes
- [ ] Gatekeeper: quota manager + token bucket (30/2/5s/3/100 minimums) + DOS lock; 429 backoff (#28–29)
- [ ] League workflow: truthful counted-game declaration (#37–38), one-counted-per-opponent (#52), warm-up flag, result-agreement handshake, **auto dual reporting** (#35)
- [ ] Burst + infinite-loop drills · **GATE M7 demo recorded**

## 8. League play
- [ ] Warm-up interop game vs a reference-derived peer (uncounted)
- [ ] Partner-team #1: negotiate, lock, play 6 sub-games, audit, agree, both report, archive artifacts+config to repos
- [ ] Partner-team #2: same (pass gate = 2 counted matches vs different teams)
- [ ] Optional additional counted matches (≤10 total; diversity reward per new opponent)
- [ ] Evidence kit per match: heatmap screenshot, `Verified OK` screenshot, terminal output, Gmail id

## 9. Submission (book ch. 9/11 + Appendix C)
- [ ] Academic README in **both** repos — 5 mandatory components: Dec-POMDP formalization · FastMCP orchestration dilemmas · strategies implemented · RL learning curves (only if RL used) · **screenshots (belief heatmap + `Verified OK`)** — plus cross-link to the sister repo (#49)
- [ ] Both repos contain: README, `/config` (incl. every match's config), PRD files, PLAN, TODO (#50)
- [ ] Per-match commit hashes recorded in declarations + result files
- [ ] Verify no secrets in either repo **history**; `.gitignore` present (#39–40)
- [ ] Annotated tag on both repos: `git tag -a v1.0-submission -m "Final submission: Police-Thief P2P, group <code>"` + push (#41)
- [ ] Moodle: download form, fill (no field changes), save as PDF; **each member submits separately**; 8-char group code (#43–45)
- [ ] Self-grade = code quality only, not match results (#55)
- [ ] Final sweep of the book's pre-submission checklist (ch. 11.5) — every layer demoed end-to-end

## External inputs needed
| Item | Owner | Status |
|---|---|---|
| Partner availability + 2+ opposing teams | both | ☐ |
| 8-char group code | both | ☐ |
| ngrok/Localtonet account(s) | ops | ☐ |
| Google Cloud project + OAuth consent + `credentials.json` (send-only) | ops | ☐ |
| Decision: repo visibility (public vs private-shared) | both | ☐ |
| Optional: Ollama install / Anthropic key for banter | ops | ☐ |
