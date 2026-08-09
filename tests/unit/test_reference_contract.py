"""Conformance to the reference family's published wire contract.

These pin the three places where a plausible-but-wrong value is indistinguishable
from a correct one until a real opponent disagrees: the commitment digest, the
deterministic ids, and the mutual result signature's *second* JSON encoding.
"""

from __future__ import annotations

import hashlib
import json
import uuid

from p2p_pursuit.domain.crypto import (
    canonical_bytes,
    reference_commit,
    sha256_raw,
    spaced_bytes,
)
from p2p_pursuit.domain.game_ids import reference_game_id, reference_game_uid
from p2p_pursuit.report.mutual_signature import mutual_signature, signature_document

TERMS = {"board_size": 7, "max_steps": 35, "setting": "7x7"}


def test_commit_matches_their_published_golden_vector() -> None:
    """Their §4: payload={"a":1}, nonce="ab"*16 -> sha256('{"a":1}|' + "ab"*16)."""
    nonce = "ab" * 16
    expected = hashlib.sha256(('{"a":1}|' + nonce).encode("utf-8")).hexdigest()
    assert reference_commit({"a": 1}, nonce) == expected


def test_commit_uses_compact_separators_not_spaced() -> None:
    """The trap: a spaced encoding hashes to a wrong-but-plausible hex string."""
    nonce = "cd" * 16
    spaced = hashlib.sha256(
        (json.dumps(TERMS, sort_keys=True) + "|" + nonce).encode("utf-8")).hexdigest()
    assert reference_commit(TERMS, nonce) != spaced


def test_game_id_is_lexicographic_and_symmetric() -> None:
    assert reference_game_id("uoh-sqak", "ahk-yosi") == "ahk-yosi-vs-uoh-sqak"
    assert reference_game_id("ahk-yosi", "uoh-sqak") == "ahk-yosi-vs-uoh-sqak"


def test_game_uid_is_deterministic_symmetric_and_terms_bound() -> None:
    a = reference_game_uid(TERMS, "ahk-yosi", "uoh-sqak")
    assert a == reference_game_uid(TERMS, "uoh-sqak", "ahk-yosi")  # order cannot matter
    assert uuid.UUID(a)  # a real UUID string, not a bare hex slice
    material = canonical_bytes(TERMS) + b"|ahk-yosi|uoh-sqak"
    assert a == str(uuid.UUID(bytes=sha256_raw(material)[:16]))
    assert a != reference_game_uid({**TERMS, "max_steps": 36}, "ahk-yosi", "uoh-sqak")


def test_signature_uses_default_separators() -> None:
    """Their §7 signs json.dumps DEFAULTS - the opposite of the commit encoding."""
    result = {"game_id": "a-vs-b", "aggregate": {}, "sub_games": []}
    doc = signature_document(result)
    assert mutual_signature(result) == hashlib.sha256(
        json.dumps(doc, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()
    assert spaced_bytes(doc) != canonical_bytes(doc)


def test_only_the_five_row_keys_reach_the_signature() -> None:
    """Rows may carry commits, clocks and tokens without moving the digest."""
    lean = {"game_id": "a-vs-b",
            "aggregate": {"total_score": {"a": 45}, "sub_games_won": {"a": 0},
                          "ties": 6, "winner_group": None, "series_tie": True},
            "sub_games": [{"sub_game_number": 1, "roles": {"a": "cop"},
                           "result": "survival", "winner_group": "b",
                           "score": {"a": 5, "b": 10}}]}
    noisy = json.loads(json.dumps(lean))
    noisy["sub_games"][0].update(github_commit="deadbeef", tokens=812, audit="Verified OK")
    noisy["generated_at"] = "2026-08-09T12:00:00Z"
    assert mutual_signature(noisy) == mutual_signature(lean)


def test_missing_row_key_is_explicit_null_not_absent() -> None:
    doc = signature_document({"game_id": "a-vs-b", "sub_games": [{"sub_game_number": 1}]})
    assert doc["sub_games"][0] == {"sub_game_number": 1, "roles": None, "result": None,
                                   "winner_group": None, "score": None}
