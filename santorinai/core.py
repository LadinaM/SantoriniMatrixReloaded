"""
The Santorini game itself: rules, moves and the board as the network sees it.

This is the only place where the rules live. Why it's built this way (plain
lists, 153 actions, the observation layers, no limit on building pieces, ...)
is written up in documentation/engine_core.md.

Quick reference:
    cells           cell = x * 5 + y
    movement moves  action = worker * 64 + move_dir * 8 + build_dir   (0..127)
    placements      action = 128 + cell                               (128..152)
"""

import random
from collections.abc import Sequence
from enum import StrEnum
from typing import Self

import numpy as np


class StartMode(StrEnum):
    placement = "placement"
    random = "random"
    standard = "standard"


BOARD_SIZE = 5
NUM_CELLS = BOARD_SIZE * BOARD_SIZE
DOME = 4  # height value of a completed (domed) tower
WIN_HEIGHT = 3  # moving up onto this level wins
UNPLACED = -1  # worker cell value before the worker is placed

# The 8 directions as (dx, dy). Their order decides what every action number
# means, so don't change it once we have trained a model.
DIRECTIONS: tuple[tuple[int, int], ...] = (
    (-1, -1),
    (-1, 0),
    (-1, 1),
    (0, -1),
    (0, 1),
    (1, -1),
    (1, 0),
    (1, 1),
)
NUM_DIRECTIONS = len(DIRECTIONS)  # 8
ACTIONS_PER_WORKER = NUM_DIRECTIONS * NUM_DIRECTIONS  # 64: all (move, build) pairs
NUM_MOVE_ACTIONS = 2 * ACTIONS_PER_WORKER  # 128
PLACEMENT_OFFSET = NUM_MOVE_ACTIONS  # placement actions are 128 + cell
NUM_ACTIONS = NUM_MOVE_ACTIONS + NUM_CELLS  # 153

# Order in which the workers are placed (indices into ``workers``): p0w0,
# p1w0, p0w1, p1w1. In the official rules one player places both workers
# first, which would be (0, 1, 2, 3).
PLACEMENT_ORDER: tuple[int, int, int, int] = (0, 2, 1, 3)


def _build_neighbor_table() -> tuple[tuple[int, ...], ...]:
    """
    Work out the neighbour of every cell in every direction, -1 if it's off
    the board. Done once at import so move generation only has to look it up.
    """
    table = []
    for cell in range(NUM_CELLS):
        x, y = divmod(cell, BOARD_SIZE)
        row = []
        for dx, dy in DIRECTIONS:
            nx, ny = x + dx, y + dy
            if 0 <= nx < BOARD_SIZE and 0 <= ny < BOARD_SIZE:
                row.append(nx * BOARD_SIZE + ny)
            else:
                row.append(-1)
        table.append(tuple(row))
    return tuple(table)


NEIGHBORS = _build_neighbor_table()

# Cross-shaped opening for skipping placement: player 0 in the middle of the
# top and bottom row, player 1 in the middle of the left and right column.
STANDARD_START: tuple[int, int, int, int] = (
    0 * BOARD_SIZE + 2,
    4 * BOARD_SIZE + 2,
    2 * BOARD_SIZE + 0,
    2 * BOARD_SIZE + 4,
)

# Observation planes, see GameState.observation().
NUM_OBS_PLANES = 9


def encode_action(worker: int, move_dir: int, build_dir: int) -> int:
    """Pack (worker, move_dir, build_dir) into a movement action id 0..127."""
    return worker * ACTIONS_PER_WORKER + move_dir * NUM_DIRECTIONS + build_dir


def decode_action(action: int) -> tuple[int, int, int]:
    """Unpack a movement action id into (worker, move_dir, build_dir)."""
    worker, rest = divmod(action, ACTIONS_PER_WORKER)
    move_dir, build_dir = divmod(rest, NUM_DIRECTIONS)
    return worker, move_dir, build_dir


def placement_action(cell: int) -> int:
    """Action id for placing the next worker on ``cell``."""
    return PLACEMENT_OFFSET + cell


