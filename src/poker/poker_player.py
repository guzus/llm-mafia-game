"""
Player class for the LLM Poker Game.
"""

import re
from poker_openrouter import get_llm_response
from poker_templates import (
    PokerAction,
    PROMPT_TEMPLATES,
    THINKING_TAGS,
    ACTION_PATTERNS,
)


class PokerPlayer:
    """Represents an LLM player in the poker game."""

    def __init__(self, model_name, position, starting_chips, language="English"):
        """
        Initialize a poker player.

        Args:
            model_name (str): The name of the LLM model to use for this player.
            position (int): The player's position at the table (0 is dealer/button).
            starting_chips (int): The number of chips the player starts with.
            language (str, optional): The language for the player. Defaults to English.
        """
        self.model_name = model_name
        self.position = position
        self.chips = starting_chips
        self.language = language
        self.hole_cards = []
        self.folded = False
        self.all_in = False
        self.current_bet = 0  # Amount bet in the current round
        self.position_name = self._get_position_name(position)

    def __str__(self):
        """Return a string representation of the player."""
        return f"{self.model_name} ({self.position_name}, {self.chips} chips)"

    def _get_position_name(self, position):
        """
        Get the name of the position based on the position index.

        Args:
            position (int): The position index.

        Returns:
            str: The name of the position.
        """
        position_names = ["Button", "Small Blind", "Big Blind", "UTG", "MP", "CO"]
        if position < len(position_names):
            return position_names[position]
        return f"Position {position}"

    def reset_for_new_hand(self):
        """Reset the player's state for a new hand."""
        self.hole_cards = []
        self.folded = False
        self.all_in = False
        self.current_bet = 0

    def receive_cards(self, cards):
        """
        Give the player their hole cards.

        Args:
            cards (list): A list of two card objects.
        """
        self.hole_cards = cards

    def generate_prompt(
        self,
        community_cards,
        pot,
        current_bet_to_call,
        active_players,
        player_chips,
        round_actions,
        previous_rounds,
    ):
        """
        Generate a prompt for the player based on the current game state.

        Args:
            community_cards (list): The community cards on the table.
            pot (int): The current pot size.
            current_bet_to_call (int): The current bet that needs to be called.
            active_players (list): List of players still in the hand.
            player_chips (dict): Dictionary mapping player names to their chip counts.
            round_actions (str): String describing the actions taken in the current round.
            previous_rounds (str): String describing the actions in previous rounds.

        Returns:
            str: The prompt for the player.
        """
        # Format hole cards for display
        hole_cards_str = (
            ", ".join([f"{card}" for card in self.hole_cards])
            if self.hole_cards
            else "None"
        )

        # Format community cards for display
        community_cards_str = (
            ", ".join([f"{card}" for card in community_cards])
            if community_cards
            else "None"
        )

        # Format active players
        active_players_str = ", ".join([str(p.model_name) for p in active_players])

        # Format player chips
        player_chips_str = ", ".join(
            [f"{name}: {chips}" for name, chips in player_chips.items()]
        )

        # Get the appropriate language, defaulting to English if not supported
        language = self.language if self.language in PROMPT_TEMPLATES else "English"

        # Get thinking tag for the player's language
        thinking_tag = THINKING_TAGS.get(language, "")

        # Get game rules for the player's language
        from src.poker.poker_templates import GAME_RULES

        game_rules = GAME_RULES.get(language, GAME_RULES["English"])

        # Generate the prompt using the template
        prompt = PROMPT_TEMPLATES[language]["POKER_PLAYER"].format(
            model_name=self.model_name,
            game_rules=game_rules,
            hole_cards=hole_cards_str,
            community_cards=community_cards_str,
            chips=self.chips,
            pot=pot,
            current_bet=current_bet_to_call,
            position=self.position_name,
            active_players=active_players_str,
            player_chips=player_chips_str,
            round_actions=round_actions,
            previous_rounds=previous_rounds,
            thinking_tag=thinking_tag,
        )

        return prompt

    def get_response(self, prompt):
        """
        Get a response from the LLM model.

        Args:
            prompt (str): The prompt to send to the model.

        Returns:
            str: The response from the model.
        """
        return get_llm_response(self.model_name, prompt)

    def parse_action(self, response, current_bet_to_call, min_raise):
        """
        Parse the player's action from their response.

        Args:
            response (str): The response from the LLM.
            current_bet_to_call (int): The current bet that needs to be called.
            min_raise (int): The minimum raise amount.

        Returns:
            tuple: (action, amount) where action is a PokerAction and amount is an integer.
        """
        # Get the appropriate language patterns
        language = self.language if self.language in ACTION_PATTERNS else "English"
        patterns = ACTION_PATTERNS[language]

        # Check for fold
        if patterns[PokerAction.FOLD].search(response):
            return (PokerAction.FOLD, 0)

        # Check for check (only valid if there's no bet to call)
        if patterns[PokerAction.CHECK].search(response):
            if current_bet_to_call == 0:
                return (PokerAction.CHECK, 0)
            else:
                # If player tries to check when there's a bet, treat as a call
                return (PokerAction.CALL, current_bet_to_call)

        # Check for call
        if patterns[PokerAction.CALL].search(response):
            # If player doesn't have enough chips to call, they go all-in
            if current_bet_to_call >= self.chips:
                return (PokerAction.ALL_IN, self.chips)
            return (PokerAction.CALL, current_bet_to_call)

        # Check for all-in
        if patterns[PokerAction.ALL_IN].search(response):
            return (PokerAction.ALL_IN, self.chips)

        # Check for bet (only valid if there's no bet to call)
        bet_match = patterns[PokerAction.BET].search(response)
        if bet_match and current_bet_to_call == 0:
            amount = int(bet_match.group(1))
            # Ensure bet is at least the minimum bet (big blind)
            if amount < min_raise:
                amount = min_raise
            # If bet is more than player's chips, they go all-in
            if amount >= self.chips:
                return (PokerAction.ALL_IN, self.chips)
            return (PokerAction.BET, amount)

        # Check for raise
        raise_match = patterns[PokerAction.RAISE].search(response)
        if raise_match:
            amount = int(raise_match.group(1))
            # Ensure raise is at least the minimum raise
            if amount < current_bet_to_call + min_raise:
                amount = current_bet_to_call + min_raise
            # If raise is more than player's chips, they go all-in
            if amount >= self.chips:
                return (PokerAction.ALL_IN, self.chips)
            return (PokerAction.RAISE, amount)

        # Default to call if no valid action is found
        if current_bet_to_call == 0:
            return (PokerAction.CHECK, 0)
        elif current_bet_to_call >= self.chips:
            return (PokerAction.ALL_IN, self.chips)
        else:
            return (PokerAction.CALL, current_bet_to_call)
