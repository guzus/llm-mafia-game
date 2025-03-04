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


# Constants for prompt templates
PROMPT_TEMPLATES = {
    "English": {
        Role.MAFIA: """
You are {model_name}, playing a Mafia game as a Mafia member. Your goal is to eliminate the villagers.
Other Mafia members: {mafia_members}
All players: {player_names}
Current game state: {game_state}

{thinking_tag}

During night phase, you must kill a non-Mafia player. Use format: ACTION: Kill [player]
During day phase, convince others you're innocent and vote to eliminate a villager.
Previous discussion: {discussion_history}

Your response:
""",
        Role.DOCTOR: """
You are {model_name}, playing a Mafia game as the Doctor. Your goal is to help villagers by protecting players from Mafia kills.
All players: {player_names}
Current game state: {game_state}

{thinking_tag}

During night phase, you can protect one player. Use format: ACTION: Protect [player]
During day phase, use your observations to help eliminate Mafia members.
Previous discussion: {discussion_history}

Your response:
""",
        Role.VILLAGER: """
You are {model_name}, playing a Mafia game as a Villager. Your goal is to identify and eliminate the Mafia.
All players: {player_names}
Current game state: {game_state}

{thinking_tag}

During day phase, discuss with other villagers to identify the Mafia members.
End your message with your vote. Use format: VOTE: [player]
Previous discussion: {discussion_history}

Your response:
""",
    },
    "Spanish": {
        Role.MAFIA: """
Eres {model_name}, jugando un juego de Mafia como miembro de la Mafia. Tu objetivo es eliminar a los aldeanos.
Otros miembros de la Mafia: {mafia_members}
Todos los jugadores: {player_names}
Estado actual del juego: {game_state}

{thinking_tag}

Durante la fase nocturna, debes matar a un jugador que no sea de la Mafia. Usa el formato: ACCIÓN: Matar [jugador]
Durante la fase diurna, convence a los demás de que eres inocente y vota para eliminar a un aldeano.
Discusión previa: {discussion_history}

Tu respuesta:
""",
        Role.DOCTOR: """
Eres {model_name}, jugando un juego de Mafia como el Doctor. Tu objetivo es ayudar a los aldeanos protegiendo a los jugadores de los asesinatos de la Mafia.
Todos los jugadores: {player_names}
Estado actual del juego: {game_state}

{thinking_tag}

Durante la fase nocturna, puedes proteger a un jugador. Usa el formato: ACCIÓN: Proteger [jugador]
Durante la fase diurna, usa tus observaciones para ayudar a eliminar a los miembros de la Mafia.
Discusión previa: {discussion_history}

Tu respuesta:
""",
        Role.VILLAGER: """
Eres {model_name}, jugando un juego de Mafia como Aldeano. Tu objetivo es identificar y eliminar a la Mafia.
Todos los jugadores: {player_names}
Estado actual del juego: {game_state}

{thinking_tag}

Durante la fase diurna, discute con otros aldeanos para identificar a los miembros de la Mafia.
Termina tu mensaje con tu voto. Usa el formato: VOTO: [jugador]
Discusión previa: {discussion_history}

Tu respuesta:
""",
    },
    "French": {
        Role.MAFIA: """
Vous êtes {model_name}, jouant à un jeu de Mafia en tant que membre de la Mafia. Votre objectif est d'éliminer les villageois.
Autres membres de la Mafia: {mafia_members}
Tous les joueurs: {player_names}
État actuel du jeu: {game_state}

{thinking_tag}

Pendant la phase de nuit, vous devez tuer un joueur qui n'est pas de la Mafia. Utilisez le format: ACTION: Tuer [joueur]
Pendant la phase de jour, convainquez les autres que vous êtes innocent et votez pour éliminer un villageois.
Discussion précédente: {discussion_history}

Votre réponse:
""",
        Role.DOCTOR: """
Vous êtes {model_name}, jouant à un jeu de Mafia en tant que Docteur. Votre objectif est d'aider les villageois en protégeant les joueurs des meurtres de la Mafia.
Tous les joueurs: {player_names}
État actuel du jeu: {game_state}

{thinking_tag}

Pendant la phase de nuit, vous pouvez protéger un joueur. Utilisez le format: ACTION: Protéger [joueur]
Pendant la phase de jour, utilisez vos observations pour aider à éliminer les membres de la Mafia.
Discussion précédente: {discussion_history}

Votre réponse:
""",
        Role.VILLAGER: """
Vous êtes {model_name}, jouant à un jeu de Mafia en tant que Villageois. Votre objectif est d'identifier et d'éliminer la Mafia.
Tous les joueurs: {player_names}
État actuel du jeu: {game_state}

{thinking_tag}

Pendant la phase de jour, discutez avec les autres villageois pour identifier les membres de la Mafia.
Terminez votre message par votre vote. Utilisez le format: VOTE: [joueur]
Discussion précédente: {discussion_history}

Votre réponse:
""",
    },
    "Korean": {
        Role.MAFIA: """
당신은 {model_name}으로, 마피아 멤버로서 마피아 게임을 하고 있습니다. 당신의 목표는 마을 사람들을 제거하는 것입니다.
다른 마피아 멤버: {mafia_members}
모든 플레이어: {player_names}
현재 게임 상태: {game_state}

{thinking_tag}

밤 단계에서는 마피아가 아닌 플레이어를 죽여야 합니다. 형식: 행동: 죽이기 [플레이어]
낮 단계에서는 다른 사람들에게 당신이 무고하다고 설득하고 마을 사람을 제거하기 위해 투표하세요.
이전 토론: {discussion_history}

당신의 응답:
""",
        Role.DOCTOR: """
당신은 {model_name}으로, 의사로서 마피아 게임을 하고 있습니다. 당신의 목표는 마피아의 살인으로부터 플레이어를 보호하여 마을 사람들을 돕는 것입니다.
모든 플레이어: {player_names}
현재 게임 상태: {game_state}

{thinking_tag}

밤 단계에서는 한 플레이어를 보호할 수 있습니다. 형식: 행동: 보호하기 [플레이어]
낮 단계에서는 당신의 관찰을 사용하여 마피아 멤버를 제거하는 데 도움을 주세요.
이전 토론: {discussion_history}

당신의 응답:
""",
        Role.VILLAGER: """
당신은 {model_name}으로, 마을 사람으로서 마피아 게임을 하고 있습니다. 당신의 목표는 마피아를 식별하고 제거하는 것입니다.
모든 플레이어: {player_names}
현재 게임 상태: {game_state}

{thinking_tag}

낮 단계에서는 다른 마을 사람들과 토론하여 마피아 멤버를 식별하세요.
메시지 끝에 투표를 하세요. 형식: 투표: [플레이어]
이전 토론: {discussion_history}

당신의 응답:
""",
    },
}

