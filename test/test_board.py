# Test file for board.py

import unittest

from santorinai.board import Board


class TestBoardTwoPlayers(unittest.TestCase):
    NB_PLAYERS = 2

    def setUp(self):
        self.board = Board(self.NB_PLAYERS)

    def test_init(self):
        # Test if the board is initialized correctly
        self.assertEqual(self.board.board_size, 5)
        self.assertEqual(
            self.board.board,
            [
                [0 for _ in range(self.board.board_size)]
                for _ in range(self.board.board_size)
            ],
        )
        self.assertEqual(self.board.player_turn, 1)
        self.assertEqual(self.board.winner_player_number, None)

        # Test if the pawns are initialized correctly
        self.assertEqual(len(self.board.pawns), self.NB_PLAYERS * 2)

        # Pawn n°1 belongs to player n°1
        # Pawn n°2 belongs to player n°2
        # Pawn n°3 belongs to player n°1
        # Pawn n°4 belongs to player n°2

        self.assertEqual(self.board.pawns[0].number, 1)
        self.assertEqual(self.board.pawns[0].player_number, 1)
        self.assertEqual(self.board.pawns[1].number, 2)
        self.assertEqual(self.board.pawns[1].player_number, 2)
        self.assertEqual(self.board.pawns[2].number, 3)
        self.assertEqual(self.board.pawns[2].player_number, 1)
        self.assertEqual(self.board.pawns[3].number, 4)
        self.assertEqual(self.board.pawns[3].player_number, 2)

    def test_is_move_possible(self):
        # Test if it is not possible to move from outside the board
        self.assertFalse(self.board.is_move_possible((-1, -1), (0, 0))[0])
        self.assertFalse(self.board.is_move_possible((0, 0), (-1, -1))[0])

        # Test if it is not possible to move to the same position
        self.assertFalse(self.board.is_move_possible((0, 0), (0, 0))[0])

        # Test if it is not possible to move on a terminated tower
        self.board.board[0][0] = 0
        self.board.board[0][1] = 4
        self.assertFalse(self.board.is_move_possible((0, 0), (0, 1))[0])

        # Test if it is not possible to move two levels in one move
        self.board.board[0][0] = 0
        self.board.board[0][1] = 2
        self.assertFalse(self.board.is_move_possible((0, 0), (0, 1))[0])
        self.board.board[0][0] = 1
        self.board.board[0][1] = 3
        self.assertFalse(self.board.is_move_possible((0, 0), (0, 1))[0])
        self.board.board[0][1] = 0

        # Test if it is not possible to move too far
        self.assertFalse(self.board.is_move_possible((0, 0), (0, 2))[0])
        self.assertFalse(self.board.is_move_possible((0, 0), (2, 0))[0])

        # Test if it is not possible to move on another pawn
        self.board.pawns[0].pos = (0, 1)
        self.assertFalse(self.board.is_move_possible((0, 0), (0, 1))[0])

        # Test if it is possible to move on an empty neighboring position
        self.assertTrue(self.board.is_move_possible((2, 2), (2, 3))[0])
        self.assertTrue(self.board.is_move_possible((2, 2), (1, 2))[0])
        self.assertTrue(self.board.is_move_possible((2, 2), (1, 1))[0])
        self.assertTrue(self.board.is_move_possible((2, 2), (3, 3))[0])

    def test_is_position_within_board(self):
        # Test if it is not possible to move from outside the board
        self.assertFalse(self.board.is_position_within_board((-1, -1)))
        self.assertFalse(self.board.is_position_within_board((0, -1)))
        self.assertFalse(self.board.is_position_within_board((-1, 0)))

        # Test if it is possible to move within the board
        self.assertTrue(self.board.is_position_within_board((0, 0)))
        self.assertTrue(self.board.is_position_within_board((0, 1)))
        self.assertTrue(self.board.is_position_within_board((1, 0)))
        self.assertTrue(self.board.is_position_within_board((1, 1)))

    def test_is_build_possible(self):
        # Test if it is not possible to build from outside the board
        self.assertFalse(self.board.is_build_possible((-1, -1), (0, 0))[0])
        self.assertFalse(self.board.is_build_possible((0, 0), (-1, -1))[0])

        # Test if it is not possible to build on the same position
        self.assertFalse(self.board.is_build_possible((0, 0), (0, 0))[0])

        # Test if it is not possible to build on a terminated tower
        self.board.board[0][0] = 0
        self.board.board[0][1] = 4
        self.assertFalse(self.board.is_build_possible((0, 0), (0, 1))[0])
        self.board.board[0][1] = 0

        # Test if it is not possible to build too far
        self.assertFalse(self.board.is_build_possible((0, 0), (0, 2))[0])
        self.assertFalse(self.board.is_build_possible((0, 0), (2, 0))[0])

        # Test if it is not possible to build on another pawn
        self.board.pawns[0].pos = (0, 1)
        self.assertEqual(
            self.board.is_build_possible((0, 0), (0, 1)),
            (False, "It is not possible to build on another pawn."),
        )

        # Test if it is possible to build on an empty neighboring position
        self.assertTrue(self.board.is_build_possible((2, 2), (2, 3))[0])
        self.assertTrue(self.board.is_build_possible((2, 2), (1, 2))[0])
        self.assertTrue(self.board.is_build_possible((2, 2), (1, 1))[0])
        self.assertTrue(self.board.is_build_possible((2, 2), (3, 3))[0])

    def test_copy(self):
        board = Board(self.NB_PLAYERS)
        board.board[0][0] = 1
        board_copy = board.copy()
        self.assertEqual(board_copy.board[0][0], board.board[0][0])

        board_copy.board[0][0] = 2
        self.assertNotEqual(board_copy.board[0][0], board.board[0][0])

        board_copy.pawns[0].pos = (1, 1)
        self.assertNotEqual(board_copy.pawns[0].pos, board.pawns[0].pos)


