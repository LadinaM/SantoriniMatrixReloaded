"""
Round-robin tournament between the baseline agents.

Run with:  uv run scripts/compare_agents.py

Prints a table with the win rate of each row agent against each column agent.
Seats are swapped every game, so the first-player advantage cancels out.
"""

from santorinai.agents import FirstChoiceAgent, GreedyAgent, MinimaxAgent, RandomAgent
from santorinai.match import format_round_robin, round_robin

NUM_GAMES = 200

agents = {
    "Random": RandomAgent(seed=0),
    "FirstChoice": FirstChoiceAgent(),
    "Greedy": GreedyAgent(seed=0),
    "Minimax": MinimaxAgent(depth=2, seed=42),
}

print(format_round_robin(round_robin(agents, NUM_GAMES)))
