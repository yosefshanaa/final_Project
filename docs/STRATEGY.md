# STRATEGY — Move Policy & Tactics (the graded core)

Living document. The book makes the movement policy "the core of the grade" (Appendix F §5) and
mandates a **separate strategy module** plugged into the PeerRuntime *after* hint decode and
*before* commit pack (ch. 6.2). Requirements live in [`PRD.md`](PRD.md) §8 and
[`PRD/PRD-3`](PRD/PRD-3-strategy-blind.md)/[`PRD-4`](PRD/PRD-4-language-and-scent.md); design
rationale in [`PLAN.md`](PLAN.md) §5. This file tracks the **actual shipped doctrine per version**
and the evidence behind it — it also feeds the mandatory "strategies implemented" README section.

## 1. Binding constraints (from the book)
- Move decision is **always pure Python** — heuristics (Manhattan + Bayesian belief), our own
  algorithm, or optional RL; three equal paths (ch. 6.3). The LLM is banter-only (#25); LLM-driven
  tactics only by explicit mutual agreement — not our default.
- Plug-in contract: `[strategy] police_class` / `thief_class` = `package.module:Class`
  subclassing `BrainBase`, overriding `_pick_move` (+ `_decide_move` for the police barrier
  choice). Private per-peer choice — never negotiated, never shared with the opponent.
- Every brain output passes the rules validator; illegal choice ⇒ safe legal fallback (we can
  never technical-lose on our own brain bug).

## 2. Doctrine v1 (blind stage — full information via dev harness)
- **Police:** barrier-aware BFS pursuit, Manhattan tie-break; barrier placement only when it
  strictly shrinks the thief's escape set AND passes the flood-fill self-trap veto.
- **Thief:** maximize `distance(police) + λ·mobility` (open orthogonal neighbors), corner
  avoidance, barrier-aware pathing.
- Acceptance: v1 police captures a random walker ≤35 steps in ≥95% of 100 seeded games; v1 thief
  survives a random walker ≥95%.

## 3. Doctrine v2 (fog — belief-driven, the real game)
**Shared belief engine:** posterior grid = motion diffusion ⊕ scent likelihood (emission+decay
forward model; freshness ⇒ recency, τ≈0.81 ⇒ adjacent last turn) ⊕ hint likelihood × trust
coefficient `w`. Trust: corroboration ⇒ `w↑`; scent contradiction (book's "north claim / SE
scent" case) ⇒ `w↓` hard.

**Police:**
- Pursue belief argmax by barrier-aware BFS; tie-break by expected posterior-entropy reduction
  (information-gain patrol when belief is flat).
- Barrier doctrine (quota 14, each costs a full turn): early — none; mid — corridor pinching once
  belief mass ≥ threshold near an edge; end — pocket sealing with ≥2 quota reserved; kill shot —
  barrier **onto** a near-certain adjacent belief cell (barrier-capture). Invariant: flood-fill
  connectivity check before every placement.
- Deception: herding lies (announce false position pushing the thief toward sealed pockets);
  intent flag sealed in the commit.

**Thief:**
- Objective: `E_belief[dist(police,·)] + λ·mobility − μ·scent_risk`; never STAY twice
  (re-emission concentrates τ); increase distance from own scent centroid.
- Barriers are declared truth — reroute around forming pockets immediately.
- **Scent-consistent lying:** claim the region our *decayed* trail supports (3–4 turns stale) so
  the opponent's contradiction detector reinforces the lie; sprinkle true hints to keep their
  trust in us exploitable. Read the police's scent to infer patrol and steer orthogonally to the
  approach axis.

## 4. Evaluation protocol (regression-gated)
Seeded sim-runner tournaments in CI: v-next vs v-prev, vs random, vs the reference-repo greedy
brain; tracked metrics — police capture rate + mean capture step; thief survival rate; lie
detection/exploitation rates. Bounds asserted in CI; findings and parameter sweeps appended here
per version (this doubles as academic-README evidence).

## 5. Extensions backlog (excellence)
Particle-filter belief · bounded expectimax endgame · articulation-point barrier analysis ·
opponent-adaptive lie policy · auto-negotiation advisor — details in `PLAN.md` §5.5.

## 6. Version log
| Version | Change | Evidence |
|---|---|---|
| v2.0 (shipped, code 0.1.0) | Full fog doctrine of 3: belief pursuit + entropy tie-break, kill-shot/corner-seal barriers with flood-fill veto, mobility+scent-centroid evasion, scent-consistent lies. Claim-thresholds calibrated to scent-posterior scale (top-cell mass ≈0.15-0.3 ⇒ claim ≥0.12, kill-shot ≥0.35). Claim answers exploited both ways: denial ⇒ hard negative evidence for police; any claim ⇒ belief collapse to the claimant's cell for the thief. | 12-seed × 6 tournament (72 sub-games): **16 captures / 56 survivals**, totals police 600 : thief 640 — a genuine contest near the 18-capture break-even; all 144 audits `Verified OK` |

Next tuning candidates: police interception (target the diffused peak's *exit* rather than the
peak), earlier corridor building (barriers went unused in most games), thief endgame risk
model (edge-running worked; corner discipline can relax after step ~25).
