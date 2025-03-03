"""
Player class for the LLM Mafia Game Competition.
"""

import re
from enum import Enum
import config
from openrouter import get_llm_response


class Role(Enum):
    """Enum for player roles in the game."""

    MAFIA = "Mafia"
    VILLAGER = "Villager"
    DOCTOR = "Doctor"


class Player:
    """Represents an LLM player in the Mafia game."""

    def __init__(self, model_name, role):
        """
        Initialize a player with a model name and role.

        Args:
            model_name (str): The name of the LLM model.
            role (Role): The role of the player in the game.
        """
        self.model_name = model_name
        self.role = role
        self.alive = True
        self.protected = False  # Whether the player is protected by the doctor

    def __str__(self):
        """String representation of the player."""
        return f"{self.model_name} ({self.role.value})"

    def generate_prompt(
        self, game_state, all_players, mafia_members=None, discussion_history=None
    ):
        """
        Generate a prompt for the player based on their role.

        Args:
            game_state (dict): The current state of the game.
            all_players (list): List of all players in the game.
            mafia_members (list, optional): List of mafia members (only for Mafia role).
            discussion_history (str, optional): History of previous discussions.
                Note: This should only contain day phase messages, night messages are filtered out.

        Returns:
            str: The prompt for the player.
        """
        if discussion_history is None:
            discussion_history = ""

        # Get list of player names
        player_names = [p.model_name for p in all_players if p.alive]

        # Base prompt based on role
        if self.role == Role.MAFIA:
            # For Mafia members
            mafia_names = [p.model_name for p in mafia_members if p != self and p.alive]
            prompt = f"""
You are playing a Mafia game as a Mafia member. Your goal is to eliminate the villagers.
Other Mafia members: {', '.join(mafia_names) if mafia_names else 'None (you are the only Mafia left)'}
All players: {', '.join(player_names)}
Current game state: {game_state}

During night phase, you must kill a non-Mafia player. Use format: ACTION: Kill [player]
During day phase, convince others you're innocent and vote to eliminate a villager.
Previous discussion: {discussion_history}

Your response:
"""
        elif self.role == Role.DOCTOR:
            # For Doctor
            prompt = f"""
You are playing a Mafia game as the Doctor. Your goal is to help villagers by protecting players from Mafia kills.
All players: {', '.join(player_names)}
Current game state: {game_state}

During night phase, you can protect one player. Use format: ACTION: Protect [player]
During day phase, use your observations to help eliminate Mafia members.
Previous discussion: {discussion_history}

Your response:
"""
        else:  # Role.VILLAGER
            # For Villagers
            prompt = f"""
You are playing a Mafia game as a Villager. Your goal is to identify and eliminate the Mafia.
All players: {', '.join(player_names)}
Current game state: {game_state}

During day phase, discuss with other villagers to identify the Mafia members.
End your message with your vote. Use format: VOTE: [player]
Previous discussion: {discussion_history}

Your response:
"""
        return prompt

    def get_response(self, prompt):
        """
        Get a response from the LLM model using OpenRouter API.

        Args:
            prompt (str): The prompt to send to the model.

        Returns:
            str: The response from the model.
        """
        return get_llm_response(self.model_name, prompt)

    def parse_night_action(self, response, all_players):
        """
        Parse the night action from the player's response.

        Args:
            response (str): The response from the player.
            all_players (list): List of all players in the game.

        Returns:
            tuple: (action_type, target_player) or (None, None) if no valid action.
        """
        if self.role == Role.MAFIA:
            # Look for "ACTION: Kill [player]" pattern
            match = re.search(r"ACTION:\s*Kill\s+(\w+[-\w]*)", response, re.IGNORECASE)
            if match:
                target_name = match.group(1).strip()
                # Find the target player
                for player in all_players:
                    if (
                        player.alive
                        and target_name.lower() in player.model_name.lower()
                    ):
                        return "kill", player

        elif self.role == Role.DOCTOR:
            # Look for "ACTION: Protect [player]" pattern
            match = re.search(
                r"ACTION:\s*Protect\s+(\w+[-\w]*)", response, re.IGNORECASE
            )
            if match:
                target_name = match.group(1).strip()
                # Find the target player
                for player in all_players:
                    if (
                        player.alive
                        and target_name.lower() in player.model_name.lower()
                    ):
                        return "protect", player

        return None, None

    def parse_day_vote(self, response, all_players):
        """
        Parse the day vote from the player's response.
        """
        # Updated regex that can handle more complex model names with special characters
        match = re.search(r"VOTE:\s*([\w./-]+(?:[-:]\w+)*)", response, re.IGNORECASE)
        if match:
            target_name = match.group(1).strip()
            # Find the target player
            for player in all_players:
                if player.alive and target_name.lower() in player.model_name.lower():
                    return player

        return None

    def get_confirmation_vote(self, game_state):
        """
        Get a confirmation vote from the player on whether to eliminate another player.

        Args:
            game_state (dict): The current state of the game, including who is up for elimination.

        Returns:
            str: "agree" or "disagree" indicating the player's vote
        """
        player_to_eliminate = game_state["confirmation_vote_for"]
        game_state_str = game_state["game_state"]

        prompt = f"""
You are playing a Mafia game. The town has voted to eliminate {player_to_eliminate}.
Before the elimination is carried out, a confirmation vote is needed.

Current game state: {game_state_str}

Do you agree with eliminating {player_to_eliminate}? 
Respond with either "AGREE" or "DISAGREE" and a brief explanation of your reasoning.

Your response:
"""
        response = self.get_response(prompt)

        # Parse the response for agree/disagree
        if re.search(r"\b(agree|yes|confirm|approve)\b", response.lower()):
            return "agree"
        else:
            return "disagree"
