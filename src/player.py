"""
Player class for the LLM Mafia Game Competition.
"""

import re
import config
from openrouter import get_llm_response
from game_templates import (
    Role,
    GAME_RULES,
    CONFIRMATION_VOTE_EXPLANATIONS,
    PROMPT_TEMPLATES,
    CONFIRMATION_VOTE_TEMPLATES,
    THINKING_TAGS,
    ACTION_PATTERNS,
    VOTE_PATTERNS,
    CONFIRMATION_VOTE_PATTERNS,
)


class Player:
    """Represents an LLM player in the Mafia game."""

    def __init__(self, model_name, player_name, role, language=None):
        """
        Initialize a player.

        Args:
            model_name (str): The name of the LLM model to use for this player (hidden from other players).
            player_name (str): The visible name of the player in the game.
            role (Role): The role of the player in the game.
            language (str, optional): The language for the player. Defaults to English.
        """
        self.model_name = model_name
        self.player_name = player_name
        self.role = role
        self.alive = True
        self.protected = False  # Whether the player is protected by the doctor
        self.language = language if language else "English"

    def __str__(self):
        """Return a string representation of the player."""
        return f"{self.player_name} ({self.role.value}) [Model: {self.model_name}]"

    def _extract_players_from_prompt(self, prompt):
        """Extract visible player names from the prompt text."""
        patterns = [
            r"All players:\s*(.+)",
            r"Todos los jugadores:\s*(.+)",
            r"Tous les joueurs:\s*(.+)",
            r"모든 플레이어:\s*(.+)",
        ]
        for pattern in patterns:
            match = re.search(pattern, prompt)
            if match:
                return [name.strip() for name in match.group(1).split(",") if name.strip()]
        return []

    def _extract_other_mafia_from_prompt(self, prompt):
        """Extract visible mafia teammate names from the prompt text."""
        patterns = [
            r"Other Mafia members:\s*(.+)",
            r"Otros miembros de la Mafia:\s*(.+)",
            r"Autres membres de la Mafia:\s*(.+)",
            r"다른 마피아 멤버:\s*(.+)",
        ]
        for pattern in patterns:
            match = re.search(pattern, prompt)
            if match:
                raw = match.group(1).strip()
                if raw.lower().startswith("none") or raw in {"없음"}:
                    return []
                return [name.strip() for name in raw.split(",") if name.strip()]
        return []

    def _is_confirmation_prompt(self, prompt):
        """Return True when this prompt is asking for a confirmation vote."""
        markers = [
            "confirmation vote is needed",
            "before the elimination is carried out",
            "se necesita un voto de confirmación",
            "vote de confirmation est nécessaire",
            "확인 투표가 필요합니다",
        ]
        prompt_lower = prompt.lower()
        return any(marker in prompt_lower for marker in markers)

    def _build_fallback_response(self, prompt):
        """Generate a minimal valid response when the upstream model call fails."""
        players = self._extract_players_from_prompt(prompt)
        other_players = [name for name in players if name != self.player_name]
        other_mafia = set(self._extract_other_mafia_from_prompt(prompt))
        non_mafia_targets = [
            name
            for name in other_players
            if name not in other_mafia and name != self.player_name
        ]
        day_target = other_players[0] if other_players else self.player_name
        night_target = non_mafia_targets[0] if non_mafia_targets else day_target

        language = self.language if self.language in PROMPT_TEMPLATES else "English"
        prompt_lower = prompt.lower()

        if self._is_confirmation_prompt(prompt):
            responses = {
                "English": "AGREE. We should proceed with the town's decision.",
                "Spanish": "ACUERDO. Debemos seguir con la decisión del pueblo.",
                "French": "D'ACCORD. Nous devons suivre la décision de la ville.",
                "Korean": "동의. 마을의 결정을 진행해야 합니다.",
            }
            return responses.get(language, responses["English"])

        is_night_phase = any(
            marker in prompt_lower
            for marker in [
                "it's night time",
                "night time",
                "es hora de noche",
                "c'est la nuit",
                "밤 시간입니다",
            ]
        )
        is_voting_phase = "voting phase" in prompt_lower or "phase de vote" in prompt_lower

        if is_night_phase and self.role == Role.MAFIA:
            responses = {
                "English": f"We need to move quickly. ACTION: Kill {night_target}",
                "Spanish": f"Debemos actuar rápido. ACCIÓN: Matar {night_target}",
                "French": f"Il faut agir vite. ACTION: Tuer {night_target}",
                "Korean": f"빨리 행동해야 합니다. 행동: 죽이기 {night_target}",
            }
            return responses.get(language, responses["English"])

        if is_night_phase and self.role == Role.DOCTOR:
            protect_target = day_target if day_target else self.player_name
            responses = {
                "English": f"I am playing it safe tonight. ACTION: Protect {protect_target}",
                "Spanish": f"Voy a jugar sobre seguro esta noche. ACCIÓN: Proteger {protect_target}",
                "French": f"Je joue la sécurité cette nuit. ACTION: Protéger {protect_target}",
                "Korean": f"이번 밤은 안전하게 갑니다. 행동: 보호하기 {protect_target}",
            }
            return responses.get(language, responses["English"])

        if is_voting_phase:
            responses = {
                "English": f"I need to force a decision. VOTE: {day_target}",
                "Spanish": f"Necesitamos tomar una decisión. VOTO: {day_target}",
                "French": f"Il faut trancher maintenant. VOTE: {day_target}",
                "Korean": f"지금 결정을 내려야 합니다. 투표: {day_target}",
            }
            return responses.get(language, responses["English"])

        responses = {
            "English": "I need a moment to regroup. We should compare stories and pressure contradictions.",
            "Spanish": "Necesito reagruparme. Debemos comparar historias y presionar las contradicciones.",
            "French": "J'ai besoin de me recentrer. Nous devons comparer les récits et pousser les contradictions.",
            "Korean": "잠시 정리하겠습니다. 서로의 이야기를 비교하고 모순을 압박해야 합니다.",
        }
        return responses.get(language, responses["English"])

    def _find_target_player(self, target_name, all_players, exclude_mafia=False):
        """
        Find a target player by name.

        Args:
            target_name (str): The name of the target player.
            all_players (list): List of all players in the game.
            exclude_mafia (bool, optional): Whether to exclude Mafia members from targets.

        Returns:
            Player or None: The target player if found, None otherwise.
        """
        for player in all_players:
            if not player.alive:
                continue

            if exclude_mafia and player.role == Role.MAFIA:
                continue

            if target_name.lower() in player.player_name.lower():
                return player

        return None

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

        # Get list of player names (using visible player names)
        player_names = [p.player_name for p in all_players if p.alive]

        # Make sure we're only using player_name (not model_name) for other players
        # This ensures players only know each other by their player names
        player_info = [{"name": p.player_name, "alive": p.alive} for p in all_players]

        # Get the appropriate language, defaulting to English if not supported
        language = self.language if self.language in GAME_RULES else "English"

        # Get game rules for the player's language
        game_rules = GAME_RULES[language]

        if self.role == Role.MAFIA:
            # For Mafia members (using visible player names)
            mafia_names = [
                p.player_name for p in mafia_members if p != self and p.alive
            ]
            mafia_list = f"{', '.join(mafia_names) if mafia_names else 'None (you are the only Mafia left)'}"
            if language == "Spanish":
                mafia_list = f"{', '.join(mafia_names) if mafia_names else 'Ninguno (eres el único miembro de la Mafia que queda)'}"
            elif language == "French":
                mafia_list = f"{', '.join(mafia_names) if mafia_names else 'Aucun (vous êtes le seul membre de la Mafia restant)'}"
            elif language == "Korean":
                mafia_list = f"{', '.join(mafia_names) if mafia_names else '없음 (당신이 유일하게 남은 마피아입니다)'}"

            prompt = PROMPT_TEMPLATES[language][Role.MAFIA].format(
                model_name=self.player_name,  # Use player_name in prompts
                game_rules=game_rules,
                mafia_members=mafia_list,
                player_names=", ".join(player_names),
                game_state=game_state,
                thinking_tag=THINKING_TAGS[language],
                discussion_history=discussion_history,
            )
        elif self.role == Role.DOCTOR:
            # For Doctor
            prompt = PROMPT_TEMPLATES[language][Role.DOCTOR].format(
                model_name=self.player_name,  # Use player_name in prompts
                game_rules=game_rules,
                player_names=", ".join(player_names),
                game_state=game_state,
                thinking_tag=THINKING_TAGS[language],
                discussion_history=discussion_history,
            )
        else:  # Role.VILLAGER
            # For Villagers
            prompt = PROMPT_TEMPLATES[language][Role.VILLAGER].format(
                model_name=self.player_name,  # Use player_name in prompts
                game_rules=game_rules,
                player_names=", ".join(player_names),
                game_state=game_state,
                thinking_tag=THINKING_TAGS[language],
                discussion_history=discussion_history,
            )

        return prompt

    def get_response(self, prompt):
        """
        Get a response from the LLM model using OpenRouter API.

        Args:
            prompt (str): The prompt to send to the model.

        Returns:
            str: The response from the model with private thoughts removed.
        """
        response = get_llm_response(self.model_name, prompt)
        if response.startswith("ERROR:"):
            response = self._build_fallback_response(prompt)

        # Remove any <think></think> tags and their contents before sharing with other players
        cleaned_response = re.sub(r"<think>.*?</think>", "", response, flags=re.DOTALL)

        # Clean up any extra whitespace that might have been created
        cleaned_response = re.sub(r"\n\s*\n", "\n\n", cleaned_response)
        cleaned_response = cleaned_response.strip()

        return cleaned_response

    def parse_night_action(self, response, all_players):
        """
        Parse the night action from the player's response.

        Args:
            response (str): The response from the player (already cleaned of thinking tags).
            all_players (list): List of all players in the game.

        Returns:
            tuple: (action_type, target_player) or (None, None) if no valid action.
        """
        if self.role == Role.MAFIA:
            # Look for action pattern based on language
            pattern = ACTION_PATTERNS.get(self.language, ACTION_PATTERNS["English"])[
                Role.MAFIA
            ]
            match = re.search(pattern, response, re.IGNORECASE)

            if match:
                target_name = match.group(1).strip()
                # Find the target player, excluding Mafia members
                target_player = self._find_target_player(
                    target_name, all_players, exclude_mafia=True
                )
                if target_player:
                    return "kill", target_player
            return None, None

        elif self.role == Role.DOCTOR:
            # Look for action pattern based on language
            pattern = ACTION_PATTERNS.get(self.language, ACTION_PATTERNS["English"])[
                Role.DOCTOR
            ]
            match = re.search(pattern, response, re.IGNORECASE)

            if match:
                target_name = match.group(1).strip()
                # Find the target player
                target_player = self._find_target_player(target_name, all_players)
                if target_player:
                    return "protect", target_player
            return None, None
        else:
            # Villagers don't have night actions
            return None, None

    def parse_day_vote(self, response, all_players):
        """
        Parse the day vote from the player's response.

        Args:
            response (str): The response from the player (already cleaned of thinking tags).
            all_players (list): List of all players in the game.

        Returns:
            Player or None: The player being voted for, or None if no valid vote.
        """
        # Get vote pattern based on language
        pattern = VOTE_PATTERNS.get(self.language, VOTE_PATTERNS["English"])
        match = re.search(pattern, response, re.IGNORECASE)

        if match:
            target_name = match.group(1).strip()
            # Find the target player
            return self._find_target_player(target_name, all_players)
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

        # Get the appropriate language, defaulting to English if not supported
        language = (
            self.language
            if self.language in CONFIRMATION_VOTE_EXPLANATIONS
            else "English"
        )

        # Get confirmation vote explanation for the player's language
        confirmation_explanation = CONFIRMATION_VOTE_EXPLANATIONS[language].format(
            player_to_eliminate=player_to_eliminate
        )

        # Generate prompt based on language
        prompt = CONFIRMATION_VOTE_TEMPLATES[language].format(
            model_name=self.player_name,  # Use player_name in prompts
            player_to_eliminate=player_to_eliminate,
            confirmation_explanation=confirmation_explanation,
            game_state_str=game_state_str,
            thinking_tag=THINKING_TAGS[language],
        )

        response = self.get_response(prompt)

        # Parse the response for agree/disagree based on language
        language = (
            self.language if self.language in CONFIRMATION_VOTE_PATTERNS else "English"
        )
        if re.search(CONFIRMATION_VOTE_PATTERNS[language]["agree"], response.lower()):
            return "agree"
        else:
            return "disagree"
