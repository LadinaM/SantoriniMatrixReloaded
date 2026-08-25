from santorinai.board import Board
from santorinai.pawn import Pawn
from santorinai.player import Player


class FirstChoicePlayer(Player):
    """
    A player that places his pawns and moves them at the first possible position
    """

    def __init__(self, player_number, log_level=0) -> None:
        super().__init__(player_number, log_level)

    def name(self):
        return "Firsty First"

    def place_pawn(self, board: Board, pawn: Pawn):
        available_positions = board.get_possible_movement_positions(pawn)
        my_choice = available_positions[0]
        return my_choice

    def play_move(self, board: Board):
        # Choose always first pawn
        l_pawns = board.get_player_pawns(self.player_number)
        pawn = l_pawns[0]

        # Get movement positions
        available_move_positions = board.get_possible_movement_positions(pawn)
        if len(available_move_positions) == 0:
            # The pawn cannot move
            return pawn.order, None, None

        my_move_choice = available_move_positions[0]

        # Simulate the move (Need to use pawn copy since returned pawn will be moved)
        pawn.move(my_move_choice)

        # Get construction positions
        available_build_positions = board.get_possible_building_positions(pawn)
        if len(available_build_positions) == 0:
            # The pawn cannot build
            raise RuntimeError("Pawn cannot build")

        # Their is always at least one position available
        my_build_choice = available_build_positions[0]

        return pawn.order, my_move_choice, my_build_choice