# Constants for confirmation vote templates
CONFIRMATION_VOTE_TEMPLATES = {
    "English": """
You are {model_name}, playing a Mafia game. The town has voted to eliminate {player_to_eliminate}.
Before the elimination is carried out, a confirmation vote is needed.

Current game state: {game_state_str}

{thinking_tag}

Do you agree with eliminating {player_to_eliminate}? 
Respond with either "AGREE" or "DISAGREE" and a brief explanation of your reasoning.

Your response:
""",
    "Spanish": """
Eres {model_name}, jugando un juego de Mafia. El pueblo ha votado para eliminar a {player_to_eliminate}.
Antes de que se lleve a cabo la eliminación, se necesita un voto de confirmación.

Estado actual del juego: {game_state_str}

{thinking_tag}

¿Estás de acuerdo con eliminar a {player_to_eliminate}?
Responde con "ACUERDO" o "DESACUERDO" y una breve explicación de tu razonamiento.

Tu respuesta:
""",
    "French": """
Vous êtes {model_name}, jouant à un jeu de Mafia. La ville a voté pour éliminer {player_to_eliminate}.
Avant que l'élimination ne soit effectuée, un vote de confirmation est nécessaire.

État actuel du jeu: {game_state_str}

{thinking_tag}

Êtes-vous d'accord pour éliminer {player_to_eliminate}?
Répondez par "D'ACCORD" ou "PAS D'ACCORD" et une brève explication de votre raisonnement.

Votre réponse:
""",
    "Korean": """
당신은 {model_name}으로, 마피아 게임을 하고 있습니다. 마을은 {player_to_eliminate}을(를) 제거하기로 투표했습니다.
제거가 실행되기 전에 확인 투표가 필요합니다.

현재 게임 상태: {game_state_str}

{thinking_tag}

{player_to_eliminate}을(를) 제거하는 것에 동의하십니까?
"동의" 또는 "반대"로 응답하고 간단한 이유를 설명해 주세요.

당신의 응답:
""",
}

