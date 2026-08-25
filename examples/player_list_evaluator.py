from santorinai.player_examples.basic_player import BasicPlayer
from santorinai.player_examples.first_choice_player import FirstChoicePlayer
from santorinai.player_examples.random_player import RandomPlayer
from santorinai.tester import Tester

# This script is used to compare the performance of a list of players.
# It will display a table with the results of each player against each other player.

players_classes = [
    BasicPlayer,
    RandomPlayer,
    FirstChoicePlayer,
]

# Init the tester
tester = Tester()
tester.verbose_level = 0
# Verbose level:
# 0: no output,
# 1: Each game results
# 2: Each move results

# tester.delay_between_moves = 0.5  # Delay between each move in seconds
# tester.display_board = True  # Display a graphical view of the board in a window

nb_games = 1000
results = {}  # We will count the number of victories for each player

# Initialize global victory type evaluator
dic_global_win_lose_type = {}

# Match all combinations of players
for i, player1_class in enumerate(players_classes):
    # Get the name of the player
    player1_name = player1_class(i).name()
    results[player1_name] = {}

    for j, player2_class in enumerate(players_classes):
        if i == j:
            continue

        # Init the players
        p1 = player1_class(1)
        p2 = player2_class(2)

        # Initialize victory type evaluator dic
        dic_win_lose_type = {p1.name(): {}, p2.name(): {}}

        # Get the name of the player 2
        player2_name = p2.name()
        results[player1_name][player2_name] = 0

        print(f"\n\nPlaying {player1_name} vs {player2_name}:")

        # Play 100 games
        victories_number, dic_global_win_lose_type[f"{p1.name()}vs{p2.name()}"] = (
            tester.play_1v1(
                p1, p2, nb_games=nb_games, dic_win_lose_type=dic_win_lose_type
            )
        )

        results[player1_name][player2_name] = victories_number[player1_name]

print(f"dic_global_win_lose_type = \n{dic_global_win_lose_type}")

print()
print("Results:")
print(results)
print()

# Display the results in a table
players = list(results.keys())

num_players = len(players)

# Create the header row
header = ["Players"]
for player in players:
    header.append("p2. " + player)

# Create the separator row
separator = ["---"] * (num_players + 1)

# Create the data rows
rows = []
for i in range(num_players):
    row = ["p1. " + players[i]]
    for j in range(num_players):
        if i != j:
            player1 = players[i]
            player2 = players[j]
            row.append(
                str(int((results[player1].get(player2, "") / nb_games) * 100)) + "%"
            )
        else:
            row.append("-")
    rows.append(row)

# Combine the header, separator, and data rows
table = [header, separator] + rows

# Convert the table to Markdown format
markdown_table = "\n".join(["|".join(row) for row in table])
print(markdown_table)


# Display winning rates
winning_rates = {}

for player, opponents in results.items():
    total_wins = sum(opponents.values())
    winning_rate = total_wins / (nb_games * len(opponents))
    winning_rates[player] = winning_rate

print("\nGlobal Winning Rates:")
for player, winning_rate in winning_rates.items():
    print(f" - {player}: {winning_rate:.2%}")
