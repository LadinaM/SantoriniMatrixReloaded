from time import sleep

from santorinai.board import Board
from santorinai.board_displayer.board_displayer import (
    close_window,
    init_window,
    update_board,
)
from santorinai.player import Player


class Tester:
    """
    Run the games with SantorinAI players, do statistics display the results
    """

    verbose_level = 2
    delay_between_moves = 0.0
    display_board = False

    def display_message(self, message, verbose_level=1):
        """
        Display a message if verbose is True

        Args:
            message (str): the message to display
        """
        if self.verbose_level >= verbose_level:
            print(message)

    def play_1v1(
        self,
        player1: Player,
        player2: Player,
        nb_games: int = 1,
        dic_win_lose_type=None,
    ):
        """
        Play a 1v1 game between player1 and player2

        Args:
            player1 (Player): the first player
            player2 (Player): the second player

        Returns:
            dict: the number of victories for each player
            dict: the different types of winning and loosing conditions
        """
        NB_PLAYERS = 2

        # Check if the players are objects of the Player class
        if player1 is None or not isinstance(player1, Player):
            raise TypeError("player1 should be an object of the Player class")
        if player2 is None or not isinstance(player2, Player):
            raise TypeError("player2 should be an object of the Player class")

        # Validate the names of the players
        player_names = [player1.name(), player2.name()]

        if type(player_names[0]) is not str or len(player_names[0]) == 0:
            raise ValueError("player1 should have a valid name")

        if type(player_names[1]) is not str or len(player_names[1]) == 0:
            raise ValueError("player2 should have a valid name")

        if player_names[0] == player_names[1]:
            raise ValueError("The players should have different names")

        # Initialize the number of victories
        nb_victories = {
            player1.name(): 0,
            player2.name(): 0,
        }

        # Initialize empty dic_win_lose_type in not passed
        if not dic_win_lose_type:
            dic_win_lose_type = {player1.name(): {}, player2.name(): {}}

        players = [player1, player2]

        # Initialize the window
        window = None
        if self.display_board:
            window = init_window([player1.name(), player2.name()])

        # Play the games
        for game_nb in range(1, nb_games + 1):
            self.display_message(f"Game {game_nb}", 1)

            # Initialize the board
            board = Board(NB_PLAYERS)

            # Placement the pawns
            for pawn_nb, current_pawn in enumerate(board.pawns):
                board_copy = board.copy()
                # If pawn_nb == 1, the player_nb is 0, if pawn_nb == 2, the
                # player_nb is 1, if pawn_nb == 3, the player_nb is 0, etc.
                player_nb = (pawn_nb) % NB_PLAYERS
                player = players[player_nb]

                # Ask the player where to place the pawn
                self.display_message(
                    f"Player '{player.name()}' is placing pawn {pawn_nb + 1}", 2
                )
                position_choice = player.place_pawn(board_copy, current_pawn)

                # Place the pawn
                success, reason = board.place_pawn(position_choice)

                if not success:
                    self.display_message(
                        f"   Pawn placed at an invalid position: {reason}", 1
                    )
                    self.display_message(f"   Player '{player.name()}' loses")
                    dic_win_lose_type[player.name()] = register_new_victory_type(
                        dic_win_lose_type[player.name()],
                        f"Pawn placed at an invalid position: {reason}",
                    )
                    nb_victories[player_names[(player_nb + 1) % NB_PLAYERS]] += 1
                    break

                self.display_message(f"   Pawn placed at position {position_choice}", 2)
                if self.display_board and window is not None:
                    update_board(window, board)
                sleep(self.delay_between_moves)

            # Play the game
            self.display_message("\nPlaying the game")
            while not board.is_game_over():
                current_player = players[board.player_turn - 1]
                # current_pawn = board.get_playing_pawn()
                # self.display_message(f"   Current pawn: {current_pawn}", 2)

                # Check if the player can move
                # if len(board.get_possible_movement_positions(current_pawn)) == 0:
                #     self.display_message("   The pawn cannot move", 2)
                #     board.next_turn()
                #     # We don't ask the player to move, we just skip his turn
                #     continue

                board_copy = board.copy()
                # current_pawn_copy = board_copy.get_playing_pawn()

                # Ask the player where to move the pawn
                # player = players[current_pawn.player_number - 1]
                self.display_message(
                    f"Player '{current_player.name()}' is moving a pawn", 2
                )
                pawn_nb, move_choice, build_choice = current_player.play_move(
                    board_copy
                )

                # Move the pawn
                success, reason = board.play_move(pawn_nb, move_choice, build_choice)

                if not success:
                    self.display_message(
                        f"   Pawn moved at an invalid position: {reason}", 1
                    )
                    self.display_message(f"   Player '{current_player.name()}' loses")
                    dic_win_lose_type[current_player.name()] = (
                        register_new_victory_type(
                            dic_win_lose_type[current_player.name()], reason
                        )
                    )

                    other_player_name_id = (board.player_turn - 1) % NB_PLAYERS
                    other_player_name = player_names[other_player_name_id]
                    nb_victories[other_player_name] += 1

                    break

                # Log the move details
                self.display_message(
                    f"   Pawn moved at position {move_choice}\
                      and built at position {build_choice}",
                    2,
                )
                self.display_message(board, 2)

                # Update the board display
                if window and self.display_board:
                    update_board(window, board)

                    # Sleep between moves
                    if self.delay_between_moves > 0:
                        sleep(self.delay_between_moves)

            # Game is over
            winner_number = board.winner_player_number
            if winner_number is None:
                self.display_message("Draw")
            else:
                winner_player_name = players[winner_number - 1].name()
                self.display_message(f"Player '{winner_player_name}' wins!")
                dic_win_lose_type[winner_player_name] = register_new_victory_type(
                    dic_win_lose_type[winner_player_name],
                    reason,
                )

                nb_victories[winner_player_name] += 1

        # Display the results
        print("\nResults:")
        print(
            f"Player {players[0].name()} won {nb_victories[players[0].name()]}\
 time{'s' if nb_victories[players[0].name()] != 1 else ''} ("
            + str(round(nb_victories[players[0].name()] / nb_games * 100, 2))
            + "%)"
        )
        print(
            f"Player {players[1].name()} won {nb_victories[players[1].name()]}\
 time{'s' if nb_victories[players[1].name()] != 1 else ''} ("
            + str(round(nb_victories[players[1].name()] / nb_games * 100, 2))
            + "%)"
        )

        # Close the window
        if self.display_board:
            close_window(window)

        return nb_victories, dic_win_lose_type


def register_new_victory_type(dic_win_lose_types, s_msg):
    """
    Function that registers types of winning and loosing conditions
    and keeps track on a counter for each type of already registered
    type
    Args:
        dic_win_lose_types:
        s_msg:

    Returns:

    """
    try:
        dic_win_lose_types[s_msg] += 1
    except KeyError:
        dic_win_lose_types[s_msg] = 1

    return dic_win_lose_types