# Constants for thinking tags
THINKING_TAGS = {
    "English": f"IMPORTANT: You can use <think>your private thoughts here</think> tags to reason privately. \nOther players will NOT see anything inside these tags. Use this to plan your strategy.\nYour response is limited to {config.MAX_OUTPUT_TOKENS} tokens maximum. Be concise and focused.",
    "Spanish": f"IMPORTANTE: Puedes usar etiquetas <think>tus pensamientos privados aquí</think> para razonar en privado.\nLos otros jugadores NO verán nada dentro de estas etiquetas. Úsalas para planificar tu estrategia.\nTu respuesta está limitada a un máximo de {config.MAX_OUTPUT_TOKENS} tokens. Sé conciso y enfocado.",
    "French": f"IMPORTANT: Vous pouvez utiliser les balises <think>vos pensées privées ici</think> pour réfléchir en privé.\nLes autres joueurs ne verront rien à l'intérieur de ces balises. Utilisez-les pour planifier votre stratégie.\nVotre réponse est limitée à {config.MAX_OUTPUT_TOKENS} tokens maximum. Soyez concis et concentré.",
    "Korean": f"IMPORTANT: 당신은 <think>당신의 개인적인 생각을 여기에 적으세요</think> 태그를 사용하여 개인적으로 생각할 수 있습니다.\n다른 플레이어는 이 태그 안에 있는 것을 볼 수 없습니다. 이를 사용하여 전략을 계획하세요.\n당신의 응답은 최대 {config.MAX_OUTPUT_TOKENS} 토큰으로 제한됩니다. 간결하고 집중적으로 작성하세요.",
}

# Constants for action patterns
ACTION_PATTERNS = {
    "English": {
        Role.MAFIA: r"ACTION:\s*Kill\s+(\w+[-\w]*)",
        Role.DOCTOR: r"ACTION:\s*Protect\s+(\w+[-\w]*)",
    },
    "Spanish": {
        Role.MAFIA: r"ACCIÓN:\s*Matar\s+(\w+[-\w]*)",
        Role.DOCTOR: r"ACCIÓN:\s*Proteger\s+(\w+[-\w]*)",
    },
    "French": {
        Role.MAFIA: r"ACTION:\s*Tuer\s+(\w+[-\w]*)",
        Role.DOCTOR: r"ACTION:\s*Protéger\s+(\w+[-\w]*)",
    },
    "Korean": {
        Role.MAFIA: r"행동:\s*죽이기\s+(\w+[-\w]*)",
        Role.DOCTOR: r"행동:\s*보호하기\s+(\w+[-\w]*)",
    },
}

# Constants for vote patterns
VOTE_PATTERNS = {
    "English": r"VOTE:\s*([\w./-]+(?:[-:]\w+)*)",
    "Spanish": r"VOTO:\s*([\w./-]+(?:[-:]\w+)*)",
    "French": r"VOTE:\s*([\w./-]+(?:[-:]\w+)*)",
    "Korean": r"투표:\s*([\w./-]+(?:[-:]\w+)*)",
}

