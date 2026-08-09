"""The reference family's *mutual* result signature (their wire contract §7).

Both peers file their own result artifact, and the two must agree. Rather than
diff whole documents - which legitimately differ in clocks, token counts and
each side's private audit verdicts - the family hashes a **projection**: the
game id, five aggregate fields, and exactly five fields per sub-game row. Rows
may carry anything else without disturbing the digest, which is what lets two
independent implementations agree without sharing a schema.

Two traps live here, and both are theirs by specification rather than ours by
choice:

* **The encoding is not the commitment encoding.** Commitments use compact
  separators; this signature uses ``json.dumps`` *defaults* (``", "`` / ``": "``).
  Same document, different bytes, different hash - see :func:`~..domain.crypto.spaced_bytes`.
* **Scores and roles are keyed by group id, not by role.** Under role
  alternation a peer is police on some sub-games and thief on others, so a
  role-keyed total cannot be compared between two teams at all.
"""

from __future__ import annotations

from typing import Any

from ..domain.crypto import sha256_hex, spaced_bytes

__all__ = ["AGGREGATE_KEYS", "SUB_GAME_KEYS", "mutual_signature", "signature_document"]

#: The only per-row keys that reach the digest.
SUB_GAME_KEYS = ("sub_game_number", "roles", "result", "winner_group", "score")
#: The only aggregate keys that reach the digest.
AGGREGATE_KEYS = ("total_score", "sub_games_won", "ties", "winner_group", "series_tie")


def _project(row: Any, keys: tuple[str, ...]) -> dict[str, Any]:
    """Keep exactly ``keys``, absent ones as ``None``.

    A missing key must become an explicit ``None`` rather than vanish: two peers
    disagreeing about whether a field exists would otherwise hash differently
    while looking identical in a side-by-side read.
    """
    source = row if isinstance(row, dict) else {}
    return {key: source.get(key) for key in keys}


def signature_document(result: dict[str, Any]) -> dict[str, Any]:
    """Reduce a full result artifact to the three-part document that is signed."""
    rows = result.get("sub_games") or []
    return {
        "game_id": result.get("game_id"),
        "aggregate": _project(result.get("aggregate"), AGGREGATE_KEYS),
        "sub_games": [_project(row, SUB_GAME_KEYS) for row in rows],
    }


def mutual_signature(result: dict[str, Any]) -> str:
    """The hex digest both teams must produce from their own artifact."""
    return sha256_hex(spaced_bytes(signature_document(result)))
