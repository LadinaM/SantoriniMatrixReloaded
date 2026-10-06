"""Tests for the baseline agents, the match runner and the Gymnasium env."""

import random
import unittest

import numpy as np

from santorinai.agents import FirstChoiceAgent, GreedyAgent, RandomAgent
from santorinai.core import NUM_ACTIONS, GameState, xy_to_cell
from santorinai.env import SantoriniEnv
from santorinai.match import format_round_robin, play_game, play_match, round_robin


class IllegalAgent:
    def select_action(self, state: GameState) -> int:
        return next(a for a in range(NUM_ACTIONS) if a not in state.legal_actions())


class TestAgents(unittest.TestCase):
    def test_agents_only_play_legal_actions(self):
        for agent in (RandomAgent(0), FirstChoiceAgent(), GreedyAgent(0)):
            rng = random.Random(0)
            for _ in range(20):
                s = GameState.new_game()
                while not s.is_terminal:
                    a = agent.select_action(s)
                    self.assertIn(a, s.legal_actions())
                    s.step(a)
                    if not s.is_terminal:  # random opponent for variety
                        s.step(rng.choice(s.legal_actions()))

    def test_greedy_takes_win_and_blocks(self):
        c = xy_to_cell
        heights = [0] * 25
        heights[c(0, 0)] = 2
        heights[c(0, 1)] = 3
        s = GameState([c(0, 0), c(4, 4), c(2, 2), c(2, 4)], heights)
        self.assertTrue(s.is_winning_action(GreedyAgent(0).select_action(s)))

        # Now player 1 (on (0,0), level 2) threatens to climb (0,1). Player 0's
        # worker on (2,1) can step next to it and dome it, and must do so.
        s = GameState([c(2, 1), c(4, 4), c(0, 0), c(2, 4)], heights)
        s.step(GreedyAgent(0).select_action(s))  # player 0's turn
        self.assertFalse(any(s.is_winning_action(a) for a in s.legal_actions()))

    def test_greedy_places_centrally(self):
        s = GameState.new_game()
        a = GreedyAgent(0).select_action(s) - 128
        self.assertTrue(1 <= a // 5 <= 3 and 1 <= a % 5 <= 3)


class TestMatch(unittest.TestCase):
    def test_play_game_reports_winner_and_reason(self):
        result = play_game([RandomAgent(0), RandomAgent(1)])
        self.assertIn(result.winner, (0, 1))
        self.assertIn(result.reason, ("climbed", "opponent_stuck"))
        self.assertEqual(result.plies, len(result.actions))

    def test_illegal_action_forfeits(self):
        result = play_game([IllegalAgent(), RandomAgent(0)])
        self.assertEqual(result.winner, 1)
        self.assertEqual(result.reason, "illegal_action")

    def test_on_move_callback(self):
        seen = []
        result = play_game(
            [RandomAgent(0), RandomAgent(1)], on_move=lambda s, a: seen.append(a)
        )
        self.assertEqual(seen, result.actions)

    def test_greedy_beats_random(self):
        result = play_match(GreedyAgent(0), RandomAgent(0), num_games=100)
        self.assertEqual(result.num_games, 100)
        self.assertGreater(result.win_rate_a, 0.8)

    def test_round_robin_table(self):
        agents = {"random": RandomAgent(0), "greedy": GreedyAgent(0)}
        results = round_robin(agents, num_games=4)
        self.assertEqual(list(results), [("random", "greedy")])
        table = format_round_robin(results)
        self.assertIn("| greedy |", table)
        self.assertIn("| random |", table)


class TestEnv(unittest.TestCase):
    def test_random_rollouts(self):
        env = SantoriniEnv(illegal_action="raise")
        rng = random.Random(0)
        for episode in range(50):
            obs, info = env.reset(seed=episode)
            self.assertTrue(env.observation_space.contains(obs))
            done = False
            reward = 0.0
            while not done:
                legal = np.flatnonzero(info["action_mask"])
                obs, reward, done, truncated, info = env.step(int(rng.choice(legal)))
                self.assertFalse(truncated)
            self.assertIn(reward, (-1.0, 1.0))

    def test_agent_moves_first_or_second(self):
        env = SantoriniEnv(agent_player=1)
        env.reset(seed=0)
        # The opponent already placed its first worker.
        self.assertEqual(env.state.num_placed, 1)
        self.assertEqual(env.state.to_play, 1)

    def test_illegal_action_loses(self):
        env = SantoriniEnv()
        _, info = env.reset(seed=0)
        illegal = int(np.flatnonzero(~info["action_mask"])[0])
        _, reward, done, _, info = env.step(illegal)
        self.assertEqual(reward, -1.0)
        self.assertTrue(done)
        self.assertTrue(info["illegal_action"])


if __name__ == "__main__":
    unittest.main()
