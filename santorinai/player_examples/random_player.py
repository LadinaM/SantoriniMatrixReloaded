from random import choice

from santorinai import Board, Pawn, Player


class RandomPlayer(Player):
    """
    A player that places his pawns and moves them randomly
    """

    def __init__(self, player_number, log_level=0) -> None:
        super().__init__(player_number, log_level)

    def name(self):
        return "Randy Random"

    def place_pawn(self, board: Board, pawn: Pawn):
        available_positions = board.get_possible_movement_positions(pawn)
        my_choice = choice(available_positions)
        return my_choice

    def play_move(self, board: Board):
        # List all possible moves
        all_possible_pawns_moves = []
        for pawn in board.get_player_pawns(self.player_number):
            pawn_moves = board.get_possible_movement_and_building_positions(pawn)
            # Add the pawn number to the possible moves
            all_possible_pawns_moves += [
                (pawn.order, move, build) for move, build in pawn_moves
            ]

        my_move_choice = choice(all_possible_pawns_moves)

        return my_move_choice
