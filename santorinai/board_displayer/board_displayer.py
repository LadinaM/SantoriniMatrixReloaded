import PySimpleGUI as sg

from santorinai.board import Board

# Board display util
# Used to display a game board live
# Provide a function to initialize the window
# Provide a function that takes and display a game board
# Provide a function to close the window

# A game board format:
# 5x5 tiles in a D2 array:
# 0: empty
# 1: tower level 1
# 2: tower level 2
# 3: tower level 3
# 4: terminated tower

# A list of pawns with a number and a pos.

sg.theme("Dark Blue 3")
SIZE = 5

pawns_colors = {
    1: "grey",
    2: "blue",
    3: "white",
}

SIZE_X = 800
SIZE_Y = 300
TILE_SIZE = SIZE_X / 5


def init_window(player_names):
    tile = player_names[0]
    for player_name in player_names[1:]:
        tile += f" VS {player_name} "

    layout = [
        [sg.Text(tile, font=("Helvetica", 20), justification="center")],
        [
            sg.Graph(
                (SIZE_X, SIZE_Y + 100),
                (0, 0),
                (SIZE_X, SIZE_Y + 100),
                key="-GRAPH-",
                change_submits=True,
            )
        ],
    ]
    window = sg.Window("Game Board", layout, finalize=True)
    return window


def draw_isometric_cube(
    window: sg.Window, x, y, size, cube_heigth, color, line_color, line_width
):
    """
    Draw an isometric cube on the given PySimpleGUI window.
    :param window: The PySimpleGUI window object to draw on.
    :param x: The x-coordinate of the cube.
    :param y: The y-coordinate of the cube.
    :param size: The size of the cube.
    :param color: The fill color of the cube.
    :param line_color: The color of the cube's outline.
    """
    graph = window["-GRAPH-"]

    if graph is None:
        return

    ratio = SIZE_X / SIZE_Y

    AY = y + size / ratio
    B2Y = y - size / ratio
    B1Y = B3Y = y
    C2Y = B2Y - cube_heigth
    C1Y = C3Y = B1Y - cube_heigth

    AX = B2X = C2X = x
    B1X = C1X = x - size
    B3X = C3X = x + size

    graph.draw_polygon(
        [
            (B1X, B1Y),
            (B2X, B2Y),
            (C2X, C2Y),
            (C1X, C1Y),
        ],
        line_color=line_color,
        fill_color=color,
        line_width=line_width,
    )
    graph.draw_polygon(
        [
            (B3X, B3Y),
            (B2X, B2Y),
            (C2X, C2Y),
            (C3X, C3Y),
        ],
        line_color=line_color,
        fill_color=color,
        line_width=line_width,
    )
    graph.draw_polygon(
        [
            (B1X, B1Y),
            (B2X, B2Y),
            (B3X, B3Y),
            (AX, AY),
        ],
        line_color=line_color,
        fill_color=color,
        line_width=line_width,
    )


def update_board(window: sg.Window, board: Board):
    graph = window["-GRAPH-"]
    graph.erase()

    # Draw the board plane
    graph.draw_polygon(
        (
            (-10, SIZE_Y / 2),
            (SIZE_X / 2, -10),
            (10 + SIZE_X, SIZE_Y / 2),
            (SIZE_X / 2, SIZE_Y + 5),
        ),
        line_color="black",
        fill_color="white",
        line_width=0,
    )

    # Board
    for i in range(SIZE - 1, -1, -1):
        for j in range(SIZE - 1, -1, -1):
            level = board.board[i][j]

            x = (j - i) * TILE_SIZE / 2 + SIZE_X / 2
            y = (j + i) * TILE_SIZE / 5.2 + 25

            if level >= 0:
                color = "light grey"
                line_width = 2
                line_color = "black"
                cube_size = TILE_SIZE / 2 - 10
                cube_heigth = 0

            draw_isometric_cube(
                window, x, y, cube_size, cube_heigth, color, line_color, line_width
            )

            if level >= 1:
                color = "#f0f0f0"
                line_width = 2
                # line_color = "dark grey"
                line_color = "black"
                cube_size = TILE_SIZE / 2 - 25
                cube_heigth = TILE_SIZE / 5
                y += cube_heigth

            draw_isometric_cube(
                window, x, y, cube_size, cube_heigth, color, line_color, line_width
            )
            if level >= 2:
                color = "#d0d0d0"
                line_width = 2
                line_color = "black"
                cube_size = TILE_SIZE / 2 - 30
                cube_heigth = TILE_SIZE / 6
                y += cube_heigth

            draw_isometric_cube(
                window, x, y, cube_size, cube_heigth, color, line_color, line_width
            )
            if level >= 3:
                color = "#b0b0b0"
                line_width = 2
                line_color = "black"
                cube_size = TILE_SIZE / 2 - 35
                cube_heigth = TILE_SIZE / 8
                y += cube_heigth

            draw_isometric_cube(
                window, x, y, cube_size, cube_heigth, color, line_color, line_width
            )
            if level >= 4:
                color = "blue"
                line_width = 2
                line_color = "black"
                cube_size = TILE_SIZE / 2 - 45
                cube_heigth = TILE_SIZE / 10
                y += cube_heigth

            draw_isometric_cube(
                window, x, y, cube_size, cube_heigth, color, line_color, line_width
            )

            # Pawns
            for pawn in board.pawns:
                px, py = pawn.pos
                if px is None or py is None:
                    continue

                if (px, py) != (i, j):
                    continue

                level = board.board[px][py]
                PAWN_SIZE = 50
                x_pos = (py - px) * TILE_SIZE / 2 + SIZE_X / 2
                y_pos = (py + px) * TILE_SIZE / 5.2 + cube_heigth * level + PAWN_SIZE

                color = pawns_colors[pawn.player_number]
                line_width = 2
                line_color = "black"

                # Draw the pawn's shadow
                graph.DrawOval(
                    (x_pos - 14, y_pos - PAWN_SIZE / 2 - 2),
                    (x_pos + 14, y_pos - PAWN_SIZE / 2 + 8),
                    fill_color="black",
                )
                # Draw the pawn
                graph.DrawOval(
                    (x_pos - 14, y_pos - PAWN_SIZE / 2),
                    (x_pos + 14, y_pos + PAWN_SIZE / 2),
                    line_color=line_color,
                    fill_color=color,
                    line_width=line_width,
                )

                # Draw the pawn's number
                graph.DrawText(
                    pawn.number,
                    (x_pos, y_pos - 3),
                    font="Courier 15",
                    color="white",
                )

    event, _values = window.read(timeout=10)
    return event == sg.WIN_CLOSED


def close_window(window):
    window.close()


if __name__ == "__main__":
    board = Board(2)
    window = init_window(["Player 1", "Player 2"])
    while True:
        should_exit = update_board(window, board)
        if should_exit:
            break
    close_window(window)
