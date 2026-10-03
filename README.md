![Santorini Matrix Reloaded](./images/headban.png)

# Santorini Matrix Reloaded

We're teaching a computer to play the board game Santorini on its own, using
reinforcement learning (PPO and MCTS). This repository contains the game
engine, a few simple opponents, a training environment and tools to let
agents play against each other.

The project started as a fork of
[SantorinAI](https://github.com/Tomansion/SantorinAI). Since then we've
rewritten the engine, the agents and the training setup with learning in
mind.

## Getting started

We use [uv](https://docs.astral.sh/uv/) to manage Python and the
dependencies.

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh   # only if you don't have uv yet
git clone https://github.com/LadinaM/SantoriniMatrixReloaded.git
cd SantoriniMatrixReloaded
uv sync
```

To check that everything works, watch two agents play:

```bash
uv run scripts/watch_game.py greedy minimax
```

You can change the agents via cmd options.

## What's where

```
santorinai/
├── core.py        the game itself: rules, moves, board representation
├── agents.py      what an agent has to look like
├── players/       agents to play against: random, first choice, greedy, minimax
├── env.py         Gymnasium environment for training
└── match.py       play games between agents and collect results
scripts/           watch a game, run a tournament, measure engine speed
documentation/     design notes (engine, minimax) and the project presentation
test/              unit tests
```

Nothing in the package needs a screen, so training also runs on servers or
Colab. If you want to know why the engine is built the way it is, have a look
at [documentation/engine_core.md](documentation/engine_core.md).

## The rules in short

Two players, two workers each, no god powers.

1. The players take turns placing their workers on free cells (p0, p1, p0,
   p1). The agents learn where to place them too.
2. On your turn you move one worker to a neighbouring cell (any of the 8
   directions) that has no worker or dome on it and is at most one level
   higher. Then that worker builds one level on a cell next to it. A level
   on top of level 3 is a dome.
3. You win by stepping up onto level 3, or when your opponent can't move.

## Using the engine

### Playing moves

```python
from santorinai import GameState

state = GameState.new_game()  # starts with placing the workers
moves = state.legal_actions()  # 0..127 are moves, 128..152 placements
state.step(moves[0])  # play a move
print(state)  # the board as text
```

For neural networks there's also `state.observation()`, which returns the
board as a (9, 5, 5) array from the point of view of the player to move,
and `state.action_mask()`, which marks the legal moves among all 153.
`state.clone()` makes a cheap copy, which is what tree search needs.

### Writing your own agent

An agent only needs a `select_action` method that gets the current state and
returns one of the legal moves:

```python
import random

from santorinai import Agent, GameState


class MyAgent(Agent):
    def select_action(self, state: GameState) -> int:
        winning = [a for a in state.legal_actions() if state.is_winning_action(a)]
        return winning[0] if winning else random.choice(state.legal_actions())
```

### Letting agents play

```python
from santorinai.match import play_game, play_match
from santorinai.agents import GreedyAgent, MinimaxAgent, RandomAgent

# One game: the first agent is player 0 and moves first.
result = play_game([GreedyAgent(), RandomAgent()])
print(result.winner, result.reason, result.plies)

# 100 games, swapping who goes first every game.
match = play_match(MinimaxAgent(depth=2), GreedyAgent(), num_games=100)
print(f"minimax won {match.win_rate_a:.0%}")
```

### Training

`SantoriniEnv` is a normal Gymnasium environment. The opponent is part of
the environment: you pass in any agent, and it answers every move of the
agent you're training.

```python
from santorinai.env import SantoriniEnv
from santorinai.agents import GreedyAgent

env = SantoriniEnv(opponent=GreedyAgent())
obs, info = env.reset(seed=0)
obs, reward, terminated, truncated, info = env.step(env.action_masks().argmax())
```

The legal moves are in `env.action_masks()`, which is what sb3-contrib's
`MaskablePPO` expects.

## Examples

```bash
uv run scripts/watch_game.py minimax greedy       # watch a game move by move
uv run scripts/watch_game.py random first_choice --quiet --seed 3
uv run scripts/compare_agents.py                  # every agent against every other
```

`watch_game.py --help` lists the available agents.

## Benchmarks

We keep track of how fast the engine and the minimax agent are, so we can see
whether a change actually helped:

```bash
uv run scripts/benchmark_engine.py --label "what changed"   # measure and save
uv run scripts/benchmark_engine.py --history                # all runs so far
```

Each run is compared with the last one from the same computer and then added
to `benchmarks/results.jsonl` with the commit it ran on. Use `--quick` to skip
the slow minimax depth 3 and `--no-save` to just try something out. Timings
from different computers aren't comparable, so the comparison only looks at
runs from your own machine.

## Development

The `dev` dependency group brings [Ruff](https://docs.astral.sh/ruff/) for
linting and formatting and [ty](https://docs.astral.sh/ty/) for type
checking. Install the pre-commit hooks once after cloning, then they run on
every commit:

```bash
uv run pre-commit install
```

To run everything by hand:

```bash
uv run python -m unittest discover -s test
uv run ruff check .
uv run ruff format .
uv run ty check
```

## Credits

Santorini was created by [Roxley Games](https://roxley.com/).

## License

Apache License 2.0, see [LICENSE](LICENSE).

## Contributors

* Columbus-droid
* LadinaM
