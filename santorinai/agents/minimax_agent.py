"""
Plain minimax without alpha-beta pruning.

The agent looks a few turns ahead, assumes the opponent always picks its best
reply, and scores the positions at the end with ``evaluate``. How it works,
how it scores positions and how slow it gets is written up in
documentation/minimax.md.
"""

import math
import random

from santorinai.agents import Agent
from santorinai.core import NEIGHBORS, UNPLACED, GameState

# A win is worth more than any heuristic score can reach.
WIN_SCORE = 1000.0

# Evaluation weights, see ``evaluate``.
HEIGHT_WEIGHT = 3.0
CLIMB_WEIGHT = 1.0
CENTER_WEIGHT = 0.25


def evaluate(state: GameState, player: int) -> float:
    """
    How good a running game looks for ``player``.

    Each worker earns points for its height, for steps it could climb next
    turn and for being near the middle; we add up our workers and subtract
    the opponent's. Workers that aren't placed yet don't count.
    """
    heights = state.heights
    workers = state.workers
    score = 0.0
    for owner, sign in ((player, 1.0), (1 - player, -1.0)):
        for cell in workers[owner * 2 : owner * 2 + 2]:
            if cell == UNPLACED:
                continue
            height = heights[cell]
            neighbors = [n for n in NEIGHBORS[cell] if n >= 0]
            climbs = sum(
                1 for n in neighbors if heights[n] == height + 1 and n not in workers
            )
            score += sign * (
                HEIGHT_WEIGHT * height
                + CLIMB_WEIGHT * climbs
                + CENTER_WEIGHT * len(neighbors)
            )
    return score


class MinimaxAgent(Agent):
    def __init__(self, depth: int = 2, seed: int | None = None) -> None:
        """
        Args:
            depth: how many turns to look ahead (1 = only my move, 2 = my move
                and the opponent's reply, ...). Every extra turn makes it about
                50 times slower.
            seed: used to pick randomly between equally good moves.
        """
        if depth < 1:
            raise ValueError("depth must be at least 1")
        self.depth = depth
        self.rng = random.Random(seed)
        self.nodes_searched = 0  # positions visited during the last move

    def select_action(self, state: GameState) -> int:
        me = state.to_play
        self.nodes_searched = 0
        best_value = -math.inf
        best_actions: list[int] = []
        for action in state.legal_actions():
            value = self._minimax(_child(state, action), self.depth - 1, me)
            if value > best_value:
                best_value, best_actions = value, [action]
            elif value == best_value:
                best_actions.append(action)
        return self.rng.choice(best_actions)

    def _minimax(self, state: GameState, depth: int, me: int) -> float:
        """Value of ``state`` for ``me``, looking ``depth`` more turns ahead."""
        self.nodes_searched += 1

        if state.is_terminal:
            # The remaining depth makes earlier wins worth a bit more.
            win = WIN_SCORE + depth
            return win if state.winner == me else -win
        if depth == 0:
            return evaluate(state, me)

        values = [
            self._minimax(_child(state, action), depth - 1, me)
            for action in state.legal_actions()
        ]
        # On my turn I take the best value, on the opponent's turn they leave
        # me the worst one.
        return max(values) if state.to_play == me else min(values)


def _child(state: GameState, action: int) -> GameState:
    """``state.child(action)`` without the legality check (it's a legal move anyway)."""
    child = state.clone()
    child.step(action, validate=False)
    return child
