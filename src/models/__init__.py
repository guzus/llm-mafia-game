"""Models package for the Mafia game."""

from .enums import Role, GamePhase, Color
from .player import Player
from .templates import (
    GAME_RULES, get_thinking_tags, PROMPT_TEMPLATES, 
    ACTION_PATTERNS, VOTE_PATTERNS, CONFIRMATION_VOTE_PATTERNS,
    PLAYER_NAMES
)

__all__ = [
    'Role', 'GamePhase', 'Color', 'Player',
    'GAME_RULES', 'get_thinking_tags', 'PROMPT_TEMPLATES',
    'ACTION_PATTERNS', 'VOTE_PATTERNS', 'CONFIRMATION_VOTE_PATTERNS',
    'PLAYER_NAMES'
]