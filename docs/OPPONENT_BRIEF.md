# OPPONENT BRIEF — what to send a new team, and what we must get back

One counted game per opponent, sealed forever once both reports are sent (book §9.2.1). So the
order is always: **exchange this brief → warm up uncounted (six sub-games) → play the counted one.**

Section 1 is copy-paste-ready to send. Section 2 is the reply we need. Section 3 is what we do
with their answers.

---

## 1. Message to send them

> **Team `ahk-yosi` — Cops & Robbers P2P match setup**
>
> Members: Yosef Shanaa (213314859), Ahmad Kaiss (325811255).
> Repos: police https://github.com/yosefshanaa/p2p-police-agent
> thief https://github.com/yosefshanaa/p2p-thief-agent
>
> **1. Constitution.** Attached is our `game.json`. The handshake exchanges `config_sha256` and
> refuses to start on any mismatch, so both sides must load a **byte-identical** file.
> Ours hashes to:
> `3835f6a137620d8d98ab3925b2d1ed397d2d20d23bb9ba857bcd104284aac443`
> It is the book's defaults: 7×7, thief (3,3), cop (0,0), top-left origin index 0, 35 moves,
> 14 barriers, scoring 20/5/5/10/2, τ₀=0.9 ρ=0.10 5×5, 6 sub-games. If you want any value
> changed, send yours back and we will adopt it (minimums may only rise) — but we must end up
> on one identical file.
>
> **2. Scent model lock** (book rule #23) — ours, for comparison before the first move:
> ```
> tau(t+1) = min(0.9, max(0, (1 - rho) * tau(t) + delta_tau))
> rho = 0.1   center_intensity = 0.9   rounding = 4 digits
> serving: each step serves the field BEFORE that step's own emission
> numeric example: tau_0 = 0.9  ->  after one decay = 0.81
> 5x5 emission kernel, centre 0.9:
>   [0.04, 0.14, 0.20, 0.14, 0.04]
>   [0.14, 0.42, 0.62, 0.42, 0.14]
>   [0.20, 0.62, 0.90, 0.62, 0.20]
>   [0.14, 0.42, 0.62, 0.42, 0.14]
>   [0.04, 0.14, 0.20, 0.14, 0.04]
> ```
> We are happy to share our `domain/scent.py` outright — the book encourages it.
>
> **3. Five questions we need answered before we can play.** These are the ones the book leaves
> to each pair of teams, and each one alone can void a whole series if we discover it mid-match:
>
> | # | Question | Our default |
> |---|---|---|
> | 1 | **Wire dialect** — which MCP tools does your peer expose? | We speak both: our own four-phase set (`handshake` / `receive_commit` / `receive_reveal` / `audit_exchange`, request-response) **and** the course reference repo's (`negotiate` / `receive_turn` / `submit_audit` / `receive_control`, push-and-inbox). Tell us which you run and we adapt — no change needed on your side. |
> | 2 | **Do roles alternate between sub-games?** | Either way. The reference repo alternates (natural role on odd sub-games, opposite on even); we default to a fixed role. Say which. |
> | 3 | **Do you re-negotiate before every sub-game, or handshake once per series?** | Either way — say which. The reference repo re-negotiates each sub-game. |
> | 4 | **Is a thief with no legal move captured?** (book §3.4 enclosure) | We play it as written — enclosed thief = capture. If your runtime has no enclosure rule, say so and we will switch it off, because otherwise our claim desynchronises the series. |
> | 5 | **How many counted games have you already played?** (rule #37) | We declare **0** at the time of writing. Both declarations go to the lecturer, so they must be truthful. |
>
> **4. First mover.** We propose **thief** (the book's default). Fine either way.
>
> **5. Endpoints.** Ours will be an ngrok HTTPS URL ending in `/mcp`, sent on match day —
> free-tier URLs rotate on every tunnel restart. Please send yours the same way. If a tunnel
> drops mid-series, restart it, send the new URL and re-handshake; silence past 180 s forfeits
> that sub-game as a technical loss.
>
> **6. Plan.** A **full six-sub-game warm-up first** (uncounted, no reports), then the counted
> match. Warm-ups are explicitly encouraged and cost nothing. We insist on six rather than one
> or two because three separate series-voiding defects only appear at a sub-game boundary — a
> short warm-up looks perfectly healthy and then the counted match dies at sub-game 2.
>
> Both teams email their own report to `rmisegal+uoh26finalgame@gmail.com` at the end; a missing
> report forfeits that side's points.

---

## 2. The reply we need (checklist)

- [ ] Their `/mcp` URL
- [ ] Dialect: native / reference / something else (we probe it too — see §3)
- [ ] Roles alternate: yes / no
- [ ] Re-handshake per sub-game: yes / no
- [ ] Enclosure claim (§3.4) honoured: yes / no
- [ ] Their prior counted-game count
- [ ] Their `game.json` (or "we accept yours")
- [ ] First mover agreed
- [ ] Warm-up time + counted-match time

## 3. What we do with it

```bash
uv run p2p-pursuit smoke https://their-url/mcp     # prints dialect=native|reference|unknown
```

The probe classifies their advertised tools, so the wire contract becomes a warm-up fact rather
than a mid-match surprise. **If the probe disagrees with what they told us, trust the probe** and
ask again — a wrong dialect means neither side can verify the other's commits at all.

Then set the four negotiated terms as environment variables (no config edit, no rebuild):

```fish
set -x P2P_OPPONENT_URL          https://their-url/mcp
set -x P2P_DIALECT               reference     # or native
set -x P2P_ALTERNATE_ROLES       true          # their answer to Q2
set -x P2P_HANDSHAKE_PER_SUB_GAME true         # their answer to Q3
set -x P2P_CLAIM_ENCLOSURE       false         # their answer to Q4
```

Warm-up (uncounted, six sub-games), then the counted match:

```bash
uv run p2p-pursuit peer --role thief --games 6
uv run p2p-pursuit peer --role thief --counted --prior-counted 0
```

Full operational detail — tunnels, the interop findings behind questions 2–4, scoring, and the
post-match archive step — is in `RUNBOOK.md` §1–4.
