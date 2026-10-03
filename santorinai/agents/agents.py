"""
What an agent looks like.

Anything with a ``select_action(state)`` method that returns a legal move is
an agent: our agents in ``santorinai.agents``, a trained policy, MCTS, and
later a human clicking in the GUI. That's why any of them can play against
any other.
"""

from typing import Protocol

from santorinai.core import GameState


class Agent(Protocol):
    """Picks a move for the player whose turn it is."""

    def select_action(self, state: GameState) -> int: ...
