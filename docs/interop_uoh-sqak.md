# Interop contract — vs. team `uoh-sqak` (CipherChase), operator Salah

Their brief received 2026-08-09. This file is (1) the reply to send, (2) the negotiated contract,
(3) the gap list their brief exposed in our stack. Companion to `RUNBOOK.md` §3b.

Their dialect is the **reference family** we already adapt to (`negotiate` / `receive_turn` /
`submit_audit` / `receive_control`, push-and-inbox, `{"ok": true}`) — but they are **not** the
unmodified reference peer, and four of their facts differ from it in ways that matter.

---

## 1. Reply to send (copy-paste)

> **Team `ahk-yosi` → `uoh-sqak`. Answering your §0, in order.**
>
> Thank you for the brief — it saved us the reverse-engineering, and three of the things you
> flagged were real in our stack. Answers first, then what we found.
>
> **1. group_id** — `ahk-yosi`
>
> **2. public URL** — **one** endpoint, sent on match day (ngrok HTTPS, `/mcp` suffix, free-tier
> URLs rotate on restart). Your §6: our cop and thief are **one service, not two** — a single
> role-configurable peer that alternates its own role across sub-games. So one address is correct
> for the whole series and there is no wrong-service failure mode on our side.
>
> **3. repos** —
> `{"cop": "https://github.com/yosefshanaa/p2p-police-agent",`
> ` "thief": "https://github.com/yosefshanaa/p2p-thief-agent"}`
>
> **4. counted_games_played** — **0**. This will be our first counted series.
>
> **5. Scent model** — **`multiplicative_book_v1`**, and here is ours in full so you can confirm
> it is the same physics and not merely the same name:
> ```
> deposit:  additive 5x5 book figure-4 kernel at the thief's cell, clamped to 0.9
>           [0.04, 0.14, 0.20, 0.14, 0.04]
>           [0.14, 0.42, 0.62, 0.42, 0.14]
>           [0.20, 0.62, 0.90, 0.62, 0.20]
>           [0.14, 0.42, 0.62, 0.42, 0.14]
>           [0.04, 0.14, 0.20, 0.14, 0.04]
> decay:    tau <- tau * (1 - 0.1)          multiplicative, every full turn
> clamp:    tau in [0, 0.9]
> rounding: 4 decimal places after every update
> floor:    values below 1e-3 snap to 0.0
> order:    each step serves the field BEFORE that step's own emission
>           (so the freshest cell an opponent ever sees is 0.81, not 0.9)
> ```
> **Please confirm three things your §5 does not pin down**, because each one silently changes
> the numbers on the wire: your **rounding digits** (ours 4 — you quote 3 dp for the *subtractive*
> model but not for this one), your **dust floor**, and your **serve-before-or-after-emit order**.
> A shared model name with a different rounding rule is exactly the silent disagreement you warn
> about. We are happy to adopt your values on all three; we just need them written down.
>
> **6. Terms** — we adopt your §2 block as-is, with **one** item to settle:
>
> | Term | Yours | Ours | Resolution |
> |---|---|---|---|
> | `min_center_intensity` | 0.001 | 0.5 | **We adopt 0.001.** Ours was a validation floor, yours is the dust floor — and 0.001 is exactly our own cutoff, so this is the same number under a better name. |
> | `axis_origin_corner` | `top_left` | `top-left` | **We adopt `top_left`.** Spelling only, same semantics. |
> | `setting` | `7x7` | `New York` | **We adopt `7x7`.** Ours only flavours trash-talk landmarks. |
> | `hint_max_words` | 30 | 15 | **Please consider 15.** The rules book caps a hint at 15 words, so 30 lets a conforming peer emit a non-conforming hint. We will play 30 if you prefer — we would simply hold our own hints to 15 regardless — but 15 is the safer number for both filed logs. Your call; say the word and we set it. |
>
> Everything else in your terms block is already our value exactly: board 7, smell grid 5, decay
> 0.1, emit 0.9, max_steps 35, barriers_max 14, thief_start [3,3], cop_start [0,0],
> axis_start_index 0, num_games 6.
>
> **7. A time to bind** — *(operator to fill: propose a friendly slot)*. Friendly first, six
> sub-games, agreed.
>
> ---
>
> **Your §8, both agreed in writing:**
>
> **(a) `capture_claim` is a question, not an assertion.** Agreed, and it is already our reading —
> our cop claims only when its own belief map puts you on its cell, which as you say is strictly
> more conservative than the reference implementation's unconditional claim. `{"caught": false}`
> is an ordinary answer and never grounds for forfeit, in either direction.
>
> **(b) `game_length` = the thief's count = 35**, per-side numbers labelled as per-side. Agreed.
>
> **Your §3 enclosure — one thing to settle, because our two designs collide.** You implement
> rules 46/47 with the **thief announcing** (`claim_response {"claim": [own cell], "caught": true}`),
> since only the thief can observe it. Our cop *also* plays for enclosure and claims it itself —
> we built that because the course reference peer has no enclosure rule at all and simply plays on
> after being sealed in, which cost us a sub-game live. Against you that defence is unnecessary and
> the two mechanisms would double-report the same event. **We propose: your rule, not ours** — the
> enclosed thief announces, the cop stays silent, and we switch our cop-side claim off for this
> series. Confirm and it is settled.
>
> **Three things we found in our own stack while reading your brief** — all being fixed before the
> friendly, listed because two of them would have put wrong data in *your* filed report:
>
> 1. **We were not sending `counted_games_played` in our identity**, and we were reading yours
>    under our own field name (`prior_counted_games`). So your report would have carried an
>    invented count for us and ours for you — precisely the "never invent one on the other team's
>    behalf" failure. Both directions fixed; we will use your spelling.
> 2. **We were not sealing a step-0 `system_spec` record**, so the `github_commit` you file per
>    sub-game for us would have read `unknown` — your ninth defect, arriving from our side.
> 3. **Our `game_id` derivation is not yours.** Ours appends a timestamp and was built before we
>    knew your group_id; yours is `"<min-gid>-vs-<max-gid>"`. Since `game_id` is the first key of
>    the mutual signature, ours could never have matched. **We adopt your derivation verbatim**,
>    including the `game_uid` UUID over `canonical(terms)|lo|hi`.
>
> **On the mutual signature (§7)** — thank you for spelling out the default-vs-compact separator
> trap; we would have walked straight into it. We are implementing your signature exactly as
> written and will diff against your kit before we bind. **We do not appear to have received the
> attachment** — the artifact set, the manifest, and the one-page wire contract. Could you resend?
> We would rather diff against your real files than against our reading of your prose.
>
> Two questions of our own, both cheap now and expensive later:
>
> - **`win_claim` type strings.** You document `{"type": "survival"}`. Does your handler compare
>   that string, or does any `win_claim` end the sub-game? We ask because our internal kind is
>   `survival_claim` and we would rather normalise to your exact spelling than find out at step 35.
> - **Audit timing at the sub-game boundary.** You re-negotiate immediately and wait ~60 s for the
>   agreement. Our audit exchange sits in front of our re-handshake, so we bound that wait to 20 s
>   for exactly this reason. If your bind window is tighter than 60 s, tell us the real number.
>
> — agent, team `ahk-yosi`

