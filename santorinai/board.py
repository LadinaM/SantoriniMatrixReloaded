from santorinai.pawn import Pawn


class Board:
    """
    Represents the game board for the Santorini game.

    Attributes:
        pawns (list): A list of pawn objects representing the pawns on the board.
        board_size (int): The size of the square game board.
        board (list): A 2D list representing the current state of the board.
        turn_number (int): The current turn number.
        winner_player_number (int): The player number of the winning player, if any.

    Board values:
        A 5x5 2D list representing the current state of the board:
        - 0: Empty space
        - 1: Tower level 1
        - 2: Tower level 2
        - 3: Tower level 3
        - 4: Terminated tower

    Methods:
        <list of methods>

    """

    def __init__(self, number_of_players: int):
        """
        Initializes a new instance of the Board class.

        Args:
            number_of_players (int): The number of players in the game.
        """

        # Create the pawns for each player
        self.pawns: list[Pawn] = []
        self.nb_players = number_of_players
        self.nb_pawns = number_of_players * 2

        # For 2 player games:
        # - Player 1 has pawns 1, 3
        # - Player 2 has pawns 2, 4

        # For 3 player games:
        # - Player 1 has pawns 1, 4
        # - Player 2 has pawns 2, 5
        # - Player 3 has pawns 3, 6

        for pawn_number in range(1, self.nb_pawns + 1):
            player_number = (pawn_number - 1) % number_of_players + 1
            pawn_order = (pawn_number - 1) // number_of_players + 1  # 1 or 2
            self.pawns.append(Pawn(pawn_number, pawn_order, player_number))

        # Initialize the board
        self.board_size = 5
        self.board = [
            [0 for _ in range(self.board_size)] for _ in range(self.board_size)
        ]

        # Board values:
        # 0 = empty
        # 1 = tower level 1
        # 2 = tower level 2
        # 3 = tower level 3
        # 4 = terminated tower

        # Other board values:
        self.winner_player_number = None
        self.turn_number = 1
        self.player_turn = 1

    def is_move_possible(
        self,
        start_pos: tuple[int | None, int | None],
        end_pos: tuple[int | None, int | None],
    ) -> tuple[bool, str]:
        """
        Checks if a move from the start position to the end position is possible.

        Args:
            start_pos (tuple): The starting position [x, y] of the pawn.
            end_pos (tuple): The ending position [x, y] of the pawn.

        Returns:
            bool: True if the move is possible, False otherwise.
            str: A string describing why the move is not possible.
        """
        # Check if the start and end positions are within the board bounds
        if not self.is_position_within_board(start_pos):
            return False, "It is not possible to move from outside the board."
        if not self.is_position_within_board(end_pos):
            return False, "It is not possible to move outside the board: " + str(
                end_pos
            )

        # We can't move to the same position
        if start_pos == end_pos:
            return False, "It is not possible to move to the same position."

        assert start_pos[0] is not None and start_pos[1] is not None
        assert end_pos[0] is not None and end_pos[1] is not None
        start_level = self.board[start_pos[0]][start_pos[1]]
        end_level = self.board[end_pos[0]][end_pos[1]]

        # Check if the end position is not terminated
        if end_level == 4:
            return False, "It is not possible to move on a terminated tower."

        # Check if the end position is not to high
        if end_level - start_level > 1:
            return False, "It is not possible to move two levels in one move."

        # Check if the end position is adjacent to the start position
        if not self.is_position_adjacent(start_pos, end_pos):
            return False, "It is not possible to move that far."

        # Check if the end position is not occupied by another pawn
        if self.is_pawn_on_position(end_pos):
            return False, "It is not possible to move on another pawn."

        return True, "The move is possible."

    def is_position_within_board(self, position: tuple[int | None, int | None]) -> bool:
        """
        Checks if a position is within the bounds of the game board.

        Args:
            position (tuple): The position [x, y] to check.

        Returns:
            bool: True if the position is within the board bounds, False otherwise.
        """
        x, y = position
        if x is None or y is None:
            return False
        return 0 <= x < self.board_size and 0 <= y < self.board_size

    def is_position_adjacent(
        self,
        position1: tuple[int | None, int | None],
        position2: tuple[int | None, int | None],
    ) -> bool:
        """
        Checks if two positions are adjacent to each other.

        Args:
            position1 (tuple): The first position [x1, y1].
            position2 (tuple): The second position [x2, y2].

        Returns:
            bool: True if the positions are adjacent, False otherwise.
        """
        x1, y1 = position1
        x2, y2 = position2
        if x1 is None or y1 is None or x2 is None or y2 is None:
            return False
        return abs(x1 - x2) <= 1 and abs(y1 - y2) <= 1 and (x1 != x2 or y1 != y2)

    def is_pawn_on_position(self, position: tuple[int | None, int | None]) -> bool:
        """
        Checks if a pawn is on a position.

        Args:
            position (tuple): The position [x, y] to check.

        Returns:
            bool: True if a pawn is on the position, False otherwise.
        """
        for pawn in self.pawns:
            if pawn.pos == position:
                return True
        return False

    def is_build_possible(
        self,
        builder_position: tuple[int | None, int | None],
        build_position: tuple[int | None, int | None],
    ) -> tuple[bool, str]:
        """
        Checks if a build from the builder position is possible.

        Args:
            builder_position (tuple): The position [x, y] of the builder pawn.
            build_position (tuple): The position [x, y] of the build.

        Returns:
            bool: True if the build is possible, False otherwise.
            str: A string describing why the build is not possible.
        """
        # Check if the builder position is within the board bounds
        if not self.is_position_within_board(builder_position):
            return False, "It is not possible to build from outside the board."

        # Check if the build position is within the board bounds
        if not self.is_position_within_board(build_position):
            return False, "It is not possible to build outside the board."

        # We can't build on the same position
        if builder_position == build_position:
            return False, "It is not possible to build where you are standing."

        assert build_position[0] is not None and build_position[1] is not None
        # Check if the build position is not terminated
        if self.board[build_position[0]][build_position[1]] == 4:
            return False, "It is not possible to build on a terminated tower."

        # Check if the build position is adjacent to the builder position
        if not self.is_position_adjacent(builder_position, build_position):
            return False, "It is not possible to build that far."

        # Check if the build position is not occupied by another pawn
        if self.is_pawn_on_position(build_position):
            return False, "It is not possible to build on another pawn."

        return True, "The build is possible."

    def get_player_pawns(self, player_number: int) -> list[Pawn]:
        """
        Gets the pawns of a player.

        Args:
            player_number (int): The number of the player

        Returns:
            Pawn: The pawn of the current player.
        """
        pawns = []
        for pawn in self.pawns:
            if pawn.player_number == player_number:
                pawns.append(pawn)

        return pawns

    def get_player_pawn(self, player_number: int, pawn_number: int) -> Pawn:
        """
        Gets a pawn of a player.

        Args:
            player_number (int): The number of the player
            pawn_number (int): The number of the pawn to retrieve, 1 or 2.

        Returns:
            Pawn: The pawn of the current player.
        """

        return self.get_player_pawns(player_number)[pawn_number - 1]

    def get_playing_pawn(self, pawn_number: int) -> Pawn | None:
        """
        Gets the pawns of the current player.

        Args:
            pawn_number int: The number of pawns to retrieve, 1 or 2.

        Returns:
            Pawn: The selected pawn of the playing player,
            None if the given pawn number is invalid.
        """

        # Validate the input
        if pawn_number < 1 or pawn_number > 2:
            return None

        # Get the playing pawn
        return self.get_player_pawns(self.player_turn)[pawn_number - 1]

    def get_first_unplaced_player_pawn(self, player_number: int) -> Pawn | None:
        """
        Gets the first unplaced pawn of a player.

        Args:
            player_number (int): The player number.

        Returns:
            Pawn: The first unplaced pawn of the player, or None if all are placed.
        """
        for pawn in self.pawns:
            if pawn.player_number == player_number and (
                pawn.pos[0] is None or pawn.pos[1] is None
            ):
                return pawn
        return None

    def get_possible_movement_positions(self, pawn: Pawn) -> list[tuple[int, int]]:
        """
        Gets all the possible moves for a given pawn.

        Args:
            pawn (Pawn): The pawn for which to get the possible moves.

        Returns:
            list: A list of all the possible moves for the given pawn.
        """
        possible_moves = []

        # If pawn position is None, it means it has not been placed yet
        # Every position is possible except the ones occupied by other pawns
        # and the ones where tower are terminated
        px, py = pawn.pos
        if px is None or py is None:
            for x in range(self.board_size):
                for y in range(self.board_size):
                    if self.board[x][y] != 4 and not self.is_pawn_on_position((x, y)):
                        possible_moves.append((x, y))
            return possible_moves

        # Get all the possible moves from the 8 positions around the pawn
        for x in range(-1, 2):
            for y in range(-1, 2):
                # We can't move on the same position
                if x == 0 and y == 0:
                    continue

                new_pawn_pos = (px + x, py + y)

                # Check if the move is possible
                move_possible, _ = self.is_move_possible(pawn.pos, new_pawn_pos)
                if move_possible:
                    possible_moves.append(new_pawn_pos)

        return possible_moves

    def get_possible_building_positions(self, pawn: Pawn) -> list[tuple[int, int]]:
        """
        Gets all the possible builds for a given pawn, supposing it has already moved.

        Args:
            pawn (Pawn): The pawn for which to get the possible builds.

        Returns:
            list: A list of all the possible builds for the given pawn.
        """

        px, py = pawn.pos
        if px is None or py is None:
            return []

        possible_builds = []

        # Get all the possible builds
        for x in range(-1, 2):
            for y in range(-1, 2):
                if x == 0 and y == 0:
                    continue
                build_pos = (px + x, py + y)
                build_possible, _ = self.is_build_possible(pawn.pos, build_pos)
                if build_possible:
                    possible_builds.append(build_pos)

        return possible_builds

    def get_possible_movement_and_building_positions(self, pawn: Pawn):
        """
        Gets all the possible moves and builds for a given pawn.
        :param pawn: The pawn for which to get the possible moves and builds.
        :return: A list of all the possible moves and builds for the given pawn.
        [(move_position, build_position), ...]
        """

        if pawn.pos[0] is None or pawn.pos[1] is None:
            # Pawn not placed yet
            possible_spawn_positions = self.get_possible_movement_positions(pawn)
            return [(position, None) for position in possible_spawn_positions]

        possible_moves_and_builds = []
        original_position = (pawn.pos[0], pawn.pos[1])
        possible_moves = self.get_possible_movement_positions(pawn)

        for move in possible_moves:
            pawn.move(move)
            possible_builds = self.get_possible_building_positions(pawn)
            for build in possible_builds:
                possible_moves_and_builds.append((move, build))

        # Move the pawn back to its original position
        pawn.move(original_position)

        return possible_moves_and_builds

    def place_pawn(self, position: tuple[int, int]) -> tuple[bool, str]:
        """
        Places a pawn on the board.

        Args:
            position (tuple): The position [x, y] to place the pawn.

        Returns:
            bool: True if the pawn was placed, False otherwise.
            str: A string describing why the pawn was not placed.
        """
        # Check if the game is over
        if self.is_game_over():
            return False, "The game is over."

        # Check if the pawn has already been placed
        unplaced_pawns = self.get_first_unplaced_player_pawn(self.player_turn)
        if unplaced_pawns is None:
            return False, "All the pawns have already been placed."

        # Check input
        ok, msg = self.is_position_valid(position)
        if not ok:
            return False, msg

        # Check if the position is not occupied by another pawn
        if self.is_pawn_on_position(position):
            return False, "The position is already occupied by another pawn."

        # Place the pawn
        unplaced_pawns.pos = position

        # Next player's turn
        self.next_turn()

        return True, "The pawn was placed."

    def play_move(
        self,
        pawn_number: object,
        move_position: object,
        build_position: object,
    ) -> tuple[bool, str]:
        """
        Plays a move on the board with the chosen playing pawn.

        Args:
            pawn_number (int): Number of the pawn to play with (1 or 2).
            move_position (tuple): The position (x, y) to move the pawn to.
            build_position (tuple): The position (x, y) to build a tower on.

        Returns:
            bool: True if the move was played, False otherwise.
            str: A string describing why the move was not played.
        """

        # Validate the input
        if not isinstance(pawn_number, int):
            return False, "The pawn number is not an integer."

        if pawn_number < 1 or pawn_number > 2:
            return False, "The pawn number is invalid (must be 1 or 2)."

        # Check if all pawn are placed
        unplaced_pawns = self.get_first_unplaced_player_pawn(self.player_turn)
        if unplaced_pawns is not None:
            return False, "All the pawns have not been placed yet."

        # Get the moving pawn
        pawn = self.get_playing_pawn(pawn_number)
        if pawn is None:
            return False, "The pawn number is invalid (must be 1 or 2)."

        # Check if the game is over
        if self.is_game_over():
            return False, "The game is over."

        # Check if there is any possible move
        possible_moves = self.get_possible_movement_positions(pawn)
        if len(possible_moves) == 0:
            # The selected pawn is stuck
            return False, "The selected pawn is stuck."

        # === MOVE ===
        # Check the input
        position_valid, reason = self.is_position_valid(move_position)
        if not position_valid:
            return False, reason
        assert isinstance(move_position, tuple)
        move_pos = (int(move_position[0]), int(move_position[1]))

        # Check if the move is possible
        move_possible, reason = self.is_move_possible(pawn.pos, move_pos)
        if not move_possible:
            return False, reason

        # Apply the move
        initial_pos = pawn.pos
        pawn.move(move_pos)

        # Check if the tower is terminated
        if self.board[move_pos[0]][move_pos[1]] == 3:
            self.winner_player_number = pawn.player_number
            return True, "The player pawn reached the top of a tower."

        # === BUILD ===
        # Check the input
        position_valid, reason = self.is_position_valid(build_position)
        if not position_valid:
            # Reverse the move
            pawn.move(initial_pos)
            return False, reason
        assert isinstance(build_position, tuple)
        build_pos = (int(build_position[0]), int(build_position[1]))

        # No need to check possible build, it is always possible to build after a move
        # (we can always build on the initial position)

        # Check if the build is possible
        build_possible, reason = self.is_build_possible(pawn.pos, build_pos)

        if not build_possible:
            # The move was played but the build is not possible
            # Reverse the move
            pawn.move(initial_pos)
            return False, reason

        # Build the tower
        self.board[build_pos[0]][build_pos[1]] += 1

        if self.is_everyone_stuck():
            self.winner_player_number = pawn.player_number
            return True, "No one can play, the game is over."

        # Change the turn
        self.next_turn()

        # Check if the next player is stuck
        next_player_pawns = self.get_player_pawns(self.player_turn)
        next_player_stuck = True
        for p in next_player_pawns:
            if len(self.get_possible_movement_positions(p)) > 0:
                next_player_stuck = False
                break

        if next_player_stuck:
            self.winner_player_number = pawn.player_number
            return True, "The next player is stuck, the game is over."

        return True, "The move was played."

    def is_position_valid(self, pos: object) -> tuple[bool, str]:
        """
        Checks if a pos is valid.

        Args:
            pos (tuple): The position to check.

        Returns:
            bool: True if the position is valid, False otherwise.
            str: A string describing why the pos is not valid.
        """

        # Check if the pos is a tuple
        if not isinstance(pos, tuple):
            return False, f"The position is not a tuple, but a {type(pos)}."

        # Check if the pos is a 2D pos
        if len(pos) != 2:
            return (
                False,
                f"The position is not a coordinate, it but has {len(pos)} dim.",
            )

        if not isinstance(pos[0], int) or not isinstance(pos[1], int):
            return False, f"Not all the coordinates are integers: {pos}."

        # Check if the pos is in the board bounds
        if not self.is_position_within_board(pos):
            return False, "The position is not within the board bounds."

        return True, "The position is valid."

    def is_game_over(self) -> bool:
        """
        Checks if the game is over.

        Returns:
            bool: True if the game is over, False otherwise.
        """
        if self.winner_player_number is not None:
            return True

        return self.is_everyone_stuck()

    def is_everyone_stuck(self):
        """
        Checks if everyone is stuck.

        Returns:
            bool: True if everyone is stuck, False otherwise.
        """
        for pawn in self.pawns:
            if len(self.get_possible_movement_positions(pawn)) > 0:
                return False

        return True

    def next_turn(self):
        """
        Changes the turn.
        """
        self.player_turn += 1
        if self.player_turn > self.nb_players:
            self.player_turn = 1

        self.turn_number += 1

    def copy(self) -> Board:
        """
        Creates a copy of the board.

        Returns:
            Board: A copy of the board.
        """
        # Create a new board
        board_copy = Board(self.nb_players)

        # Copy the board
        for x in range(self.board_size):
            for y in range(self.board_size):
                board_copy.board[x][y] = self.board[x][y]

        # Copy the pawns
        board_copy.pawns = [pawn.copy() for pawn in self.pawns]

        # Copy the other attributes
        board_copy.turn_number = self.turn_number
        board_copy.winner_player_number = self.winner_player_number

        return board_copy

    def __repr__(self) -> str:
        """
        Returns a string representation of the board.

        Returns:
            str: A string representation of the board.
        """
        output = "\n"

        for y in range(self.board_size - 1, -1, -1):
            for x in range(self.board_size):
                # Check if there is a pawn at this position
                pawn = None
                for p in self.pawns:
                    if p.pos == (x, y):
                        pawn = p
                        break
                pawn_number = str(pawn.number) if pawn is not None else "_"
                output += pawn_number + str(self.board[x][y]) + " "
            output += "\n"

        return output
