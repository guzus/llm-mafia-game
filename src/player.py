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

    def __init__(self, model_name, role, language=None):
        """
        Initialize a player with a model name and role.

        Args:
            model_name (str): The name of the LLM model.
            role (Role): The role of the player in the game.
            language (str, optional): Language for game prompts and interactions. Defaults to config.LANGUAGE.
        """
        self.model_name = model_name
        self.role = role
        self.alive = True
        self.protected = False  # Whether the player is protected by the doctor
        self.language = language if language is not None else config.LANGUAGE

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

        # Base prompt based on role and language
        if self.language == "English":
            if self.role == Role.MAFIA:
                # For Mafia members
                mafia_names = [
                    p.model_name for p in mafia_members if p != self and p.alive
                ]
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
        elif self.language == "Spanish":
            if self.role == Role.MAFIA:
                # For Mafia members in Spanish
                mafia_names = [
                    p.model_name for p in mafia_members if p != self and p.alive
                ]
                prompt = f"""
Estás jugando un juego de Mafia como miembro de la Mafia. Tu objetivo es eliminar a los aldeanos.
Otros miembros de la Mafia: {', '.join(mafia_names) if mafia_names else 'Ninguno (eres el único miembro de la Mafia que queda)'}
Todos los jugadores: {', '.join(player_names)}
Estado actual del juego: {game_state}

Durante la fase nocturna, debes matar a un jugador que no sea de la Mafia. Usa el formato: ACCIÓN: Matar [jugador]
Durante la fase diurna, convence a los demás de que eres inocente y vota para eliminar a un aldeano.
Discusión previa: {discussion_history}

Tu respuesta:
"""
            elif self.role == Role.DOCTOR:
                # For Doctor in Spanish
                prompt = f"""
Estás jugando un juego de Mafia como el Doctor. Tu objetivo es ayudar a los aldeanos protegiendo a los jugadores de los asesinatos de la Mafia.
Todos los jugadores: {', '.join(player_names)}
Estado actual del juego: {game_state}

Durante la fase nocturna, puedes proteger a un jugador. Usa el formato: ACCIÓN: Proteger [jugador]
Durante la fase diurna, usa tus observaciones para ayudar a eliminar a los miembros de la Mafia.
Discusión previa: {discussion_history}

Tu respuesta:
"""
            else:  # Role.VILLAGER
                # For Villagers in Spanish
                prompt = f"""
Estás jugando un juego de Mafia como Aldeano. Tu objetivo es identificar y eliminar a la Mafia.
Todos los jugadores: {', '.join(player_names)}
Estado actual del juego: {game_state}

Durante la fase diurna, discute con otros aldeanos para identificar a los miembros de la Mafia.
Termina tu mensaje con tu voto. Usa el formato: VOTO: [jugador]
Discusión previa: {discussion_history}

Tu respuesta:
"""
        elif self.language == "French":
            if self.role == Role.MAFIA:
                # For Mafia members in French
                mafia_names = [
                    p.model_name for p in mafia_members if p != self and p.alive
                ]
                prompt = f"""
Vous jouez à un jeu de Mafia en tant que membre de la Mafia. Votre objectif est d'éliminer les villageois.
Autres membres de la Mafia: {', '.join(mafia_names) if mafia_names else 'Aucun (vous êtes le seul membre de la Mafia restant)'}
Tous les joueurs: {', '.join(player_names)}
État actuel du jeu: {game_state}

Pendant la phase de nuit, vous devez tuer un joueur qui n'est pas de la Mafia. Utilisez le format: ACTION: Tuer [joueur]
Pendant la phase de jour, convainquez les autres que vous êtes innocent et votez pour éliminer un villageois.
Discussion précédente: {discussion_history}

Votre réponse:
"""
            elif self.role == Role.DOCTOR:
                # For Doctor in French
                prompt = f"""
Vous jouez à un jeu de Mafia en tant que Docteur. Votre objectif est d'aider les villageois en protégeant les joueurs des meurtres de la Mafia.
Tous les joueurs: {', '.join(player_names)}
État actuel du jeu: {game_state}

Pendant la phase de nuit, vous pouvez protéger un joueur. Utilisez le format: ACTION: Protéger [joueur]
Pendant la phase de jour, utilisez vos observations pour aider à éliminer les membres de la Mafia.
Discussion précédente: {discussion_history}

Votre réponse:
"""
            else:  # Role.VILLAGER
                # For Villagers in French
                prompt = f"""
Vous jouez à un jeu de Mafia en tant que Villageois. Votre objectif est d'identifier et d'éliminer la Mafia.
Tous les joueurs: {', '.join(player_names)}
État actuel du jeu: {game_state}

Pendant la phase de jour, discutez avec les autres villageois pour identifier les membres de la Mafia.
Terminez votre message par votre vote. Utilisez le format: VOTE: [joueur]
Discussion précédente: {discussion_history}

Votre réponse:
"""
        elif self.language == "Korean":
            if self.role == Role.MAFIA:
                # For Mafia members in Korean
                mafia_names = [
                    p.model_name for p in mafia_members if p != self and p.alive
                ]
                prompt = f"""
당신은 마피아 게임에서 마피아 멤버로 플레이하고 있습니다. 당신의 목표는 마을 사람들을 제거하는 것입니다.
다른 마피아 멤버: {', '.join(mafia_names) if mafia_names else '없음 (당신이 유일하게 남은 마피아입니다)'}
모든 플레이어: {', '.join(player_names)}
현재 게임 상태: {game_state}

밤 단계에서는 마피아가 아닌 플레이어를 죽여야 합니다. 형식: 행동: 죽이기 [플레이어]
낮 단계에서는 다른 사람들에게 당신이 무고하다고 설득하고 마을 사람을 제거하기 위해 투표하세요.
이전 토론: {discussion_history}

당신의 응답:
"""
            elif self.role == Role.DOCTOR:
                # For Doctor in Korean
                prompt = f"""
당신은 마피아 게임에서 의사로 플레이하고 있습니다. 당신의 목표는 마피아의 살인으로부터 플레이어를 보호하여 마을 사람들을 돕는 것입니다.
모든 플레이어: {', '.join(player_names)}
현재 게임 상태: {game_state}

밤 단계에서는 한 플레이어를 보호할 수 있습니다. 형식: 행동: 보호하기 [플레이어]
낮 단계에서는 당신의 관찰을 사용하여 마피아 멤버를 제거하는 데 도움을 주세요.
이전 토론: {discussion_history}

당신의 응답:
"""
            else:  # Role.VILLAGER
                # For Villagers in Korean
                prompt = f"""
당신은 마피아 게임에서 마을 사람으로 플레이하고 있습니다. 당신의 목표는 마피아를 식별하고 제거하는 것입니다.
모든 플레이어: {', '.join(player_names)}
현재 게임 상태: {game_state}

낮 단계에서는 다른 마을 사람들과 토론하여 마피아 멤버를 식별하세요.
메시지 끝에 투표를 포함하세요. 형식: 투표: [플레이어]
이전 토론: {discussion_history}

당신의 응답:
"""
        else:
            # Default to English if language not supported
            if self.role == Role.MAFIA:
                # For Mafia members
                mafia_names = [
                    p.model_name for p in mafia_members if p != self and p.alive
                ]
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
            # Look for action pattern based on language
            if self.language == "English":
                match = re.search(
                    r"ACTION:\s*Kill\s+(\w+[-\w]*)", response, re.IGNORECASE
                )
            elif self.language == "Spanish":
                match = re.search(
                    r"ACCIÓN:\s*Matar\s+(\w+[-\w]*)", response, re.IGNORECASE
                )
            elif self.language == "French":
                match = re.search(
                    r"ACTION:\s*Tuer\s+(\w+[-\w]*)", response, re.IGNORECASE
                )
            elif self.language == "Korean":
                match = re.search(
                    r"행동:\s*죽이기\s+(\w+[-\w]*)", response, re.IGNORECASE
                )
            else:
                # Default to English
                match = re.search(
                    r"ACTION:\s*Kill\s+(\w+[-\w]*)", response, re.IGNORECASE
                )

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
            # Look for action pattern based on language
            if self.language == "English":
                match = re.search(
                    r"ACTION:\s*Protect\s+(\w+[-\w]*)", response, re.IGNORECASE
                )
            elif self.language == "Spanish":
                match = re.search(
                    r"ACCIÓN:\s*Proteger\s+(\w+[-\w]*)", response, re.IGNORECASE
                )
            elif self.language == "French":
                match = re.search(
                    r"ACTION:\s*Protéger\s+(\w+[-\w]*)", response, re.IGNORECASE
                )
            elif self.language == "Korean":
                match = re.search(
                    r"행동:\s*보호하기\s+(\w+[-\w]*)", response, re.IGNORECASE
                )
            else:
                # Default to English
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

        Args:
            response (str): The response from the player.
            all_players (list): List of all players in the game.

        Returns:
            Player or None: The player being voted for, or None if no valid vote.
        """
        # Updated regex that can handle more complex model names with special characters
        # and supports different languages
        if self.language == "English":
            match = re.search(
                r"VOTE:\s*([\w./-]+(?:[-:]\w+)*)", response, re.IGNORECASE
            )
        elif self.language == "Spanish":
            match = re.search(
                r"VOTO:\s*([\w./-]+(?:[-:]\w+)*)", response, re.IGNORECASE
            )
        elif self.language == "French":
            match = re.search(
                r"VOTE:\s*([\w./-]+(?:[-:]\w+)*)", response, re.IGNORECASE
            )
        elif self.language == "Korean":
            match = re.search(
                r"투표:\s*([\w./-]+(?:[-:]\w+)*)", response, re.IGNORECASE
            )
        else:
            # Default to English
            match = re.search(
                r"VOTE:\s*([\w./-]+(?:[-:]\w+)*)", response, re.IGNORECASE
            )

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

        # Generate prompt based on language
        if self.language == "English":
            prompt = f"""
