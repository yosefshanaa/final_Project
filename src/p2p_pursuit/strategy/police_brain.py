"""Police doctrine (STRATEGY.md 3): belief pursuit, barrier phases, herding lies.

Kill shot: barrier onto a near-certain adjacent belief cell captures outright.
Corner seal: pinch the escape ring when the belief mass is cornered nearby.
Every placement passes the flood-fill self-trap veto; two barriers stay in
reserve for the endgame.
"""

from __future__ import annotations

from ..domain.board import Cell
from ..domain.brains_base import BrainBase, BrainView
from ..domain.hints import region_of
from ..domain.rules import Decision
from .pathing import bfs_distances, still_connected

# Under scent evidence the posterior spreads over ~5-8 live cells, so the
# top-cell mass rarely exceeds ~0.3; thresholds are calibrated to that scale
# (a claim/kill-shot is a repeatable probabilistic play, not a certainty).
KILL_SHOT_BELIEF = 0.35
SEAL_BELIEF = 0.25
ENDGAME_RESERVE = 2

OPPOSITE = {"north": "south", "south": "north", "east": "west", "west": "east",
            "northeast": "southwest", "southwest": "northeast",
            "northwest": "southeast", "southeast": "northwest", "center": "north"}


class PoliceBrain(BrainBase):
    claim_threshold = 0.12

    def _decide_move(self, view: BrainView) -> Decision:
        target = view.belief.argmax()
        b_max = view.belief.grid[target[0]][target[1]]
        barrier = self._barrier_play(view, target, b_max)
        if barrier is not None:
            return Decision(move="STAY", barrier=barrier)
        return self._pursue(view, target)

    def _barrier_play(self, view: BrainView, target: Cell, b_max: float) -> Cell | None:
        left = view.barrier_quota - view.barriers_used
        if left <= 0:
            return None
        adjacent_open = [c for c in view.board.neighbors4(view.own_pos) if view.board.is_open(c)]
        # Kill shot: near-certain belief on a cell we can bar right now (captures, #46).
        if b_max >= KILL_SHOT_BELIEF and target in adjacent_open:
            return target
        # Corner seal: cornered belief mass close by - pinch its exit, keep a reserve.
        if left <= ENDGAME_RESERVE or b_max < SEAL_BELIEF:
            return None
        dist = bfs_distances(view.board, view.own_pos)
        if dist.get(target, 99) > 2 or not self._is_cornered(view, target):
            return None
        for cell in adjacent_open:
            if target in view.board.neighbors4(cell) and cell != target and \
                    still_connected(view.board, cell, view.own_pos, target):
                return cell
        return None

    def _is_cornered(self, view: BrainView, cell: Cell) -> bool:
        n = view.board.size
        edges = (cell[0] in (0, n - 1)) + (cell[1] in (0, n - 1))
        return edges >= 1 and len(view.board.open_neighbors(cell)) <= 2

    def _pursue(self, view: BrainView, target: Cell) -> Decision:
        dist_from_target = bfs_distances(view.board, target)

        def score(move: str) -> tuple:
            from ..domain.board import target_of

            pos = target_of(view.own_pos, move)
            d = dist_from_target.get(pos, 9999)
            near = view.belief.mass_in({
                (pos[0] + dr, pos[1] + dc) for dr in (-2, -1, 0, 1, 2) for dc in (-2, -1, 0, 1, 2)
            })
            return (d, -near, view.rng.random())

        best = min(view.board.legal_moves(view.own_pos), key=score)
        return Decision(move=best)

    def hint_plan(self, view: BrainView, decision: Decision) -> tuple[str, str]:
        """Herding lie: claim to close in from the opposite side of our true region."""
        if view.rng.random() < 0.2:
            return region_of(view.own_pos, view.board.size), "truth"
        true_region = region_of(view.own_pos, view.board.size)
        return OPPOSITE.get(true_region, "north"), "lie"