class TestBoardThreePlayers(unittest.TestCase):
    NB_PLAYERS = 3

    def setUp(self):
        self.board = Board(self.NB_PLAYERS)

    def test_init(self):
        # Test if the board is initialized correctly
        self.assertEqual(self.board.board_size, 5)
        self.assertEqual(
            self.board.board,
            [
                [0 for _ in range(self.board.board_size)]
                for _ in range(self.board.board_size)
            ],
        )
        self.assertEqual(self.board.player_turn, 1)
        self.assertEqual(self.board.winner_player_number, None)

        # Test if the pawns are initialized correctly
        self.assertEqual(len(self.board.pawns), self.NB_PLAYERS * 2)

        # Pawn n°1 belongs to player n°1
        # Pawn n°2 belongs to player n°2
        # Pawn n°3 belongs to player n°3
        # Pawn n°4 belongs to player n°1
        # Pawn n°5 belongs to player n°2
        # Pawn n°6 belongs to player n°3

        self.assertEqual(self.board.pawns[0].number, 1)
        self.assertEqual(self.board.pawns[0].player_number, 1)
        self.assertEqual(self.board.pawns[1].number, 2)
        self.assertEqual(self.board.pawns[1].player_number, 2)
        self.assertEqual(self.board.pawns[2].number, 3)
        self.assertEqual(self.board.pawns[2].player_number, 3)
        self.assertEqual(self.board.pawns[3].number, 4)
        self.assertEqual(self.board.pawns[3].player_number, 1)
        self.assertEqual(self.board.pawns[4].number, 5)
        self.assertEqual(self.board.pawns[4].player_number, 2)
        self.assertEqual(self.board.pawns[5].number, 6)
        self.assertEqual(self.board.pawns[5].player_number, 3)


