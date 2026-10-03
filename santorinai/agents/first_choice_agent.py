from santorinai.agents import Agent
from santorinai.core import GameState


class FirstChoiceAgent(Agent):
    """
    Always plays the first legal move.

    Sounds silly, but it's tougher than it looks: by always moving the same
    way it tends to build itself a staircase. A good check that an agent has
    learned more than just avoiding random blunders.
    """

    def select_action(self, state: GameState) -> int:
        return state.legal_actions()[0]
