"""Tests for the naive minimax agent."""

import random
import unittest

from santorinai.agents import GreedyAgent, MinimaxAgent, RandomAgent
from santorinai.agents.minimax_agent import evaluate
from santorinai.core import GameState, StartMode, xy_to_cell
from santorinai.match import play_match

c = xy_to_cell


class TestMinimax(unittest.TestCase):
    def test_takes_immediate_win(self):
        heights = [0] * 25
        heights[c(0, 0)] = 2
        heights[c(0, 1)] = 3
        s = GameState([c(0, 0), c(4, 4), c(2, 2), c(2, 4)], heights)
        self.assertTrue(
            s.is_winning_action(MinimaxAgent(depth=2, seed=0).select_action(s))
        )

    def test_blocks_opponent_win(self):
        # Player 1 (on (0,0), level 2) threatens to climb (0,1). Player 0's
        # worker on (2,1) can step next to it and dome it. Depth 2 sees the
        # threat; after the move the opponent must have no winning reply.
        heights = [0] * 25
        heights[c(0, 0)] = 2
        heights[c(0, 1)] = 3
        s = GameState([c(2, 1), c(4, 4), c(0, 0), c(2, 4)], heights)
        s.step(MinimaxAgent(depth=2, seed=0).select_action(s))
        self.assertFalse(any(s.is_winning_action(a) for a in s.legal_actions()))

    def test_visits_every_node(self):
        # Naive minimax visits the full tree: depth 1 = one node per legal
        # action, depth 2 = additionally one node per reply.
        s = GameState.new_game(StartMode.standard)
        agent = MinimaxAgent(depth=1, seed=0)
        agent.select_action(s)
        self.assertEqual(agent.nodes_searched, len(s.legal_actions()))

        agent = MinimaxAgent(depth=2, seed=0)
        agent.select_action(s)
        expected = sum(1 + len(s.child(a).legal_actions()) for a in s.legal_actions())
        self.assertEqual(agent.nodes_searched, expected)

    def test_evaluation_is_zero_sum(self):
        rng = random.Random(0)
        s = GameState.new_game()
        while not s.is_terminal:
            self.assertEqual(evaluate(s, 0), -evaluate(s, 1))
            s.step(rng.choice(s.legal_actions()))

    def test_only_legal_actions(self):
        rng = random.Random(1)
        agent = MinimaxAgent(depth=1, seed=1)
        for _ in range(5):
            s = GameState.new_game()
            while not s.is_terminal:
                a = (
                    agent.select_action(s)
                    if s.to_play == 0
                    else rng.choice(s.legal_actions())
                )
                self.assertIn(a, s.legal_actions())
                s.step(a)

    def test_beats_random_and_greedy(self):
        self.assertGreater(
            play_match(MinimaxAgent(depth=2, seed=0), RandomAgent(0), 10).win_rate_a,
            0.8,
        )
        self.assertGreater(
            play_match(MinimaxAgent(depth=2, seed=0), GreedyAgent(0), 10).win_rate_a,
            0.5,
        )

    def test_rejects_depth_zero(self):
        with self.assertRaises(ValueError):
            MinimaxAgent(depth=0)


if __name__ == "__main__":
    unittest.main()
