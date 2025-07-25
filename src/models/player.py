"""Player model for the Mafia game."""

import re
from .enums import Role
from .templates import (
    GAME_RULES, PROMPT_TEMPLATES, get_thinking_tags, ACTION_PATTERNS,
    VOTE_PATTERNS, CONFIRMATION_VOTE_PATTERNS
)
from api.openrouter_client import get_llm_response


class Player:
    """Represents an LLM player in the Mafia game."""

    def __init__(self, model_name: str, player_name: str, role: Role, language: str = "English"):
        self.model_name = model_name
        self.player_name = player_name
        self.role = role
        self.alive = True
        self.protected = False
        self.language = language

    def __str__(self) -> str:
        return f"{self.player_name} ({self.role.value}) [Model: {self.model_name}]"

    def _find_target_player(self, target_name: str, all_players: list, exclude_mafia: bool = False):
        """Find a target player by name."""
        for player in all_players:
            if not player.alive:
                continue
            if exclude_mafia and player.role == Role.MAFIA:
                continue
            if target_name.lower() in player.player_name.lower():
                return player
        return None

    def generate_prompt(self, game_state: str, all_players: list, 
                       mafia_members: list = None, discussion_history: str = ""):
        """Generate a prompt for the player based on their role."""
        player_names = [p.player_name for p in all_players if p.alive]
        language = self.language if self.language in GAME_RULES else "English"
        game_rules = GAME_RULES[language]
        thinking_tags = get_thinking_tags()

        if self.role == Role.MAFIA and mafia_members:
            mafia_names = [p.player_name for p in mafia_members if p != self and p.alive]
            mafia_list = ', '.join(mafia_names) if mafia_names else 'None (you are the only Mafia left)'
            
            prompt = PROMPT_TEMPLATES[language][Role.MAFIA].format(
                model_name=self.player_name,
                game_rules=game_rules,
                mafia_members=mafia_list,
                player_names=", ".join(player_names),
                game_state=game_state,
                thinking_tag=thinking_tags[language],
                discussion_history=discussion_history,
            )
        else:
            # For Doctor and Villager
            template = PROMPT_TEMPLATES[language].get(self.role, PROMPT_TEMPLATES[language][Role.VILLAGER])
            prompt = template.format(
                model_name=self.player_name,
                game_rules=game_rules,
                player_names=", ".join(player_names),
                game_state=game_state,
                thinking_tag=thinking_tags[language],
                discussion_history=discussion_history,
            )

        return prompt

    def get_response(self, prompt: str) -> str:
        """Get a response from the LLM model."""
        response = get_llm_response(self.model_name, prompt)
        
        # Remove thinking tags
        cleaned_response = re.sub(r"<think>.*?</think>", "", response, flags=re.DOTALL)
        cleaned_response = re.sub(r"\n\s*\n", "\n\n", cleaned_response)
        
        return cleaned_response.strip()

    def parse_night_action(self, response: str, all_players: list) -> tuple:
        """Parse the night action from the player's response."""
        if self.role == Role.MAFIA:
            pattern = ACTION_PATTERNS.get(self.language, ACTION_PATTERNS["English"])[Role.MAFIA]
            match = re.search(pattern, response, re.IGNORECASE)
            if match:
                target_name = match.group(1).strip()
                target_player = self._find_target_player(target_name, all_players, exclude_mafia=True)
                if target_player:
                    return "kill", target_player
        elif self.role == Role.DOCTOR:
            pattern = ACTION_PATTERNS.get(self.language, ACTION_PATTERNS["English"])[Role.DOCTOR]
            match = re.search(pattern, response, re.IGNORECASE)
            if match:
                target_name = match.group(1).strip()
                target_player = self._find_target_player(target_name, all_players)
                if target_player:
                    return "protect", target_player
        
        return None, None

    def parse_day_vote(self, response: str, all_players: list):
        """Parse the day vote from the player's response."""
        pattern = VOTE_PATTERNS.get(self.language, VOTE_PATTERNS["English"])
        match = re.search(pattern, response, re.IGNORECASE)
        
        if match:
            target_name = match.group(1).strip()
            return self._find_target_player(target_name, all_players)
        return None

    def get_confirmation_vote(self, game_state: dict) -> str:
        """Get a confirmation vote from the player."""
        # Simplified confirmation vote logic
        prompt = f"Do you agree to eliminate {game_state['confirmation_vote_for']}? Respond with AGREE or DISAGREE."
        response = self.get_response(prompt)
        
        language = self.language if self.language in CONFIRMATION_VOTE_PATTERNS else "English"
        if re.search(CONFIRMATION_VOTE_PATTERNS[language]["agree"], response.lower()):
            return "agree"
        return "disagree"