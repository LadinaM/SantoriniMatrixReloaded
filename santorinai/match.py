"""
Let agents play against each other and count who wins.

``play_match`` swaps seats every game, because the player who moves first
has an advantage and we want to compare the agents, not the seats.
"""

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from enum import StrEnum

from santorinai.agents import Agent
from santorinai.core import GameState, StartMode


class EndReason(StrEnum):
    climbed = "climbed"
    opponent_stuck = "opponent_stuck"
    illegal_action = "illegal_action"


@dataclass
class GameResult:
    winner: int
    reason: EndReason
    plies: int
    actions: list[int]


@dataclass
class MatchResult:
    """Results of ``play_match``, counted from agent A's side."""

    wins_a: int = 0
    wins_b: int = 0
    total_plies: int = 0
    reasons: dict[EndReason, int] = field(default_factory=dict)

    @property
    def num_games(self) -> int:
        return self.wins_a + self.wins_b

    @property
    def win_rate_a(self) -> float:
        return self.wins_a / self.num_games if self.num_games else 0.0

    @property
    def mean_plies(self) -> float:
        return self.total_plies / self.num_games if self.num_games else 0.0


def play_game(
    agents: Sequence[Agent],
    state: GameState | None = None,
    on_move: Callable[[GameState, int], None] | None = None,
) -> GameResult:
    """
    Play one game to the end.

    Args:
        agents: ``agents[0]`` plays as player 0 (moves first), ``agents[1]``
            as player 1.
        state: where to start; a new game with placement by default.
        on_move: called with ``(state, action)`` after every move, e.g. to
            print the board.

    An agent that returns an illegal move loses the game instead of crashing
    the whole run.
    """
    state = state if state is not None else GameState.new_game()
    actions: list[int] = []
    while not state.is_terminal:
        player = state.to_play
        action = agents[player].select_action(state)
        if action not in state.legal_actions():
            return GameResult(1 - player, EndReason.illegal_action, state.ply, actions)
        climbed = state.is_winning_action(action)
        state.step(action, validate=False)
        actions.append(action)
        if on_move is not None:
            on_move(state, action)
        if state.is_terminal:
            reason: EndReason = (
                EndReason.climbed if climbed else EndReason.opponent_stuck
            )
            assert state.winner is not None
            return GameResult(state.winner, reason, state.ply, actions)
    raise ValueError("the starting position is already terminal")


def play_match(
    agent_a: Agent,
    agent_b: Agent,
    num_games: int,
    start: StartMode = StartMode.placement,
    swap_seats: bool = True,
) -> MatchResult:
    """
    Play ``num_games`` games between two agents.

    By default agent A moves first in every other game, so neither agent
    profits from always going first.
    """
    result = MatchResult()
    for i in range(num_games):
        a_seat = i % 2 if swap_seats else 0
        agents = (agent_a, agent_b) if a_seat == 0 else (agent_b, agent_a)
        game = play_game(agents, GameState.new_game(start))
        if game.winner == a_seat:
            result.wins_a += 1
        else:
            result.wins_b += 1
        result.total_plies += game.plies
        result.reasons[game.reason] = result.reasons.get(game.reason, 0) + 1
    return result


def round_robin(
    agents: Mapping[str, Agent], num_games: int
) -> dict[tuple[str, str], MatchResult]:
    """Let every agent play a match against every other agent."""
    names = list(agents)
    return {
        (a, b): play_match(agents[a], agents[b], num_games)
        for i, a in enumerate(names)
        for b in names[i + 1 :]
    }


def format_round_robin(results: Mapping[tuple[str, str], MatchResult]) -> str:
    """Markdown table of how often the row agent beat the column agent."""
    names = sorted({n for pair in results for n in pair})
    rate: dict[tuple[str, str], float] = {}
    for (a, b), r in results.items():
        rate[a, b] = r.win_rate_a
        rate[b, a] = 1.0 - r.win_rate_a
    lines = [
        "| | " + " | ".join(names) + " |",
        "|---" * (len(names) + 1) + "|",
    ]
    for a in names:
        cells = ["-" if a == b else f"{rate[a, b]:.0%}" for b in names]
        lines.append(f"| {a} | " + " | ".join(cells) + " |")
    return "\n".join(lines)
