"""Stigmergic scent field: 5x5 radial emission, per-full-turn decay (book ch. 4).

The emission kernel is the book's exact figure-4 matrix (center tau = 0.9).
Values are clamped to [0, 0.9] and rounded to 4 decimals after every update
so both peers - and the post-game audit - recompute bit-identical fields.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .board import Cell

CENTER_INTENSITY = 0.9
DECAY_RATE = 0.10
FIELD_SIZE = 5
ROUND_DIGITS = 4
DUST_FLOOR = 0.001

#: Our reading of book ch. 4: the field is served *before* the step's own
#: emission (so the freshest cell an opponent ever sees is 0.81), values are
#: rounded to 4 dp and dust below 1e-3 snaps to zero.
BOOK_V1 = "book_v1"
#: The registered inter-team model (`multiplicative_book_v3`): decay and
#: emission in ONE expression, **no rounding**, no dust floor, and the field
#: served *after* the update - so the freshest cell reads 0.9. Negotiated per
#: opponent, because it is a different physics and not merely a different name.
REGISTERED_V3 = "registered_v3"
#: Team s82kma9e's `copthief-league-protocol` kit model, negotiated 2026-08-17.
#: Three differences from ours, and all three matter: the falloff is by
#: **Chebyshev** distance (flat square rings, not a graded radial matrix), decay
#: is **subtractive** (a flat -0.1, not a 0.9 multiplier), and emission
#: **max-merges** into the field instead of adding to it. Its freshest cell
#: therefore reads 0.8 - neither our 0.81 nor the registered model's 0.9.
SUBTRACTIVE_CHEBYSHEV_V1 = "subtractive_chebyshev_v1"
MODELS = (BOOK_V1, REGISTERED_V3, SUBTRACTIVE_CHEBYSHEV_V1)

#: Their kernel, by Chebyshev ring: centre, ring 1, ring 2. Flat within a ring,
#: which is the part that survives our peak-normalised belief update and so
#: actually changes where we search.
CHEBYSHEV_RINGS = (0.9, 0.6, 0.3)
SUBTRACTIVE_DECAY = 0.1
SUBTRACTIVE_ROUND_DIGITS = 3

# Book figure 4: radial falloff around the emitting agent (offsets -2..2).
EMISSION_KERNEL: list[list[float]] = [
    [0.04, 0.14, 0.20, 0.14, 0.04],
    [0.14, 0.42, 0.62, 0.42, 0.14],
    [0.20, 0.62, 0.90, 0.62, 0.20],
    [0.14, 0.42, 0.62, 0.42, 0.14],
    [0.04, 0.14, 0.20, 0.14, 0.04],
]


def scent_model_document(model: str = BOOK_V1) -> dict:
    """The emission+decay model with a numeric example - the pre-series lock payload
    (book rule #23: both teams hash-lock this before the first move)."""
    if model == SUBTRACTIVE_CHEBYSHEV_V1:
        # s82kma9e's canonical lock document, adopted byte-for-byte 2026-08-17.
        # The physics were already ours; the *schema* was not, and a lock only
        # locks if both sides hash the same object. This one is theirs verbatim -
        # do not tidy the field names, reorder anything, or "fix" the sparse
        # example into a matrix. Canonicalised it must hash to
        #   81ebee59640e80eae8ca9ee5f86abd26e7edf5cdbb27d15925cb6ee45ca6ddf4
        # which `tests/unit/test_scent_models.py` pins.
        half = FIELD_SIZE // 2
        emit_field = {
            f"{r},{c}": CHEBYSHEV_RINGS[max(abs(r - 3), abs(c - 3))]
            for r in range(3 - half, 3 + half + 1)
            for c in range(3 - half, 3 + half + 1)
        }
        after_one_decay = {
            k: round(v - SUBTRACTIVE_DECAY, SUBTRACTIVE_ROUND_DIGITS)
            for k, v in emit_field.items()
        }
        return {
            "example": {
                "after_one_decay": after_one_decay,
                "emit_center": [3, 3],
                "emit_field": emit_field,
                "note": "emit at the centre of a 7x7 board, then one decay",
            },
            "family": "scent_model",
            "name": SUBTRACTIVE_CHEBYSHEV_V1,
            "params": {
                "cadence": "per_full_turn",
                "clamp": [0.0, None],
                "decay": "subtractive",
                "decay_per_step": SUBTRACTIVE_DECAY,
                "distance": "chebyshev",
                "emit_intensity": CENTER_INTENSITY,
                "falloff": "linear",
                "falloff_step": "emit_intensity / (field_size // 2 + 1)",
                "field_size": FIELD_SIZE,
                "initial_field": "empty",
                "min_center_intensity": 0.5,
                "order": "deposit_then_decay",
                "receiver_side_decay": True,
                "rounding_decimals": SUBTRACTIVE_ROUND_DIGITS,
                "transmitted": True,
                "update": "tau' = round(max(0, tau - decay_per_step), 3)",
            },
        }
    if model == REGISTERED_V3:
        return {
            "model": "multiplicative_book_v3",
            # The spelling is pinned, not the algebra: the two forms are
            # algebraically equal and NOT equal in IEEE-754 doubles, and a model
            # that rounds nothing propagates that last bit forever.
            "formula": "tau(t+1) = clamp((1 - rho) * tau(t) + delta_tau, 0, 0.9)",
            "evaluation_order": "(1 - rho) * tau + delta",
            "rho": DECAY_RATE,
            "center_intensity": CENTER_INTENSITY,
            "kernel": EMISSION_KERNEL,
            "numeric_example": {"tau": 0.05, "delta": 0.04, "result": 0.085},
            "rounding_digits": None,
            "dust_floor": None,
            "serving": "each step serves the field AFTER that step's own update",
        }
    return {
        "formula": "tau(t+1) = min(0.9, max(0, (1 - rho) * tau(t) + delta_tau))",
        "rho": DECAY_RATE,
        "center_intensity": CENTER_INTENSITY,
        "kernel": EMISSION_KERNEL,
        "numeric_example": {"tau_0": 0.9, "after_one_decay": 0.81},
        "rounding_digits": ROUND_DIGITS,
        "serving": "each step serves the field BEFORE that step's emission",
    }


@dataclass
class ScentField:
    """One agent's own pheromone field; the opponent reads it, never the owner."""

    size: int
    grid: list[list[float]] = field(default_factory=list)
    model: str = BOOK_V1

    def __post_init__(self) -> None:
        if not self.grid:
            self.grid = [[0.0] * self.size for _ in range(self.size)]

    def advance(self, center: Cell) -> None:
        """Registered model: decay and emission in one pinned expression.

        No rounding and no dust floor - the registration's own words are "with
        NO rounding", and a floor would be another silent divergence.
        """
        half = FIELD_SIZE // 2
        for r in range(self.size):
            for c in range(self.size):
                dr, dc = r - center[0], c - center[1]
                delta = (EMISSION_KERNEL[dr + half][dc + half]
                         if abs(dr) <= half and abs(dc) <= half else 0.0)
                value = (1.0 - DECAY_RATE) * self.grid[r][c] + delta
                self.grid[r][c] = min(CENTER_INTENSITY, max(0.0, value))

    def serve_for_step(self, center: Cell) -> list[list[float]]:
        """Apply one own-step and return the field that step must serve.

        The *ordering* is the whole difference between the two models, and it
        has to be stated once: the live engine and the audit replay both call
        this, so a field we serve and a field the auditor recomputes cannot
        drift apart without the drift being in this one method.
        """
        if self.model == REGISTERED_V3:
            self.advance(center)
            return self.snapshot()
        if self.model == SUBTRACTIVE_CHEBYSHEV_V1:
            self.advance_subtractive(center)
            return self.snapshot()
        served = self.snapshot()
        self.emit(center)
        self.decay()
        return served

    def advance_subtractive(self, center: Cell) -> None:
        """s82kma9e's kit model: max-merge the ring kernel, then subtract.

        Their stated order, which their two golden fields pin down exactly:
        emit the kernel at the current cell, merge with ``max(existing,
        emitted)``, subtract 0.1 from *every* cell, clamp at zero, round to 3dp.
        Served after the update, so the freshest centre reads 0.8.

        The max-merge is why a revisited cell does not accumulate and why the
        current cell is always uniquely maximal - which is what keeps our
        belief argmax pointing at their true position under their physics.
        """
        half = FIELD_SIZE // 2
        for r in range(self.size):
            for c in range(self.size):
                dr, dc = abs(r - center[0]), abs(c - center[1])
                ring = max(dr, dc)
                emitted = CHEBYSHEV_RINGS[ring] if ring <= half else 0.0
                merged = max(self.grid[r][c], emitted)
                self.grid[r][c] = round(
                    max(0.0, merged - SUBTRACTIVE_DECAY), SUBTRACTIVE_ROUND_DIGITS
                )

    def emit(self, center: Cell) -> None:
        """Deposit the radial kernel around ``center``, clamped to the focal cap."""
        half = FIELD_SIZE // 2
        for dr in range(-half, half + 1):
            for dc in range(-half, half + 1):
                r, c = center[0] + dr, center[1] + dc
                if 0 <= r < self.size and 0 <= c < self.size:
                    add = EMISSION_KERNEL[dr + half][dc + half]
                    self.grid[r][c] = round(
                        min(CENTER_INTENSITY, self.grid[r][c] + add), ROUND_DIGITS
                    )

    def decay(self) -> None:
        """One full-turn decay tick: tau *= (1 - rho); dust below 1e-3 snaps to zero
        (a higher cutoff than the rounding step, so no value can get stuck)."""
        for r in range(self.size):
            for c in range(self.size):
                v = round(self.grid[r][c] * (1.0 - DECAY_RATE), ROUND_DIGITS)
                self.grid[r][c] = v if v >= 0.001 else 0.0

    def snapshot(self) -> list[list[float]]:
        return [row[:] for row in self.grid]

    def max_value(self) -> float:
        return max(max(row) for row in self.grid)