def is_placement_action(action: int) -> bool:
    return action >= PLACEMENT_OFFSET


def cell_to_xy(cell: int) -> tuple[int, int]:
    """Cell index -> (x, y)."""
    return divmod(cell, BOARD_SIZE)


def xy_to_cell(x: int, y: int) -> int:
    """(x, y) -> cell index."""
    return x * BOARD_SIZE + y


class Slots(StrEnum):
    legal = "_legal"
    heights = "heights"
    num_placed = "num_placed"
    ply = "ply"
    to_play = "to_play"
    winner = "winner"
    workers = "workers"


class GameState:
    """
    One Santorini position.

    ``step(action)`` plays a move on this position. ``child(action)`` returns
    the position after the move and leaves this one as it is, which is handy
    for tree search. The legal moves are worked out right after every move and
    kept until the next one.
    """

    __slots__ = (
        Slots.legal,
        Slots.heights,
        Slots.num_placed,
        Slots.ply,
        Slots.to_play,
        Slots.winner,
        Slots.workers,
    )

    def __init__(
        self,
        workers: Sequence[int] = (UNPLACED,) * 4,
        heights: Sequence[int] | None = None,
        to_play: int = 0,
    ) -> None:
        """
        Set up a position, e.g. a hand-made one for a test.

        Args:
            workers: the cells of ``[p0w0, p0w1, p1w0, p1w1]``, ``UNPLACED``
                for workers that aren't on the board yet. Workers have to be
                placed in ``PLACEMENT_ORDER``. By default nobody is placed.
            heights: the 25 cell heights (0-3, 4 = dome). Empty by default.
            to_play: whose turn it is. While placing, this has to match the
                placement order.
        """
        if len(workers) != 4:
            raise ValueError("workers must have 4 entries")
        placed = [c for c in workers if c != UNPLACED]
        if len(set(placed)) != len(placed):
            raise ValueError("workers must be on distinct cells")
        if not all(0 <= c < NUM_CELLS for c in placed):
            raise ValueError("worker cell out of range")
        num_placed = len(placed)
        if any(workers[i] == UNPLACED for i in PLACEMENT_ORDER[:num_placed]):
            raise ValueError("placed workers must follow PLACEMENT_ORDER")
        if heights is None:
            heights = [0] * NUM_CELLS
        if len(heights) != NUM_CELLS:
            raise ValueError(f"heights must have {NUM_CELLS} entries")
        if any(heights[c] == DOME for c in placed):
            raise ValueError("a worker cannot stand on a dome")
        if to_play not in (0, 1):
            raise ValueError("to_play must be 0 or 1")
        if num_placed < 4 and to_play != PLACEMENT_ORDER[num_placed] // 2:
            raise ValueError("to_play does not match the placement order")

        self.heights: list[int] = list(heights)
        self.workers: list[int] = list(workers)
        self.num_placed: int = num_placed
        self.to_play: int = to_play
        self.winner: int | None = None
        self.ply: int = 0
        self._legal: list[int] = self._generate_legal_actions()
        # The player to move may already be stuck in a hand-made position.
        if not self._legal:
            self.winner = 1 - to_play

    # ------------------------------------------------------------------ #
    # Construction
    # ------------------------------------------------------------------ #
    @classmethod
    def new_game(
        cls, start: StartMode = StartMode.placement, rng: random.Random | None = None
    ) -> Self:
        """
        Start a new game.

        Args:
            start: ``StartMode.placement`` (the real game) starts with an
                empty board. ``StartMode.random`` and ``StartMode.standard``
                skip placement and put the workers on random cells or on the
                cross opening, which is handy for debugging and benchmarks.
            rng: random generator for ``StartMode.random``; pass a seeded one
                to get the same start every time.
        """
        if start == StartMode.placement:
            return cls()
        if start == StartMode.standard:
            return cls(STANDARD_START)
        if start == StartMode.random:
            rng = rng or random.Random()
            return cls(rng.sample(range(NUM_CELLS), 4))
        raise ValueError(f"unknown start mode: {start!r}")

    def clone(self) -> Self:
        """
        Copy the position.

        Skips the checks in ``__init__`` because tree search copies a lot. The
        list of legal moves can be shared, since we only ever replace it.
        """
        new = type(self).__new__(type(self))
        new.heights = self.heights.copy()
        new.workers = self.workers.copy()
        new.num_placed = self.num_placed
        new.to_play = self.to_play
        new.winner = self.winner
        new.ply = self.ply
        new._legal = self._legal
        return new

    # ------------------------------------------------------------------ #
    # Rules
    # ------------------------------------------------------------------ #
    @property
    def in_placement(self) -> bool:
        """True while workers are still being placed."""
        return self.num_placed < 4

    def _generate_legal_actions(self) -> list[int]:
        """Enumerate all legal action ids for the player to move."""
        if self.num_placed < 4:
            occupied = self.workers
            heights = self.heights
            return [
                PLACEMENT_OFFSET + cell
                for cell in range(NUM_CELLS)
                if cell not in occupied and heights[cell] != DOME
            ]
        return self._generate_move_actions()

    def _generate_move_actions(self) -> list[int]:
        """
        All legal movement actions for the player to move.

        A winning move only gets one action number (the first build direction
        that works). The game ends before the build, so the others would just
        be duplicates. There's always at least one: the cell the worker just
        left.
        """
        heights = self.heights
        workers = self.workers
        base = self.to_play * 2
        actions: list[int] = []
        for w in (0, 1):
            idx = base + w
            src = workers[idx]
            src_height = heights[src]
            # The other three workers block both moving and building. The
            # moving worker's own source cell is free after the move.
            others = [workers[i] for i in range(4) if i != idx]
            src_neighbors = NEIGHBORS[src]
            for move_dir in range(NUM_DIRECTIONS):
                dst = src_neighbors[move_dir]
                if dst < 0 or dst in others:
                    continue
                dst_height = heights[dst]
                if dst_height == DOME or dst_height > src_height + 1:
                    continue
                winning = dst_height == WIN_HEIGHT and src_height < WIN_HEIGHT
                action_base = w * ACTIONS_PER_WORKER + move_dir * NUM_DIRECTIONS
                dst_neighbors = NEIGHBORS[dst]
                for build_dir in range(NUM_DIRECTIONS):
                    b = dst_neighbors[build_dir]
                    if b < 0 or heights[b] == DOME or b in others:
                        continue
                    actions.append(action_base + build_dir)
                    if winning:
                        break
        return actions

    def legal_actions(self) -> list[int]:
        """Legal action ids for the player to move (empty if the game is over)."""
        return self._legal

    def action_mask(self) -> np.ndarray:
        """Boolean mask of shape (153,), True for legal actions."""
        mask = np.zeros(NUM_ACTIONS, dtype=bool)
        mask[self._legal] = True
        return mask

    def move_destination(self, action: int) -> int:
        """Cell the moving worker ends up on for a movement action."""
        w, move_dir, _ = decode_action(action)
        return NEIGHBORS[self.workers[self.to_play * 2 + w]][move_dir]

    def is_winning_action(self, action: int) -> bool:
        """True if ``action`` moves a worker up onto level 3."""
        if action >= PLACEMENT_OFFSET or self.num_placed < 4:
            return False
        w, move_dir, _ = decode_action(action)
        src = self.workers[self.to_play * 2 + w]
        dst = NEIGHBORS[src][move_dir]
        return (
            dst >= 0
            and self.heights[dst] == WIN_HEIGHT
            and self.heights[src] < WIN_HEIGHT
        )

    def step(self, action: int, validate: bool = True) -> None:
        """
        Play ``action`` for the player whose turn it is.

        Args:
            action: one of ``legal_actions()``.
            validate: check the move first. Only switch this off when the move
                comes straight from ``legal_actions()`` (e.g. inside a search);
                an illegal move would quietly break the position.

        Raises:
            ValueError: if the game is over or the move isn't legal.
        """
        if validate:
            if self.winner is not None:
                raise ValueError("the game is already over")
            if action not in self._legal:
                raise ValueError(f"illegal action {action}")

        me = self.to_play
        self.ply += 1

        if action >= PLACEMENT_OFFSET:
            self.workers[PLACEMENT_ORDER[self.num_placed]] = action - PLACEMENT_OFFSET
            self.num_placed += 1
            # The next player is the owner of the next worker to place, or
            # player 0 once all workers are placed (player 0 moves first).
            if self.num_placed < 4:
                self.to_play = PLACEMENT_ORDER[self.num_placed] // 2
            else:
                self.to_play = 0
        else:
            w, move_dir, build_dir = decode_action(action)
            idx = me * 2 + w
            src = self.workers[idx]
            dst = NEIGHBORS[src][move_dir]
            self.workers[idx] = dst

            heights = self.heights
            if heights[dst] == WIN_HEIGHT and heights[src] < WIN_HEIGHT:
                self.winner = me
                self._legal = []
                return

            heights[NEIGHBORS[dst][build_dir]] += 1
            self.to_play = 1 - me

        self._legal = self._generate_legal_actions()
        if not self._legal:
            # The player to move cannot move: they lose.
            self.winner = 1 - self.to_play

    def child(self, action: int) -> Self:
        """Return the state after ``action`` without modifying ``self``."""
        new = self.clone()
        new.step(action)
        return new

    # ------------------------------------------------------------------ #
    # Queries
    # ------------------------------------------------------------------ #
    @property
    def is_terminal(self) -> bool:
        return self.winner is not None

    def reward(self, player: int) -> float:
        """+1 if ``player`` won, -1 if they lost, 0 while the game runs."""
        if self.winner is None:
            return 0.0
        return 1.0 if self.winner == player else -1.0

    def key(self) -> tuple:
        """
        The position as a hashable tuple, e.g. for a transposition table.

        Swapping a player's two workers gives a different key, because the
        actions refer to them by number.
        """
        return tuple(self.heights), tuple(self.workers), self.to_play

    def observation(self) -> np.ndarray:
        """
        The board for the network: nine 5x5 layers (float32, ``[layer, x, y]``),
        seen from the side of the player whose turn it is.

            0-4   one layer per height: level 0, 1, 2, 3, dome
            5     my first worker
            6     my second worker
            7     the opponent's workers
            8     all ones while workers are being placed

        Why it looks like this: documentation/engine_core.md.
        """
        obs = np.zeros((NUM_OBS_PLANES, BOARD_SIZE, BOARD_SIZE), dtype=np.float32)
        flat = obs.reshape(NUM_OBS_PLANES, NUM_CELLS)  # view, no copy
        flat[self.heights, range(NUM_CELLS)] = 1.0
        me = self.to_play * 2
        opp = (1 - self.to_play) * 2
        for plane, idx in ((5, me), (6, me + 1), (7, opp), (7, opp + 1)):
            cell = self.workers[idx]
            if cell != UNPLACED:  # -1 would silently index the last cell
                flat[plane, cell] = 1.0
        if self.num_placed < 4:
            flat[8] = 1.0
        return obs

    def __str__(self) -> str:
        """
        The board as text. Each cell shows a worker (``A``/``a`` for player 0,
        ``B``/``b`` for player 1, ``_`` for none) and its height. Rows are x,
        columns are y.
        """
        marks = {
            cell: mark for cell, mark in zip(self.workers, "AaBb") if cell != UNPLACED
        }
        lines = [
            " ".join(
                f"{marks.get(cell, '_')}{self.heights[cell]}"
                for cell in range(x * BOARD_SIZE, (x + 1) * BOARD_SIZE)
            )
            for x in range(BOARD_SIZE)
        ]
        if self.winner is not None:
            status = f"player {self.winner} won"
        elif self.num_placed < 4:
            status = f"player {self.to_play} to place"
        else:
            status = f"player {self.to_play} to play"
        return "\n".join(lines) + f"\n(ply {self.ply}, {status})"

    def __repr__(self) -> str:
        return (
            f"GameState(workers={self.workers}, heights={self.heights}, "
            f"to_play={self.to_play}, winner={self.winner}, ply={self.ply})"
        )
