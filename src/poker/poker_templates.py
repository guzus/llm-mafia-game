"""
Poker game templates and constants for the LLM Poker Game.
This file contains all the templates, patterns, and constants used in the game.
"""

import re
from enum import Enum


class PokerHand(Enum):
    """Enum for poker hand rankings."""

    HIGH_CARD = "High Card"
    PAIR = "Pair"
    TWO_PAIR = "Two Pair"
    THREE_OF_A_KIND = "Three of a Kind"
    STRAIGHT = "Straight"
    FLUSH = "Flush"
    FULL_HOUSE = "Full House"
    FOUR_OF_A_KIND = "Four of a Kind"
    STRAIGHT_FLUSH = "Straight Flush"
    ROYAL_FLUSH = "Royal Flush"


class PokerAction(Enum):
    """Enum for poker actions."""

    FOLD = "fold"
    CHECK = "check"
    CALL = "call"
    BET = "bet"
    RAISE = "raise"
    ALL_IN = "all-in"


# Card suits and values
SUITS = ["♠", "♥", "♦", "♣"]
VALUES = ["2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K", "A"]

# Constants for game rules by language
GAME_RULES = {
    "English": """
POKER RULES (Texas Hold'em):
- Each player is dealt 2 private cards (hole cards)
- 5 community cards are dealt face up in the middle
- Players make the best 5-card hand using any combination of their 2 hole cards and the 5 community cards
- Betting rounds: pre-flop (after hole cards), flop (first 3 community cards), turn (4th card), river (5th card)
- Actions: fold (give up hand), check (pass), call (match current bet), bet/raise (increase bet), all-in (bet all chips)
- Hand rankings (lowest to highest): High Card, Pair, Two Pair, Three of a Kind, Straight, Flush, Full House, Four of a Kind, Straight Flush, Royal Flush
"""
}

# Constants for prompt templates
PROMPT_TEMPLATES = {
    "English": {
        "POKER_PLAYER": """
You are {model_name}, playing in a Texas Hold'em poker game. 

{game_rules}

GAME STATE:
- Your hole cards: {hole_cards}
- Community cards: {community_cards}
- Your chips: {chips}
- Current pot: {pot}
- Current bet to call: {current_bet}
- Your position: {position}
- Players remaining in hand: {active_players}
- Players and their chip counts: {player_chips}
- Previous actions this round: {round_actions}
- Previous rounds: {previous_rounds}

{thinking_tag}

Based on your cards, the community cards, and the actions of other players, decide your next move.
Respond with one of these actions:
- FOLD: Give up your hand and forfeit any chance at the pot
- CHECK: Pass the action to the next player (only if there's no bet to call)
- CALL: Match the current bet
- BET [amount]: Place a bet (if no one has bet yet)
- RAISE [amount]: Increase the current bet
- ALL-IN: Bet all your remaining chips

Your response:
"""
    }
}

# Thinking tags for internal reasoning
THINKING_TAGS = {
    "English": """
THINKING (not shown to other players):
Consider your hand strength, position, pot odds, and the behavior of other players.
Analyze your chances of winning and the expected value of each action.
"""
}

# Patterns for parsing player actions
ACTION_PATTERNS = {
    "English": {
        PokerAction.FOLD: re.compile(
            r"(?i)(?:ACTION\s*:|I(?:'ll| will))?\s*FOLD", re.IGNORECASE
        ),
        PokerAction.CHECK: re.compile(
            r"(?i)(?:ACTION\s*:|I(?:'ll| will))?\s*CHECK", re.IGNORECASE
        ),
        PokerAction.CALL: re.compile(
            r"(?i)(?:ACTION\s*:|I(?:'ll| will))?\s*CALL", re.IGNORECASE
        ),
        PokerAction.BET: re.compile(
            r"(?i)(?:ACTION\s*:|I(?:'ll| will))?\s*BET\s+(\d+)", re.IGNORECASE
        ),
        PokerAction.RAISE: re.compile(
            r"(?i)(?:ACTION\s*:|I(?:'ll| will))?\s*RAISE\s+(?:TO\s+)?(\d+)",
            re.IGNORECASE,
        ),
        PokerAction.ALL_IN: re.compile(
            r"(?i)(?:ACTION\s*:|I(?:'ll| will))?\s*(?:GO\s+)?ALL[\s-]IN", re.IGNORECASE
        ),
    }
}