You are playing a Mafia game. The town has voted to eliminate {player_to_eliminate}.
Before the elimination is carried out, a confirmation vote is needed.

Current game state: {game_state_str}

Do you agree with eliminating {player_to_eliminate}? 
Respond with either "AGREE" or "DISAGREE" and a brief explanation of your reasoning.

Your response:
"""
        elif self.language == "Spanish":
            prompt = f"""
Estás jugando un juego de Mafia. El pueblo ha votado para eliminar a {player_to_eliminate}.
Antes de que se lleve a cabo la eliminación, se necesita un voto de confirmación.

Estado actual del juego: {game_state_str}

¿Estás de acuerdo con eliminar a {player_to_eliminate}?
Responde con "ACUERDO" o "DESACUERDO" y una breve explicación de tu razonamiento.

Tu respuesta:
"""
        elif self.language == "French":
            prompt = f"""
Vous jouez à un jeu de Mafia. La ville a voté pour éliminer {player_to_eliminate}.
Avant que l'élimination ne soit effectuée, un vote de confirmation est nécessaire.

État actuel du jeu: {game_state_str}

Êtes-vous d'accord pour éliminer {player_to_eliminate}?
Répondez par "D'ACCORD" ou "PAS D'ACCORD" et une brève explication de votre raisonnement.

