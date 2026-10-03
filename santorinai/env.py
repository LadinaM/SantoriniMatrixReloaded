"""
Gymnasium environment for training one agent against an opponent.

The opponent is part of the environment: after every move of the agent it
answers straight away, and the agent gets the position after that. Rewards
are +1 for a win, -1 for a loss and 0 otherwise. The background (random
seats, masking, why there are no in-between rewards) is in
documentation/engine_core.md under "The training environment".
"""

import random
from typing import Any, Literal

import gymnasium as gym
import numpy as np
from gymnasium import spaces

from santorinai.agents import Agent, RandomAgent
from santorinai.core import (
    BOARD_SIZE,
    NUM_ACTIONS,
    NUM_OBS_PLANES,
    GameState,
    StartMode,
)


class SantoriniEnv(gym.Env):
    # Gymnasium's own convention for declaring render modes.
    metadata = {"render_modes": ["ansi"]}  # noqa: RUF012

    def __init__(
        self,
        opponent: Agent | None = None,
        agent_player: int | None = None,
        start: StartMode = StartMode.placement,
        illegal_action: Literal["lose", "raise"] = "lose",
        render_mode: str | None = None,
    ) -> None:
        """
        Args:
            opponent: who the agent plays against (a ``RandomAgent`` if not
                given). For self-play, pass a frozen copy of the policy.
            agent_player: always seat the agent as player 0 or 1. By default
                it gets a random seat every episode.
            start: how episodes start, see ``GameState.new_game``. The default
                includes placement, so the agent learns that too.
            illegal_action: ``"lose"`` ends the episode with -1 if the agent
                picks an illegal move; ``"raise"`` throws an error instead,
                which helps when debugging action masking.
            render_mode: ``None`` or ``"ansi"`` (the board as text).
        """
        super().__init__()
        self.opponent: Agent = opponent if opponent is not None else RandomAgent()
        self.fixed_agent_player = agent_player
        self.start: StartMode = start
        self.illegal_action = illegal_action
        self.render_mode = render_mode

        self.observation_space = spaces.Box(
            0.0, 1.0, (NUM_OBS_PLANES, BOARD_SIZE, BOARD_SIZE), dtype=np.float32
        )
        self.action_space = spaces.Discrete(NUM_ACTIONS)

        self._rng = random.Random()
        self.agent_player = 0
        self.state = GameState.new_game()

    def reset(
        self, *, seed: int | None = None, options: dict[str, Any] | None = None
    ) -> tuple[np.ndarray, dict[str, Any]]:
        super().reset(seed=seed)
        if seed is not None:
            self._rng.seed(seed)
        self.agent_player = (
            self.fixed_agent_player
            if self.fixed_agent_player is not None
            else self._rng.randint(0, 1)
        )
        self.state = GameState.new_game(self.start, self._rng)
        # If the agent plays second, the opponent opens.
        if self.state.to_play != self.agent_player:
            self.state.step(self.opponent.select_action(self.state))
        return self.state.observation(), self._info()

    def step(self, action: int) -> tuple[np.ndarray, float, bool, bool, dict[str, Any]]:
        action = int(action)
        if action not in self.state.legal_actions():
            if self.illegal_action == "raise":
                raise ValueError(f"illegal action {action}")
            info = self._info()
            info["illegal_action"] = True
            return self.state.observation(), -1.0, True, False, info

        self.state.step(action, validate=False)
        if not self.state.is_terminal:
            self.state.step(self.opponent.select_action(self.state))

        # Games always end (<= 105 plies), so no truncation is needed.
        return (
            self.state.observation(),
            self.state.reward(self.agent_player),
            self.state.is_terminal,
            False,
            self._info(),
        )

    def action_masks(self) -> np.ndarray:
        """Which moves are legal right now (the name MaskablePPO looks for)."""
        return self.state.action_mask()

    def render(self) -> str | None:
        if self.render_mode == "ansi":
            return str(self.state)
        return None

    def _info(self) -> dict[str, Any]:
        return {
            "action_mask": self.state.action_mask(),
            "agent_player": self.agent_player,
            "winner": self.state.winner,
        }
