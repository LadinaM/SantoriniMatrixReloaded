"""
The Santorini engine, our agents and the training environment.

Nothing in here needs a screen, so it also runs on servers and Colab.
"""

from .core import NUM_ACTIONS as NUM_ACTIONS
from .core import GameState as GameState
from .match import play_game as play_game
from .match import play_match as play_match