Votre réponse:
"""
        elif self.language == "Korean":
            prompt = f"""
당신은 마피아 게임을 하고 있습니다. 마을은 {player_to_eliminate}을(를) 제거하기로 투표했습니다.
제거가 실행되기 전에 확인 투표가 필요합니다.

현재 게임 상태: {game_state_str}

{player_to_eliminate}을(를) 제거하는 것에 동의하십니까?
"동의" 또는 "반대"로 응답하고 간단한 이유를 설명해 주세요.

당신의 응답:
"""
        else:
            # Default to English if language not supported
            prompt = f"""
You are playing a Mafia game. The town has voted to eliminate {player_to_eliminate}.
Before the elimination is carried out, a confirmation vote is needed.

Current game state: {game_state_str}

Do you agree with eliminating {player_to_eliminate}? 
Respond with either "AGREE" or "DISAGREE" and a brief explanation of your reasoning.

Your response:
"""
        response = self.get_response(prompt)

        # Parse the response for agree/disagree based on language
        if self.language == "Spanish":
            if re.search(r"\b(acuerdo|sí|confirmo|apruebo)\b", response.lower()):
                return "agree"
            else:
                return "disagree"
        elif self.language == "French":
            if re.search(r"\b(d'accord|oui|confirme|approuve)\b", response.lower()):
                return "agree"
            else:
                return "disagree"
        elif self.language == "Korean":
            if re.search(r"\b(동의|예|확인|승인)\b", response.lower()):
                return "agree"
            else:
                return "disagree"
        else:
            # Default English parsing
            if re.search(r"\b(agree|yes|confirm|approve)\b", response.lower()):
                return "agree"
            else:
                return "disagree"
