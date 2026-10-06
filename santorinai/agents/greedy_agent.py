import random

from santorinai.agents import Agent
from santorinai.core import BOARD_SIZE, PLACEMENT_OFFSET, GameState, cell_to_xy


def _is_central(cell: int) -> bool:
    x, y = cell_to_xy(cell)
    return 0 < x < BOARD_SIZE - 1 and 0 < y < BOARD_SIZE - 1


class GreedyAgent(Agent):
    """
    Looks one move ahead.

    It takes a win if there is one. Otherwise it avoids moves that would let
    the opponent win right away (for example by putting a dome on the
    opponent's tower), and among the rest it climbs as high as it can.

    Workers go into the middle 3x3 of the board, where they have the most room
    to move and are hardest to trap.
    """

    def __init__(self, seed: int | None = None) -> None:
        self.rng = random.Random(seed)

    def select_action(self, state: GameState) -> int:
        legal = state.legal_actions()
        if state.in_placement:
            central = [a for a in legal if _is_central(a - PLACEMENT_OFFSET)]
            return self.rng.choice(central or legal)

        for a in legal:
            if state.is_winning_action(a):
                return a

        me = state.to_play
        safe: list[int] = []
        for a in legal:
            nxt = state.child(a)
            if nxt.winner == me:  # opponent got stuck
                return a
            if not any(nxt.is_winning_action(r) for r in nxt.legal_actions()):
                safe.append(a)
        candidates = safe or legal

        # Height of the destination cell (the build never changes it).
        heights = {a: state.heights[state.move_destination(a)] for a in candidates}
        best = max(heights.values())
        return self.rng.choice([a for a, h in heights.items() if h == best])