---

## 2. Negotiated contract (fill in as they confirm)

| Item | Value | Confirmed? |
|---|---|---|
| Dialect | reference family (`P2P_DIALECT=reference`) | their brief §1 ✔ |
| Roles alternate | yes (`P2P_ALTERNATE_ROLES=true`) | their §9.2 ✔ |
| Handshake per sub-game | yes (`P2P_HANDSHAKE_PER_SUB_GAME=true`) | their §2 ✔ |
| Enclosure | thief announces; our cop silent (`P2P_CLAIM_ENCLOSURE=false`) | proposed, awaiting |
| Scent model | `multiplicative_book_v1` | name ✔ / rounding, floor, order **open** |
| `hint_max_words` | 15 or 30 | **open** |
| `min_center_intensity` | 0.001 (adopt theirs) | ours to adopt ✔ |
| `axis_origin_corner` | `top_left` (adopt theirs) | ours to adopt ✔ |
| `setting` | `7x7` (adopt theirs) | ours to adopt ✔ |
| First mover | thief | both ✔ |
| Their counted count | *(awaiting)* | open |
| Their URL(s) | *(awaiting)* | open |
| Interop kit | **not received** — resend requested | open |

## 2b. Match day — the whole configuration, no file edits

Every negotiated term is an environment variable, so the committed constitution is never touched
and nothing can ride into the next opponent's match. `hint_max_words` below assumes they hold at
30; drop the line if they accept 15.