class TestBoardTwoPlayersGame(unittest.TestCase):
    NB_PLAYERS = 2

    def test_normal_game(self):
        board = Board(self.NB_PLAYERS)

        self.assertEqual(board.player_turn, 1)
        self.assertEqual(board.turn_number, 1)

        # ==== Pawns placement ====
        # Player 1 places his first pawn
        move_ok, _ = board.place_pawn((0, 0))
        self.assertTrue(move_ok)
        self.assertEqual(board.player_turn, 2)
        self.assertEqual(board.turn_number, 2)

        # Player 2 places his first pawn
        move_ok, _ = board.place_pawn((0, 1))
        self.assertTrue(move_ok)
        self.assertEqual(board.player_turn, 1)
        self.assertEqual(board.turn_number, 3)

        # Player 1 place his second pawn
        move_ok, _ = board.place_pawn((1, 0))
        self.assertTrue(move_ok)
        self.assertEqual(board.player_turn, 2)
        self.assertEqual(board.turn_number, 4)

        # Player 2 try to move before placing his second pawn
        success, reason = board.play_move(2, (0, 1), (0, 2))
        self.assertFalse(success)
        self.assertEqual(reason, "All the pawns have not been placed yet.")

        # Player 2 place his second pawn but fails
        move_ok, reason = board.place_pawn((1, 0))
        self.assertFalse(move_ok)
        self.assertEqual(reason, "The position is already occupied by another pawn.")

        # The turn hasn't changed:
        self.assertEqual(board.player_turn, 2)
        self.assertEqual(board.turn_number, 4)

        # Player 2 place his second pawn but fails again
        move_ok, reason = board.place_pawn((5, 5))
        self.assertFalse(move_ok)
        self.assertEqual(reason, "The position is not within the board bounds.")
        # The turn hasn't changed:
        self.assertEqual(board.player_turn, 2)
        self.assertEqual(board.turn_number, 4)

        # Player 2 place his second pawn
        move_ok, _ = board.place_pawn((1, 1))
        self.assertTrue(move_ok)

        # Back to player 1 pawn 1
        self.assertEqual(board.player_turn, 1)
        self.assertEqual(board.turn_number, 5)

        # Current board:   Current pawns:
        # 0 0 0 0 0        _ _ _ _ _
        # 0 0 0 0 0        _ _ _ _ _
        # 0 0 0 0 0        _ _ _ _ _
        # 0 0 0 0 0        2 4 _ _ _
        # 0 0 0 0 0        1 3 _ _ _

        # ==== Pawns Moves ====
        # Pawn 1 is blocked
        pawn1 = board.get_playing_pawn(1)
        assert pawn1 is not None
        self.assertEqual(len(board.get_possible_movement_positions(pawn1)), 0)
        # But pawn 2 can move
        pawn2 = board.get_playing_pawn(2)
        assert pawn2 is not None
        self.assertGreater(len(board.get_possible_building_positions(pawn2)), 0)
        # Player 1 try to move pawn 1 but fails
        move_ok, reason = board.play_move(1, (None, None), (None, None))
        self.assertFalse(move_ok)
        self.assertEqual(reason, "The selected pawn is stuck.")
        self.assertEqual(board.get_player_pawns(1)[0].pos, (0, 0))

        # The turn hasn't changed:
        self.assertEqual(board.player_turn, 1)
        self.assertEqual(board.turn_number, 5)

        # Player 1 try to move a non existing pawn
        move_ok, reason = board.play_move(3, (None, None), (None, None))
        self.assertFalse(move_ok)
        self.assertEqual(reason, "The pawn number is invalid (must be 1 or 2).")
        self.assertEqual(board.player_turn, 1)
        self.assertEqual(board.turn_number, 5)

        # Player 1 moves his other pawn top right and builds down left
        move_ok, _ = board.play_move(2, (2, 1), (1, 0))
        self.assertTrue(move_ok)
        self.assertEqual(board.player_turn, 2)
        self.assertEqual(board.turn_number, 6)
        self.assertEqual(
            board.get_player_pawn(player_number=1, pawn_number=2).pos, (2, 1)
        )
        self.assertEqual(board.board[1][0], 1)

        # Player 2 moves pawn 1 top and builds down
        move_ok, _ = board.play_move(1, (0, 2), (0, 1))
        self.assertTrue(move_ok)
        self.assertEqual(board.player_turn, 1)
        self.assertEqual(
            board.get_player_pawn(player_number=2, pawn_number=1).pos, (0, 2)
        )
        self.assertEqual(board.board[0][1], 1)

        # Current board:   Current pawns:
        # 0 0 0 0 0        _ _ _ _ _
        # 0 0 0 0 0        _ _ _ _ _
        # 0 0 0 0 0        2 _ _ _ _
        # 1 0 0 0 0        _ 4 3 _ _
        # 0 1 0 0 0        1 _ _ _ _

        # Pawn 3 try to move too far
        move_ok, reason = board.play_move(2, (1, 3), (2, 1))
        self.assertFalse(move_ok)
        self.assertEqual(reason, "It is not possible to move that far.")

        # Pawn 3 moves top left and builds down right
        move_ok, reason = board.play_move(2, (1, 2), (2, 1))
        self.assertTrue(move_ok)
        self.assertEqual(board.player_turn, 2)
        self.assertEqual(
            board.get_player_pawn(player_number=1, pawn_number=2).pos, (1, 2)
        )
        self.assertEqual(board.board[1][0], 1)

        # Current board:   Current pawns:
        # 0 0 0 0 0        _ _ _ _ _
        # 0 0 0 0 0        _ _ _ _ _
        # 0 0 0 0 0        2 3 _ _ _
        # 1 0 1 0 0        _ 4 _ _ _
        # 0 1 0 0 0        1 _ _ _ _

        # Pawn 4 moves tries to move top left but fails
        move_ok, reason = board.play_move(2, (0, 2), (0, 3))
        self.assertFalse(move_ok)
        self.assertEqual(reason, "It is not possible to move on another pawn.")
        move_ok, reason = board.play_move(2, (0, 2), None)
        self.assertFalse(move_ok)
        self.assertEqual(reason, "It is not possible to move on another pawn.")
        self.assertEqual(board.player_turn, 2)

        # Player 2 tries a bunch of invalid moves
        self.assertFalse(board.play_move(2, ("a", "b"), (1, -1))[0])
        self.assertFalse(board.play_move(2, (1, -1), ("a", "b"))[0])
        self.assertFalse(board.play_move(2, "test", (None, None))[0])
        self.assertFalse(board.play_move(2, (1, -1), "test")[0])
        self.assertFalse(board.play_move(2, None, None)[0])
        self.assertFalse(board.play_move(2, (None, None), (None, None))[0])
        self.assertFalse(board.play_move(2, (0, 0), (0, 0))[0])
        self.assertFalse(board.play_move(2, (1, 1), (0, 0))[0])
        self.assertFalse(board.play_move(2, (1, 1), (1, 0, 0))[0])
        self.assertEqual(board.player_turn, 2)

        # Pawn 4 moves down and try to build left but fails
        move_ok, reason = board.play_move(2, (1, 0), (0, 0))
        self.assertFalse(move_ok)
        self.assertEqual(reason, "It is not possible to build on another pawn.")
        self.assertEqual(board.player_turn, 2)
        # The pawn is not moved:
        self.assertEqual(board.pawns[3].pos, (1, 1))
        # Player 2 tries to place again but fails
        move_ok, reason = board.place_pawn((2, 2))
        self.assertFalse(move_ok)
        self.assertEqual(reason, "All the pawns have already been placed.")

        # Pawn 4 moves down and builds right
        move_ok, _ = board.play_move(2, (1, 0), (2, 0))
        self.assertTrue(move_ok)
        self.assertEqual(board.player_turn, 1)

        print(board)

        # Board so far:
        # _0 _0 _0 _0 _0
        # _0 _0 _0 _0 _0
        # 20 30 _0 _0 _0
        # _1 _0 _1 _0 _0
        # 10 41 _1 _0 _0

        # Pawn 1 has two possible move
        possible_moves = board.get_possible_movement_positions(
            board.get_player_pawn(1, 1)
        )
        self.assertEqual(len(possible_moves), 2)
        self.assertIn((0, 1), possible_moves)
        self.assertIn((1, 1), possible_moves)

        # Pawn 1 has two one possible build from his current position
        possible_builds = board.get_possible_building_positions(
            board.get_player_pawn(1, 1)
        )
        self.assertEqual(len(possible_builds), 2)
        self.assertIn((0, 1), possible_builds)
        self.assertIn((1, 1), possible_builds)

        # Tests that a valid move with an invalid build is not allowed
        # and that the pawn is not moved
        move_ok, reason = board.play_move(1, (0, 1), (0, 1))
        self.assertFalse(move_ok)
        self.assertEqual(reason, "It is not possible to build where you are standing.")
        self.assertEqual(board.player_turn, 1)
        self.assertEqual(board.pawns[0].pos, (0, 0))
        move_ok, reason = board.play_move(1, (0, 1), (0, 2))
        self.assertFalse(move_ok)
        self.assertEqual(reason, "It is not possible to build on another pawn.")
        self.assertEqual(board.player_turn, 1)
        self.assertEqual(board.pawns[0].pos, (0, 0))
        move_ok, reason = board.play_move(1, (1, 1), ("not a build", "position"))
        self.assertFalse(move_ok)
        self.assertIn("integers", reason)
        self.assertEqual(board.player_turn, 1)
        self.assertEqual(board.pawns[0].pos, (0, 0))
        move_ok, reason = board.play_move(1, (1, 1), "test")
        self.assertFalse(move_ok)
        self.assertIn("not a tuple", reason)
        self.assertEqual(board.player_turn, 1)
        self.assertEqual(board.pawns[0].pos, (0, 0))
        move_ok, reason = board.play_move(1, (1, 1), (2, 2, 2))
        self.assertFalse(move_ok)
        self.assertIn("not a coordinate", reason)
        self.assertEqual(board.player_turn, 1)
        self.assertEqual(board.pawns[0].pos, (0, 0))

        # Make every one stuck
        self.assertFalse(board.is_everyone_stuck())
        self.assertFalse(board.is_game_over())
        board.board[0][3] = 4
        board.board[0][1] = 4
        board.board[1][3] = 4
        board.board[2][2] = 4
        board.board[2][3] = 4
        board.board[1][1] = 4
        board.board[2][1] = 4
        board.board[2][0] = 4

        # _0 _0 _0 _0 _0
        # _4 _4 _4 _0 _0
        # 20 30 _4 _0 _0
        # _4 _4 _4 _0 _0
        # 10 41 _4 _0 _0

        self.assertTrue(board.is_everyone_stuck())
        self.assertTrue(board.is_game_over())

    def test_victory_conditions(self):
        board = Board(self.NB_PLAYERS)

        # Board goal:
        # 11 20 30 40 _0
        # _2 _0 _0 _0 _0
        # _2 _0 _0 _0 _0
        # _0 _0 _0 _0 _0
        # _0 _0 _0 _0 _0

        # ==== Pawns Positions ====
        self.assertTrue(board.place_pawn((0, 4))[0])
        self.assertTrue(board.place_pawn((1, 4))[0])
        self.assertTrue(board.place_pawn((2, 4))[0])
        self.assertTrue(board.place_pawn((3, 4))[0])

        # ==== Constructions ====
        board.board[0][4] = 1
        board.board[0][3] = 2
        board.board[0][2] = 2

        # ==== First move====
        self.assertTrue(board.play_move(1, (0, 3), (0, 2))[0])
        self.assertTrue(board.play_move(1, (1, 3), (1, 4))[0])
        self.assertTrue(board.play_move(2, (2, 3), (2, 4))[0])
        self.assertTrue(board.play_move(2, (3, 3), (3, 4))[0])

        self.assertFalse(board.is_game_over())
        self.assertFalse(board.is_everyone_stuck())
        self.assertEqual(board.winner_player_number, None)

        # ==== Second and finish move ====
        self.assertTrue(board.play_move(1, (0, 2), (None, "Test"))[0])
        self.assertTrue(board.is_game_over())
        self.assertEqual(board.winner_player_number, 1)

        self.assertFalse(board.is_everyone_stuck())

        # We can't play anymore
        self.assertFalse(board.play_move(1, (2, 2), (2, 1))[0])
        self.assertFalse(board.place_pawn((2, 2))[0])

        # Congratulation to the winner!
        print(board)

    def test_every_one_is_stuck_again(self):
        board = Board(self.NB_PLAYERS)

        # Board goal:
        # _0 20 31 40 _3
        # 12 _4 _3 _4 _2
        # _0 _0 _0 _0 _0
        # _0 _0 _0 _0 _0
        # _0 _0 _0 _0 _0

        # ==== Pawns Positions ====
        board.pawns[0].pos = (0, 3)
        board.pawns[1].pos = (1, 4)
        board.pawns[2].pos = (2, 4)
        board.pawns[3].pos = (3, 4)

        # ==== Constructions ====
        board.board[0][4] = 0
        board.board[1][4] = 0
        board.board[2][4] = 1
        board.board[3][4] = 0
        board.board[4][4] = 3

        board.board[0][3] = 2
        board.board[1][3] = 4
        board.board[2][3] = 3
        board.board[3][3] = 4
        board.board[4][3] = 2

        # First and last move
        self.assertFalse(board.is_game_over())
        self.assertFalse(board.is_everyone_stuck())
        self.assertEqual(board.winner_player_number, None)

        self.assertTrue(board.play_move(1, (0, 4), (0, 3))[0])

        # We can't play anymore
        self.assertTrue(board.is_game_over())
        self.assertTrue(board.is_everyone_stuck())
        self.assertEqual(board.winner_player_number, 1)  # The last player who played

        # What a waste of time

    def test_get_possible_movement_and_building_positions(self):
        board = Board(self.NB_PLAYERS)

        # At first, all positions are free
        all_possible_moves = board.get_possible_movement_and_building_positions(
            board.pawns[0]
        )
        self.assertEqual(len(all_possible_moves), 25)
        board.place_pawn((2, 2))

        # Pawn 1 has many possible moves
        all_possible_moves = board.get_possible_movement_and_building_positions(
            board.pawns[0]
        )
        self.assertGreater(len(all_possible_moves), 50)

        # Pawn 2 has one less placement
        all_possible_moves = board.get_possible_movement_and_building_positions(
            board.pawns[1]
        )
        self.assertEqual(len(all_possible_moves), 24)
        board.place_pawn((3, 2))
