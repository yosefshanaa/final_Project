"""Sealing and auditing in the reference dialect.

Split out of :mod:`.interop_codec` (§3.2 - split, never compress). One concern:
their commit formula and the audit built on it. Theirs hashes
``canonical(payload)|nonce``; ours puts the nonce inside the record, so neither
side can verify the other until one adopts the other's digest - which is what
this module is for.
"""

from __future__ import annotations

import logging
from typing import Any

from ..domain.crypto import reference_commit, verify_reference_record

log = logging.getLogger(__name__)


# The formula itself lives in domain.crypto, which owns every digest in the
# system; these helpers wrap it in the record envelope their audit expects.
def reference_records(sealed_records: list[dict[str, Any]],
                      live_hashes: list[str] | None = None) -> list[dict[str, Any]]:
    """Our sealed records -> their ``{payload, nonce, commit}`` audit format.

    Only the envelope changes: the payload is our record, so what we committed
    to is exactly what we played.

    ``commit`` is the commitment **we actually sent live**, not one re-derived
    here. Re-deriving is what makes a broken reveal look healthy: every record
    still verifies against its own recomputed hash, so the package passes any
    self-check, while binding to nothing the opponent holds. Recomputation is
    still done - as a comparison, so a divergence is a loud mismatch at the
    moment of sending instead of a silent 0-of-N in their audit.
    """
    hashes = list(live_hashes or [])
    out = []
    for index, sealed in enumerate(sealed_records):
        payload = {k: v for k, v in sealed.items() if k != "nonce"}
        derived = reference_commit(payload, sealed["nonce"])
        live = hashes[index] if index < len(hashes) else None
        if live is not None and live != derived:
            log.error("record %d: the sealed payload no longer hashes to the "
                      "commitment we sent (%s != %s) - revealing the live one",
                      index, derived[:16], live[:16])
        out.append({"payload": payload, "nonce": sealed["nonce"],
                    "commit": live or derived})
    return out


def reference_verify(record: dict[str, Any]) -> bool:
    """Re-hash one revealed ``{payload, nonce, commit}`` record on their terms."""
    return verify_reference_record(record)


def reference_audit(records: list[dict[str, Any]]) -> dict[str, Any]:
    """Verify a whole reference-format log; mirrors their ``audit_records`` report."""
    failed = [record["payload"].get("step", -1)
              for record in records if not reference_verify(record)]
    return {"passed": not failed, "verified_steps": len(records) - len(failed),
            "failed_steps": failed}
