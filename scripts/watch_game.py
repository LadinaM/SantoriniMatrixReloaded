"""
Watch a single game between two agents in the terminal.

Run with:
    uv run scripts/watch_game.py                      # greedy vs random
    uv run scripts/watch_game.py random first_choice  # player 0 vs player 1
    uv run scripts/watch_game.py greedy greedy --seed 42
    uv run scripts/watch_game.py --help
"""

import argparse
from collections.abc import Callable

from santorinai.agents import (
    Agent,
    FirstChoiceAgent,
    GreedyAgent,
    MinimaxAgent,
    RandomAgent,
)
from santorinai.core import GameState
from santorinai.match import play_game

# Agent name on the command line -> factory taking a seed.
AGENTS: dict[str, Callable[[int | None], Agent]] = {
    "random": lambda seed: RandomAgent(seed),
    "first_choice": lambda seed: FirstChoiceAgent(),
    "greedy": lambda seed: GreedyAgent(seed),
    "minimax": lambda seed: MinimaxAgent(depth=2, seed=seed),
}


def show(state: GameState, action: int) -> None:
    print(f"action {action}\n{state}\n")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument(
        "player0",
        nargs="?",
        default="greedy",
        choices=AGENTS,
        help="agent for player 0 (moves first)",
    )
    parser.add_argument(
        "player1",
        nargs="?",
        default="random",
        choices=AGENTS,
        help="agent for player 1",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="seed for reproducible games (default: random)",
    )
    parser.add_argument(
        "--quiet", action="store_true", help="only print the result, not every move"
    )
    args = parser.parse_args()

    # Different seeds per player, so two random agents don't mirror each other.
    seed1 = None if args.seed is None else args.seed + 1
    agents = [AGENTS[args.player0](args.seed), AGENTS[args.player1](seed1)]

    result = play_game(agents, on_move=None if args.quiet else show)
    winner = args.player0 if result.winner == 0 else args.player1
    print(
        f"player {result.winner} ({winner}) wins ({result.reason}) "
        f"after {result.plies} plies"
    )


if __name__ == "__main__":
    main()
