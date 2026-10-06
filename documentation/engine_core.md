# How the engine works (and why)

These are our notes on how the Santorini engine in `santorinai/` is built and
why we made the choices we did. The short version: everything is designed
around reinforcement learning. A policy network wants a fixed list of
actions, MCTS wants to copy game states millions of times, and both want the
board as a tensor. The docstrings in `santorinai/core.py` go into the same
details right next to the code.

## Layout

```
santorinai/
├── core.py          GameState: rules, action encoding, observation
├── agents.py        the Agent protocol
├── agents/          agents we play against and compare with
│   ├── random_agent.py
│   ├── first_choice_agent.py
│   ├── greedy_agent.py
│   └── minimax_agent.py
├── env.py           SantoriniEnv, a Gymnasium environment for training
└── match.py         play_game / play_match / round_robin for evaluation
```

The rules live in `core.py` and nowhere else. The training environment, the
match runner, the agents and (later) the GUI all go through `GameState`, so
if we ever change a rule there is exactly one place to do it.

```
 PPO ──────► SantoriniEnv ──┐
 MCTS (clone/step) ─────────┼──► GameState ◄── match.py (evaluation)
 GUI (later) ── Agents ─────┘
```

## Why we replaced SantorinAI's Board

We started from the `Board`/`Pawn`/`Player` classes of SantorinAI. They are
nice to read, but they didn't fit what we need for learning. A policy
network outputs one number per possible action, so we need a fixed action
list and a mask of the legal ones, while `Board` handed out lists of
`(pawn, move_pos, build_pos)` tuples of varying length. MCTS copies the game
state for every simulation, and `Board.copy()` rebuilt all the `Pawn`
objects each time. And the network needs the board as a tensor seen from the
side of the player whose turn it is. Rather than bending `Board` into all of
that, we wrote a small engine around these needs.

## How a position is stored

A `GameState` is just a handful of plain values:

| Field        | Meaning                                                                   |
|--------------|---------------------------------------------------------------------------|
| `heights`    | 25 numbers, one per cell: 0–3 for the building level, 4 for a dome        |
| `workers`    | 4 cells, ordered `[p0w0, p0w1, p1w0, p1w1]`; `UNPLACED` (−1) until placed |
| `num_placed` | how many workers are on the board; below 4 means we're still placing      |
| `to_play`    | whose turn it is, 0 or 1                                                  |
| `winner`     | `None` while the game runs, otherwise 0 or 1                              |
| `ply`        | how many turns have been played                                           |

Cells are numbered `cell = x * 5 + y`; `cell_to_xy` and `xy_to_cell` convert
back and forth.

We use plain Python lists instead of numpy arrays on purpose. The board only
has 25 cells, and for arrays that small numpy spends more time on its own
bookkeeping than on the actual work. Copying a short list, on the other
hand, is a single fast call. numpy only shows up where the network needs it:
in `observation()` and `action_mask()`.

