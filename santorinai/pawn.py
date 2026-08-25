class Pawn:
    def __init__(self, number: int, order: int, player_number: int):
        """
        Initialize a pawn
        :param number: the number of the pawn (1 to 6 depending on the number of pawns)
        :param order: the order of the pawn (1 or 2)
        :param player_number: the player number of the pawn (1, 2 or 3
            depending on players number)
        """

        # Validate the input
        if not 1 <= number <= 6:
            raise ValueError("The number of the pawn should be between 1 and 6")

        if order not in [1, 2]:
            raise ValueError(f"The order of the pawn should be 1 or 2, not {order}")

        if player_number not in [1, 2, 3]:
            raise ValueError("The player number of the pawn should be 1, 2 or 3")

        self.number = number  # 1 to 6 depending on the number of pawns
        self.order = order  # 1 or 2
        self.player_number = player_number  # 1, 2 or 3 depending on players number
        self.pos: tuple[int | None, int | None] = (None, None)

    def move(self, new_pos: tuple[int | None, int | None]):
        """
        Move the pawn to the new position
        :param new_pos: the new position of the pawn
        """
        self.pos = new_pos

    def copy(self) -> Pawn:
        """
        Return a copy of the pawn
        :return: a copy of the pawn
        """
        new_pawn = Pawn(self.number, self.order, self.player_number)
        new_pawn.pos = self.pos
        return new_pawn

    def __repr__(self):
        return (
            f"pawn n°{self.order} of player {self.player_number} at position {self.pos}"
        )
