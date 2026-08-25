from abc import abstractmethod

from santorinai.board import Board
from santorinai.pawn import Pawn


class Player:
    """
    A player of Santorini, has a name and can play a move given a board
    """

    def __init__(self, player_number: int, log_level=0) -> None:
        self.log_level = log_level
        self.player_number = player_number

    @abstractmethod
    def name(self):
        """
        The name of the player
        """

    @abstractmethod
    def place_pawn(self, board: Board, pawn: Pawn) -> tuple[int, int]:
        """
        Place a pawn given a board
        :param board: the board
        :param pawn: the pawn that needs to be placed
        :return: a position of the form (x, y)

        Return example: (2, 2) means that the player wants to place
        his pawn at the center of the board
        """

    @abstractmethod
    def play_move(self, board: Board) -> tuple[int, tuple[int, int], tuple[int, int]]:
        """
        Choose a pawn and play a move given a board
        :param board: the board
        :return: two positions of the form (x1, y1), (x2, y2)

        The first coordinate corresponds to the new position of the pawn
        The second coordinate corresponds to the position of the construction
        of the tower

        Return example: (2, 2), (2, 3) means that the player wants to move the
        pawn at center of the board and build a tower one tile above
        """
