# The minimax agent

`MinimaxAgent` (in `santorinai/players/minimax_agent.py`) is our first agent
that actually thinks ahead. It's the plain textbook version for now, without
alpha-beta pruning. These notes explain how it works, how it scores
positions and how expensive it gets.

## How it searches

The agent looks `depth` turns ahead. For every legal move it plays the move
on a copy of the board, then tries every reply of the opponent, then every
answer to that, and so on, until it has looked `depth` turns deep. Along
the way it assumes both sides play well: on its own turns it picks the move
with the highest value, on the opponent's turns it assumes the opponent
picks the move with the lowest value (for us). Since turns always
alternate, "whose turn is it" is all it needs to know to decide between
maximum and minimum.

At the end of the lookahead the position is scored with an evaluation
function (see below). If a game ends earlier, the result counts as a win
(+1000) or a loss (−1000). We add the remaining depth to that number, so a
win found earlier in the search scores a little higher than one found
later. That makes the agent go for the quickest win and drag out a loss as
long as possible.

If several moves end up with the same value, the agent picks one of them at
random (with a seed for reproducibility). Otherwise it would play exactly the
same game every time against a deterministic opponent like
`FirstChoiceAgent`.

## How it scores a position

`evaluate(state, player)` adds up a score for each of my workers and
subtracts the same score for the opponent's workers. A worker gets

- 3 points per level it stands on, since higher workers are closer to
  winning,
- 1 point per free neighboring cell exactly one level higher, because those
  are steps it can climb next turn, and
- 0.25 points per neighboring cell on the board (3 in a corner, 5 on an
  edge, 8 in the middle), because workers in the middle are harder to trap.

Workers that haven't been placed yet don't count. The weights are constants
at the top of the file (`HEIGHT_WEIGHT`, `CLIMB_WEIGHT`, `CENTER_WEIGHT`), so
they're easy to experiment with. Since the score is "mine minus theirs",
`evaluate(state, 0)` is always exactly `-evaluate(state, 1)`; a test checks
this.

## How expensive it is

Without pruning, the agent looks at every position in the tree, so the work
grows with the number of moves to the power of the depth. Santorini usually
has 50 to 100 legal moves per turn, which makes each extra turn of lookahead
roughly 50 times slower. Measured on a mid-game position with 46 legal
moves:

| Depth | Positions looked at | Time per move |
|---|---:|---:|
| 1 | 46 | under 1 ms |
| 2 | 3,437 | 24 ms |
| 3 | 162,517 | 1.3 s |

Depth 2 is the default. Depth 3 is still usable for single games but too
slow for long tournaments, and anything much deeper won't finish.

At depth 2 the agent beat `RandomAgent` in all of 40 games, `FirstChoiceAgent`
in 70% and `GreedyAgent` in 88% (seats swapped every game).

## Counting positions

`nodes_searched` holds the number of positions the agent looked at for its
last move. For the plain version that number is exactly the size of the
search tree, and a test checks it at depth 1 and 2.

This is also how we'll check alpha-beta pruning once we add it. Alpha-beta
skips branches that can't change the result, so it has to pick a move with
the same value as the plain version while `nodes_searched` goes down. With
good move ordering (for example trying winning and climbing moves first),
depth 3 should come down from over a second to well below that.

## Implementation notes

The search copies the board for every move it tries (`clone()` followed by
`step(action, validate=False)`). It skips the legality check because the
moves come straight from `legal_actions()`, and checking them again would
only slow down the innermost loop.