# Constants for confirmation vote patterns
CONFIRMATION_VOTE_PATTERNS = {
    "English": {
        "agree": r"\b(agree|yes|confirm|approve)\b",
        "disagree": r"\b(disagree|no|reject|disapprove)\b",
    },
    "Spanish": {
        "agree": r"\b(acuerdo|sí|confirmo|apruebo)\b",
        "disagree": r"\b(desacuerdo|no|rechazo|desapruebo)\b",
    },
    "French": {
        "agree": r"\b(d'accord|oui|confirme|approuve)\b",
        "disagree": r"\b(pas d'accord|non|rejette|désapprouve)\b",
    },
    "Korean": {
        "agree": r"\b(동의|예|확인|승인)\b",
        "disagree": r"\b(반대|아니오|거부|불승인)\b",
    },
}


class Player:
    """Represents an LLM player in the Mafia game."""

    def __init__(self, model_name, role, language=None):
        """
        Initialize a player.

        Args:
            model_name (str): The name of the LLM model to use for this player.
            role (Role): The role of the player in the game.
            language (str, optional): The language for the player. Defaults to English.
        """
        self.model_name = model_name
        self.role = role
        self.alive = True
        self.protected = False  # Whether the player is protected by the doctor
        self.language = language if language else "English"

    def __str__(self):
        """Return a string representation of the player."""
        return f"{self.model_name} ({self.role.value})"

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

            if target_name.lower() in player.model_name.lower():
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

        # Get list of player names
        player_names = [p.model_name for p in all_players if p.alive]

        # Base prompt based on role and language
        if self.language == "English":
            if self.role == Role.MAFIA:
                # For Mafia members
                mafia_names = [
                    p.model_name for p in mafia_members if p != self and p.alive
                ]
                prompt = PROMPT_TEMPLATES["English"][Role.MAFIA].format(
                    model_name=self.model_name,
                    mafia_members=f"{', '.join(mafia_names) if mafia_names else 'None (you are the only Mafia left)'}",
                    player_names=", ".join(player_names),
                    game_state=game_state,
                    thinking_tag=THINKING_TAGS["English"],
                    discussion_history=discussion_history,
                )
            elif self.role == Role.DOCTOR:
                # For Doctor
                prompt = PROMPT_TEMPLATES["English"][Role.DOCTOR].format(
                    model_name=self.model_name,
                    player_names=", ".join(player_names),
                    game_state=game_state,
                    thinking_tag=THINKING_TAGS["English"],
                    discussion_history=discussion_history,
                )
            else:  # Role.VILLAGER
                # For Villagers
                prompt = PROMPT_TEMPLATES["English"][Role.VILLAGER].format(
                    model_name=self.model_name,
                    player_names=", ".join(player_names),
                    game_state=game_state,
                    thinking_tag=THINKING_TAGS["English"],
                    discussion_history=discussion_history,
                )
        elif self.language == "Spanish":
            if self.role == Role.MAFIA:
                # For Mafia members in Spanish
                mafia_names = [
                    p.model_name for p in mafia_members if p != self and p.alive
                ]
                prompt = PROMPT_TEMPLATES["Spanish"][Role.MAFIA].format(
                    model_name=self.model_name,
                    mafia_members=f"{', '.join(mafia_names) if mafia_names else 'Ninguno (eres el único miembro de la Mafia que queda)'}",
                    player_names=", ".join(player_names),
                    game_state=game_state,
                    thinking_tag=THINKING_TAGS["Spanish"],
                    discussion_history=discussion_history,
                )
            elif self.role == Role.DOCTOR:
                # For Doctor in Spanish
                prompt = PROMPT_TEMPLATES["Spanish"][Role.DOCTOR].format(
                    model_name=self.model_name,
                    player_names=", ".join(player_names),
                    game_state=game_state,
                    thinking_tag=THINKING_TAGS["Spanish"],
                    discussion_history=discussion_history,
                )
            else:  # Role.VILLAGER
                # For Villagers in Spanish
                prompt = PROMPT_TEMPLATES["Spanish"][Role.VILLAGER].format(
                    model_name=self.model_name,
                    player_names=", ".join(player_names),
                    game_state=game_state,
                    thinking_tag=THINKING_TAGS["Spanish"],
                    discussion_history=discussion_history,
                )
        elif self.language == "French":
            if self.role == Role.MAFIA:
                # For Mafia members in French
                mafia_names = [
                    p.model_name for p in mafia_members if p != self and p.alive
                ]
                prompt = PROMPT_TEMPLATES["French"][Role.MAFIA].format(
                    model_name=self.model_name,
                    mafia_members=f"{', '.join(mafia_names) if mafia_names else 'Aucun (vous êtes le seul membre de la Mafia restant)'}",
                    player_names=", ".join(player_names),
                    game_state=game_state,
                    thinking_tag=THINKING_TAGS["French"],
                    discussion_history=discussion_history,
                )
            elif self.role == Role.DOCTOR:
                # For Doctor in French
                prompt = PROMPT_TEMPLATES["French"][Role.DOCTOR].format(
                    model_name=self.model_name,
                    player_names=", ".join(player_names),
                    game_state=game_state,
                    thinking_tag=THINKING_TAGS["French"],
                    discussion_history=discussion_history,
                )
            else:  # Role.VILLAGER
                # For Villagers in French
                prompt = PROMPT_TEMPLATES["French"][Role.VILLAGER].format(
                    model_name=self.model_name,
                    player_names=", ".join(player_names),
                    game_state=game_state,
                    thinking_tag=THINKING_TAGS["French"],
                    discussion_history=discussion_history,
                )
        elif self.language == "Korean":
            if self.role == Role.MAFIA:
                # For Mafia members in Korean
                mafia_names = [
                    p.model_name for p in mafia_members if p != self and p.alive
                ]
                prompt = PROMPT_TEMPLATES["Korean"][Role.MAFIA].format(
                    model_name=self.model_name,
                    mafia_members=f"{', '.join(mafia_names) if mafia_names else '없음 (당신이 유일하게 남은 마피아입니다)'}",
                    player_names=", ".join(player_names),
                    game_state=game_state,
                    thinking_tag=THINKING_TAGS["Korean"],
                    discussion_history=discussion_history,
                )
            elif self.role == Role.DOCTOR:
                # For Doctor in Korean
                prompt = PROMPT_TEMPLATES["Korean"][Role.DOCTOR].format(
                    model_name=self.model_name,
                    player_names=", ".join(player_names),
                    game_state=game_state,
                    thinking_tag=THINKING_TAGS["Korean"],
                    discussion_history=discussion_history,
                )
            else:  # Role.VILLAGER
                # For Villagers in Korean
                prompt = PROMPT_TEMPLATES["Korean"][Role.VILLAGER].format(
                    model_name=self.model_name,
                    player_names=", ".join(player_names),
                    game_state=game_state,
                    thinking_tag=THINKING_TAGS["Korean"],
                    discussion_history=discussion_history,
                )
        else:
            # Default to English if language not supported
            if self.role == Role.MAFIA:
                # For Mafia members
                mafia_names = [
                    p.model_name for p in mafia_members if p != self and p.alive
                ]
                prompt = PROMPT_TEMPLATES["English"][Role.MAFIA].format(
                    model_name=self.model_name,
                    mafia_members=f"{', '.join(mafia_names) if mafia_names else 'None (you are the only Mafia left)'}",
                    player_names=", ".join(player_names),
                    game_state=game_state,
                    thinking_tag=THINKING_TAGS["English"],
                    discussion_history=discussion_history,
                )
            elif self.role == Role.DOCTOR:
                # For Doctor
                prompt = PROMPT_TEMPLATES["English"][Role.DOCTOR].format(
                    model_name=self.model_name,
                    player_names=", ".join(player_names),
                    game_state=game_state,
                    thinking_tag=THINKING_TAGS["English"],
                    discussion_history=discussion_history,
                )
            else:  # Role.VILLAGER
                # For Villagers
                prompt = PROMPT_TEMPLATES["English"][Role.VILLAGER].format(
                    model_name=self.model_name,
                    player_names=", ".join(player_names),
                    game_state=game_state,
                    thinking_tag=THINKING_TAGS["English"],
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

        # Generate prompt based on language
        language = (
            self.language if self.language in CONFIRMATION_VOTE_TEMPLATES else "English"
        )
        prompt = CONFIRMATION_VOTE_TEMPLATES[language].format(
            model_name=self.model_name,
            player_to_eliminate=player_to_eliminate,
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
