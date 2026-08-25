import unittest

from santorinai.player_examples.first_choice_player import FirstChoicePlayer
from santorinai.player_examples.random_player import RandomPlayer
from santorinai.tester import Tester


class TestTester(unittest.TestCase):
    def test_play_1v1_bad_players(self):
        tester = Tester()
        player1 = "Test"
        player2 = "Test"
        self.assertRaises(TypeError, tester.play_1v1, player1, player2)

    def test_play_1v1(self):
        tester = Tester()
        tester.verbose_level = 0
        tester.display_board = False

        player1 = RandomPlayer(2)
        player2 = FirstChoicePlayer(2)
        tester.play_1v1(player1, player2, nb_games=10)