```fish
set -x P2P_OPPONENT_URL           https://THEIR-TUNNEL/mcp   # from them, match day
set -x P2P_DIALECT                reference
set -x P2P_ALTERNATE_ROLES        true
set -x P2P_HANDSHAKE_PER_SUB_GAME true
set -x P2P_CLAIM_ENCLOSURE        false        # their thief announces it, not our cop
set -x P2P_MAP_AREA               7x7          # their `setting`
set -x P2P_AXIS_ORIGIN_CORNER     top_left
set -x P2P_MIN_CENTER_INTENSITY   0.001
set -x P2P_HINT_MAX_WORDS         30           # only if they hold at 30

uv run p2p-pursuit smoke $P2P_OPPONENT_URL          # expect dialect=reference
uv run p2p-pursuit peer --role thief --games 6      # FRIENDLY, uncounted
uv run p2p-pursuit peer --role thief --counted --prior-counted 0   # only after the friendly
```

Expose our side first: `ngrok http 8801`, then send them the `https://…/mcp` URL.

## 3. Gap list (what their brief exposed in our stack)

Severity: **A** blocks the handshake, **B** corrupts a filed artifact, **C** blocks their §9 step 3.

| # | Sev | Gap | Fix | Status |
|---|---|---|---|---|
| 1 | A | `min_center_intensity` / `hint_max_words` / `axis_origin_corner` / `setting` differ; their `verify_peer` compares terms by exact dict equality | env-var overrides for the negotiable terms, following the existing `P2P_MAP_AREA` precedent — never edit the committed constitution | **done** (`NEGOTIABLE_TERM_VARS`) |
| 2 | B | identity omits `counted_games_played`; we read theirs as `prior_counted_games` | send and read their spelling, both directions | **done** |
| 3 | B | no step-0 `system_spec` record ⇒ our `github_commit` files as `unknown` on their side | seal one into the audit package in the reference dialect | **done** |
| 4 | C | `game_id` has a timestamp and `"opponent"` placeholder; `game_uid` is random | adopt their derivation: `"<min-gid>-vs-<max-gid>"`, uid = UUID over `canonical(terms)\|lo\|hi` | functions built + tested; **not yet bound into the runtime** |
| 5 | C | mutual signature not implemented at all (5 keys per row, **default** `json.dumps` separators) | `report/mutual_signature.py` | projection + digest built and tested; **result artifact not yet reshaped** (`aggregate`, `links`, `diversity_reward_applied`, `games_played_including_this`) |
| 6 | D | our enclosure is cop-claimed; theirs is thief-announced via `claim_response` | `claim_enclosure=false`; map our thief's forced confession onto their `claim_response {caught: true}` + "You got me." | **done** |
| 7 | D | our `win_claim` carries `{"type": "survival_claim"}`; they document `{"type": "survival"}` | normalise on the reference path (question also asked of them) | **done** |
| 8 | D | agreement omits `sub_game_number`, which they use to detect index drift | add it outside `terms`, so the signature is undisturbed | **done** |

**4 and 5 are deliberately unbound.** Their aggregate is keyed by *group id*, ours by *role* —
which under role alternation are not the same shape — and they told us to diff against their
interop kit before binding. That kit did not arrive with the brief, so binding now would mean
implementing our reading of their prose and calling it agreement. The primitives are built,
match their published golden vector, and are ready to wire the moment the kit lands.

**Every change is gated to the reference/interop path — the native dialect stays byte-identical,
because that is the contract our two published repos and all 238 tests are built on.**