For the same reason, the neighbors of every cell are worked out once when
the module is imported (`NEIGHBORS[cell][direction]`, with −1 for "off the
board"). Move generation then only needs a table lookup instead of
recomputing coordinates and bounds for every neighbor.

## Placement and movement

A game has two phases. First the players place their workers one at a time,
then they take turns moving and building.

We want the agent to learn placement as well. Where you start matters:
workers in the middle have more room, workers in a corner are easy to box
in. A fixed or random start would hide that part of the game.

Workers are placed in the order p0, p1, p0, p1 (`PLACEMENT_ORDER = (0, 2, 1,
3)`), which we kept from SantorinAI. In the official rules one player places
both workers first; that would be `(0, 1, 2, 3)`, and changing the constant
is all it takes. Player 0 moves first once everyone is placed.

## Actions

There are 153 actions in total:

```
movement:  action = worker * 64 + move_dir * 8 + build_dir     # 0..127
placement: action = 128 + cell                                  # 128..152
```

Placement and movement share one action list so that the network only needs
one output layer and one mask. During placement only 128–152 can be legal,
afterwards only 0–127, and the mask takes care of the rest. A placement
action only needs the cell, because the placement order already says which
worker goes next.

A movement action combines three choices: which of my two workers moves
(`worker`), in which of the 8 directions it steps (`move_dir`), and in which
direction it then builds (`build_dir`). The build direction is relative to
where the worker ends up, not to where it started. The formula packs the
three numbers into one like digits: `build_dir` is the last digit, `move_dir`
counts eights and `worker` counts sixty-fours, so every combination gets its
own number between 0 and 127.

We use directions instead of target cells because target cells would need
2 × 25 × 25 = 1,250 actions, almost all of them impossible. Directions give
us 128, and a given action means the same thing wherever it happens on the
board, which suits convolutional networks.

Two things to keep in mind:

- The order of `DIRECTIONS` must never change once we have trained a model.
  It defines what every action number means.
- A winning move (stepping up onto level 3) only gets one action number.
  The game ends before the build, so all eight build directions would lead
  to the same result. If we listed all of them, MCTS would treat them as
  eight different moves and spread its search across copies of the same
  thing.

## Rules we implement

- Two players, two workers each, no god powers.
- A worker can be placed on any cell without a worker or a dome.
- A worker moves to one of the 8 neighboring cells if there's no worker or
  dome on it and it's at most one level higher. Stepping down any number of
  levels is fine.
- Stepping up onto level 3 wins on the spot, without building.
- Otherwise the worker builds one level on a neighboring cell without a
  worker or a dome. The cell it just left counts too.
- If it's your turn and you have no legal move, you lose.

We left out the limit on building pieces. Each turn without a win adds
exactly one level, and the board can hold at most 25 × 4 = 100 levels, so a
game can't last longer than 4 + 101 = 105 turns.
With a piece limit, builds can become impossible, and in another Santorini
environment we looked at (cstorm125) that made some games run forever.

`GameState.new_game()` normally starts with placement. For debugging,
benchmarks, or if we want to teach movement before placement, there are two
shortcuts: `StartMode.random` puts the workers on random cells, and
`StartMode.standard` uses a fixed cross-shaped opening.

## What the network sees

`observation()` returns a stack of nine 5×5 layers (float32, indexed
`[layer, x, y]`):

| Layer | Content                                        |
|-------|------------------------------------------------|
| 0–4   | one layer per height: level 0, 1, 2, 3, dome   |
| 5     | my first worker                                |
| 6     | my second worker                               |
| 7     | the opponent's workers                         |
| 8     | all ones while we're placing, zeros afterwards |

Everything is seen from the side of the player whose turn it is. That way
one network can play both colors, because it always answers the same
question: what's best for me right now? This is also how AlphaZero does it.
It does mean that a value `v` for the current player is `-v` for the other
one.

My two workers get separate layers because actions refer to them by number;
the opponent's two workers are interchangeable, so one layer is enough.
Heights are split into one layer each so the network doesn't have to figure
out from a single number that 3 means "win" and 4 means "wall". The phase
layer is technically redundant (you could count the workers), but it costs
nothing.

Unplaced workers simply don't appear. One trap we ran into: `UNPLACED` is
−1, and indexing an array with −1 quietly marks the last cell instead. A test
checks that this doesn't happen.

## Using it for search (MCTS)

The methods that matter for tree search:

- `legal_actions()` returns the legal moves. They're computed at the end of
  every `step()` anyway, so asking for them is free.
- `step(action, validate=False)` plays a move in place without checking it
  again. Only use it with actions from `legal_actions()`.
- `clone()` copies the state in about 0.13 µs; `child(action)` is a clone
  plus a step.
- `key()` returns a hashable version of the position for transposition
  tables.
- `is_terminal`, `winner` and `reward(player)` tell you how the game ended.

We compute the legal moves right after each move because we need them to
know whether the next player is stuck (and has lost), and almost every
caller asks for them next anyway. The list is never changed afterwards, only
replaced, so clones can safely share it.

## The training environment

`SantoriniEnv` follows the Gymnasium interface. Santorini has two players,
but most RL libraries expect one agent, so the opponent becomes part of the
environment: after the agent moves, the opponent (any `Agent`) replies, and
the agent gets the resulting position. For self-play we can pass in a frozen
copy of the policy being trained and swap it out every so often.

Each episode starts with placement. Since turns strictly alternate in both
phases, "agent moves, opponent answers once" works for the whole game. The
agent gets a random seat each episode so it doesn't learn to rely on going
first, and because observations are always from its own point of view it
can't tell the difference anyway.

The legal moves come back in `info["action_mask"]` and through
`action_masks()`, which is the name sb3-contrib's `MaskablePPO` looks for.
Rewards are +1 for a win, −1 for a loss and 0 otherwise. We deliberately
don't reward intermediate things like "climbed a level", because agents in
board games tend to find ways to collect those rewards without actually
winning. If the agent picks an illegal move, it loses by default (useful
without masking); with `illegal_action="raise"` you get an error instead,
which helps when debugging a masking setup.

## Agents

Anything that picks moves is an agent: it just needs a
`select_action(state) -> int` method. That covers our baselines, a trained
policy, MCTS, and later a human clicking in the GUI. Because they all look
the same from the outside, human against model, model against model and
human against human all work without special cases.

The players we have so far:

- `RandomAgent` picks any legal move.
- `FirstChoiceAgent` always picks the first legal move.
- `GreedyAgent` places its workers in the middle of the board. It takes a
  win if it sees one, otherwise avoids moves that let the opponent win right
  away, and otherwise climbs as high as it can.
- `MinimaxAgent` looks a few turns ahead (two by default), assuming the
  opponent always answers with its best move, and scores the positions at
  the end with a simple formula: how high the workers stand, how many steps
  they could climb next, and how central they are. It doesn't use alpha-beta
  pruning yet, so it looks at every position; each extra turn of lookahead
  makes it roughly 50 times slower. More about it in [minimax.md](minimax.md).

When we let the first three play each other (`scripts/compare_agents.py`,
200 games per pair, seats swapped every game), the row player won:

|             | FirstChoice | Greedy | Minimax | Random |
|-------------|-------------|--------|---------|--------|
| FirstChoice | -           | 38%    | 28%     | 100%   |
| Greedy      | 62%         | -      | 12%     | 100%   |
| Minimax     | 72%         | 88%    | -       | 100%   |
| Random      | 0%          | 0%     | 0%      | -      |


## Evaluating agents

`play_game` plays one game and tells you who won, why (`climbed`,
`opponent_stuck` or `illegal_action`) and which moves were played.
`play_match` plays many games and swaps the seats each time. Santorini
favors the player who moves first, and with fixed seats we'd mostly be
measuring that. An agent that returns an illegal move loses that game, so a
buggy experiment doesn't crash a long evaluation run.

## Tests

`test/test_core.py` checks each rule on hand-built positions: winning by
climbing, not climbing two levels, domes, workers blocking each other,
building on the cell you just left, losing when you're stuck, and the
placement order. It also plays 500 random games and checks that nothing
impossible ever happens: workers never share a cell or stand on a dome,
buildings never shrink, every turn adds exactly one level, and no game lasts
more than 105 turns.

## Ideas for later

- If MCTS ever becomes too slow, numba or a bitboard representation would
  speed up the engine. For now we expect the neural network to be the
  bottleneck.
- A thing to think about, idea by an LLM: The board looks the same after rotating or mirroring it (8 ways). For
  AlphaZero-style training we could use that to get 8 training examples out
  of each position; the direction numbers in the actions would have to be
  remapped the same way.