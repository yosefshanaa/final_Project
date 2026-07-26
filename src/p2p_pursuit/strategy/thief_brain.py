"""Thief doctrine (STRATEGY.md 3): belief-weighted evasion, scent-aware pathing,
scent-consistent lying.

Objective per move: maximize expected distance from the police belief cloud
plus mobility, stay off our own fresh trail (never STAY twice), and phrase
lies that our stale scent actually supports.
"""

from __future__ import annotations

from ..domain.board import Cell, target_of
from ..domain.brains_base import BrainBase, BrainView
from ..domain.hints import region_of
from ..domain.rules import Decision
from .pathing import bfs_distances, scent_centroid

W_MOBILITY = 0.6
W_CENTROID = 0.4
STAY_PENALTY = 1.2
CORNER_PENALTY = 0.5
STALE_LOW, STALE_HIGH = 0.25, 0.65


class ThiefBrain(BrainBase):
    def _pick_move(self, view: BrainView) -> Decision:
        centroid = scent_centroid(view.own_scent)

        def expected_police_distance(pos: Cell) -> float:
            dist = bfs_distances(view.board, pos)
            return sum(
                view.belief.grid[r][c] * dist.get((r, c), view.board.size * 2)
                for r in range(view.board.size)
                for c in range(view.board.size)
                if view.belief.grid[r][c] > 0
            )

        def score(move: str) -> float:
            pos = target_of(view.own_pos, move)
            s = expected_police_distance(pos)
            s += W_MOBILITY * len(view.board.open_neighbors(pos))
            if centroid is not None:
                s += W_CENTROID * (abs(pos[0] - centroid[0]) + abs(pos[1] - centroid[1]))
            if move == "STAY":
                s -= STAY_PENALTY  # re-emission concentrates our trail (doctrine: never camp)
            if view.step <= view.survival_threshold // 2:
                n = view.board.size
                edges = (pos[0] in (0, n - 1)) + (pos[1] in (0, n - 1))
                s -= CORNER_PENALTY * edges
            return s + view.rng.random() * 1e-3

        best = max(view.board.legal_moves(view.own_pos), key=score)
        return Decision(move=best)

    def hint_plan(self, view: BrainView, decision: Decision) -> tuple[str, str]:
        """Scent-consistent lie: claim the stale region our decayed trail supports."""
        if view.rng.random() < 0.15:
            return region_of(view.own_pos, view.board.size), "truth"
        stale = [
            (r, c)
            for r, row in enumerate(view.own_scent)
            for c, v in enumerate(row)
            if STALE_LOW <= v <= STALE_HIGH
        ]
        if stale:
            own = view.own_pos
            far = max(stale, key=lambda p: abs(p[0] - own[0]) + abs(p[1] - own[1]))
            return region_of(far, view.board.size), "lie"
        from .police_brain import OPPOSITE

        return OPPOSITE.get(region_of(view.own_pos, view.board.size), "north"), "lie"
