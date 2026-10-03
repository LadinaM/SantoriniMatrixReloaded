import random

from santorinai.agents import Agent
from santorinai.core import GameState


class RandomAgent(Agent):
    """Picks any legal move at random."""

    def __init__(self, seed: int | None = None) -> None:
        self.rng = random.Random(seed)

    def select_action(self, state: GameState) -> int:
        return self.rng.choice(state.legal_actions())
