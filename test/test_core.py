"""Rule tests for the game engine (``santorinai.core``)."""

import random
import unittest

import numpy as np

from santorinai.core import (
    DOME,
    NEIGHBORS,
    NUM_ACTIONS,
    NUM_MOVE_ACTIONS,
    PLACEMENT_ORDER,
    UNPLACED,
    GameState,
    StartMode,
    decode_action,
    encode_action,
    is_placement_action,
    placement_action,
    xy_to_cell,
)


def c(x: int, y: int) -> int:
    return xy_to_cell(x, y)


# Workers far from the top-left corner, used as "bystanders" in rule tests.
P1_FAR = [c(2, 2), c(2, 4)]


class TestActionEncoding(unittest.TestCase):
    def test_roundtrip(self):
        for a in range(NUM_MOVE_ACTIONS):
            self.assertEqual(encode_action(*decode_action(a)), a)

    def test_placement_actions_follow_move_actions(self):
        self.assertEqual(NUM_ACTIONS, 128 + 25)
        self.assertEqual(placement_action(0), 128)
        self.assertTrue(is_placement_action(placement_action(24)))
        self.assertFalse(is_placement_action(127))


class TestPlacement(unittest.TestCase):
    def test_new_game_starts_in_placement(self):
        s = GameState.new_game()
        self.assertTrue(s.in_placement)
        self.assertEqual(s.workers, [UNPLACED] * 4)
        self.assertEqual(s.legal_actions(), [placement_action(i) for i in range(25)])

    def test_alternating_order_then_player_0_moves(self):
        s = GameState.new_game()
        cells = [c(0, 0), c(1, 1), c(2, 2), c(3, 3)]
        for k, cell in enumerate(cells):
            self.assertEqual(s.to_play, PLACEMENT_ORDER[k] // 2)
            s.step(placement_action(cell))
            self.assertEqual(s.workers[PLACEMENT_ORDER[k]], cell)
        # p0w0, p0w1, p1w0, p1w1
        self.assertEqual(s.workers, [c(0, 0), c(2, 2), c(1, 1), c(3, 3)])
        self.assertFalse(s.in_placement)
        self.assertEqual(s.to_play, 0)
        self.assertTrue(all(a < NUM_MOVE_ACTIONS for a in s.legal_actions()))

    def test_cannot_place_on_occupied_cell(self):
        s = GameState.new_game()
        s.step(placement_action(c(2, 2)))
        self.assertNotIn(placement_action(c(2, 2)), s.legal_actions())
        self.assertEqual(len(s.legal_actions()), 24)
        with self.assertRaises(ValueError):
            s.step(placement_action(c(2, 2)))

    def test_move_actions_illegal_during_placement(self):
        s = GameState.new_game()
        self.assertFalse(s.action_mask()[:NUM_MOVE_ACTIONS].any())

    def test_partially_placed_constructor_validates_order(self):
        GameState([c(0, 0), UNPLACED, c(1, 1), UNPLACED], to_play=0)
        with self.assertRaises(ValueError):  # p0w1 placed before p1w0
            GameState([c(0, 0), c(1, 1), UNPLACED, UNPLACED], to_play=1)
        with self.assertRaises(ValueError):  # wrong player to place
            GameState([c(0, 0), UNPLACED, UNPLACED, UNPLACED], to_play=0)


class TestMovement(unittest.TestCase):
    def test_moving_up_to_level_3_wins_without_build(self):
        heights = [0] * 25
        heights[c(0, 0)] = 2
        heights[c(0, 1)] = 3
        s = GameState([c(0, 0), c(4, 4), *P1_FAR], heights)
        wins = [a for a in s.legal_actions() if s.is_winning_action(a)]
        # Exactly one action per winning (worker, move): no duplicate builds.
        self.assertEqual(len(wins), 1)
        before = list(s.heights)
        s.step(wins[0])
        self.assertEqual(s.winner, 0)
        self.assertEqual(s.heights, before)
        self.assertEqual(s.legal_actions(), [])

    def test_moving_down_is_allowed(self):
        heights = [0] * 25
        heights[c(0, 0)] = 3
        s = GameState([c(0, 0), c(4, 4), *P1_FAR], heights)
        self.assertIn(encode_action(0, 4, 3), s.legal_actions())  # 3 -> 0

    def test_cannot_climb_two_levels_or_onto_dome(self):
        heights = [0] * 25
        heights[c(0, 1)] = 2
        heights[c(1, 0)] = DOME
        heights[c(1, 1)] = DOME
        s = GameState([c(0, 0), c(4, 4), *P1_FAR], heights)
        for a in s.legal_actions():
            w, _, _ = decode_action(a)
            self.assertEqual(w, 1, "worker 0 at (0,0) must be blocked")

    def test_cannot_move_or_build_onto_workers(self):
        # Worker 0 at (0,0) is boxed in by the three other workers; worker 1
        # at (0,1) may neither step nor build onto the remaining workers.
        s = GameState([c(0, 0), c(0, 1), c(1, 0), c(1, 1)])
        blocked = (c(0, 0), c(1, 0), c(1, 1))
        for a in s.legal_actions():
            w, _, build_dir = decode_action(a)
            self.assertEqual(w, 1)
            dst = s.move_destination(a)
            self.assertNotIn(dst, blocked)
            self.assertNotIn(NEIGHBORS[dst][build_dir], blocked)

    def test_can_build_on_vacated_cell(self):
        s = GameState([c(0, 0), c(4, 4), *P1_FAR])
        a = encode_action(0, 4, 3)  # move (0,+1), build (0,-1)
        self.assertIn(a, s.legal_actions())
        s.step(a)
        self.assertEqual(s.heights[c(0, 0)], 1)

    def test_build_on_level_3_makes_dome(self):
        heights = [0] * 25
        heights[c(0, 0)] = 3
        s = GameState([c(0, 1), c(4, 4), *P1_FAR], heights)
        s.step(encode_action(0, 6, 0))  # move to (1,1), build (0,0)
        self.assertEqual(s.heights[c(0, 0)], DOME)

    def test_stuck_player_loses(self):
        # Player 1's workers sit in corners walled in by domes, except that
        # (4,3) at level 1 is still reachable from (4,4). Player 0 moves
        # (2,2) -> (3,2) and builds (4,3) up to level 2, which closes the
        # last escape: player 1 has no legal move and loses.
        heights = [0] * 25
        for cell in (c(0, 1), c(1, 0), c(1, 1), c(3, 3), c(3, 4)):
            heights[cell] = DOME
        heights[c(4, 3)] = 1
        s = GameState([c(2, 2), c(2, 0), c(0, 0), c(4, 4)], heights)
        s.step(encode_action(0, 6, 7))  # move (+1, 0), build (+1, +1)
        self.assertEqual(s.heights[c(4, 3)], 2)
        self.assertEqual(s.legal_actions(), [])
        self.assertEqual(s.winner, 0)

    def test_illegal_action_raises(self):
        s = GameState.new_game(StartMode.standard)
        illegal = next(a for a in range(NUM_ACTIONS) if a not in s.legal_actions())
        with self.assertRaises(ValueError):
            s.step(illegal)

    def test_step_after_game_over_raises(self):
        heights = [0] * 25
        heights[c(0, 0)] = 2
        heights[c(0, 1)] = 3
        s = GameState([c(0, 0), c(4, 4), *P1_FAR], heights)
        s.step(next(a for a in s.legal_actions() if s.is_winning_action(a)))
        with self.assertRaises(ValueError):
            s.step(0)


class TestInvariants(unittest.TestCase):
    """Properties that must hold in every position of random games."""

    def test_random_games(self):
        rng = random.Random(1)
        for _ in range(500):
            s = GameState.new_game()
            while not s.is_terminal:
                prev = s.clone()
                action = rng.choice(s.legal_actions())
                s.step(action)
                placed = [w for w in s.workers if w != UNPLACED]
                self.assertEqual(len(placed), len(set(placed)))
                self.assertTrue(all(s.heights[w] != DOME for w in placed))
                # Heights never go down, and exactly one level is added per
                # movement turn (none during placement or on a winning move).
                self.assertTrue(all(a >= b for a, b in zip(s.heights, prev.heights)))
                builds = not prev.in_placement and not prev.is_winning_action(action)
                self.assertEqual(sum(s.heights) - sum(prev.heights), int(builds))
            self.assertLessEqual(s.ply, 105)

    def test_clone_is_independent(self):
        s = GameState.new_game(StartMode.random, random.Random(0))
        t = s.clone()
        t.step(t.legal_actions()[0])
        self.assertEqual(s.ply, 0)
        self.assertNotEqual(s.key(), t.key())

    def test_child_leaves_parent_untouched(self):
        s = GameState.new_game(StartMode.standard)
        key = s.key()
        s.child(s.legal_actions()[0])
        self.assertEqual(s.key(), key)


class TestObservation(unittest.TestCase):
    def test_canonical_planes(self):
        s = GameState.new_game(StartMode.standard)
        obs = s.observation()
        self.assertEqual(obs.shape, (9, 5, 5))
        self.assertEqual(obs.dtype, np.float32)
        self.assertTrue(np.all(obs[8] == 0.0))  # not in placement
        self.assertEqual(obs[5, 0, 2], 1.0)  # player 0 worker 0 at (0,2)
        s.step(s.legal_actions()[0])
        obs = s.observation()
        self.assertEqual(obs[5, 2, 0], 1.0)  # now player 1's worker 0 is "mine"
        self.assertTrue(np.all(obs[:5].sum(axis=0) == 1.0))  # one-hot heights

    def test_during_placement(self):
        s = GameState.new_game()
        s.step(placement_action(c(4, 4)))  # p0 places; now p1's turn
        obs = s.observation()
        self.assertTrue(np.all(obs[8] == 1.0))  # placement-phase plane
        self.assertEqual(obs[7, 4, 4], 1.0)  # p0's worker is the opponent's
        self.assertEqual(obs[5:7].sum(), 0.0)  # p1 has nothing placed yet
        # The unplaced (-1) workers must not leak into the last cell.
        self.assertEqual(obs[5:8, 4, 4].sum(), 1.0)

    def test_action_mask_matches_legal_actions(self):
        s = GameState.new_game(StartMode.random, random.Random(2))
        mask = s.action_mask()
        self.assertEqual(mask.shape, (NUM_ACTIONS,))
        self.assertEqual(list(np.flatnonzero(mask)), sorted(s.legal_actions()))


if __name__ == "__main__":
    unittest.main()
