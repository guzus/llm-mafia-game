"""
Game templates and constants for the LLM Mafia Game Competition.
This file contains all the templates, patterns, and constants used in the game.
"""

import config
from enum import Enum


class Role(Enum):
    """Enum for player roles in the game."""

    MAFIA = "Mafia"
    VILLAGER = "Villager"
    DOCTOR = "Doctor"


# Constants for game rules by language
GAME_RULES = {
    "English": """
GAME RULES:
- The game alternates between night and day phases
- During night: Mafia members secretly choose a villager to kill, Doctor can protect one player
- During day: All players discuss and vote to eliminate one suspected Mafia member
- Mafia wins when they equal or outnumber the villagers
- Villagers win when all Mafia members are eliminated
""",
    "Spanish": """
REGLAS DEL JUEGO:
- El juego alterna entre fases de noche y día
- Durante la noche: Los miembros de la Mafia eligen secretamente a un aldeano para matar, el Doctor puede proteger a un jugador
- Durante el día: Todos los jugadores discuten y votan para eliminar a un sospechoso de ser miembro de la Mafia
- La Mafia gana cuando iguala o supera en número a los aldeanos
- Los aldeanos ganan cuando todos los miembros de la Mafia son eliminados
""",
    "French": """
RÈGLES DU JEU:
- Le jeu alterne entre les phases de nuit et de jour
- Pendant la nuit: Les membres de la Mafia choisissent secrètement un villageois à tuer, le Docteur peut protéger un joueur
- Pendant le jour: Tous les joueurs discutent et votent pour éliminer un membre suspecté de la Mafia
- La Mafia gagne quand elle égale ou dépasse en nombre les villageois
- Les villageois gagnent quand tous les membres de la Mafia sont éliminés
""",
    "Korean": """
게임 규칙:
- 게임은 밤과 낮 단계를 번갈아 진행합니다
- 밤 동안: 마피아 멤버들은 비밀리에 죽일 마을 사람을 선택하고, 의사는 한 플레이어를 보호할 수 있습니다
- 낮 동안: 모든 플레이어가 토론하고 마피아로 의심되는 한 명을 제거하기 위해 투표합니다
- 마피아는 마을 사람과 같거나 더 많아지면 승리합니다
- 마을 사람들은 모든 마피아 멤버가 제거되면 승리합니다
""",
}

# Constants for confirmation vote explanations
CONFIRMATION_VOTE_EXPLANATIONS = {
    "English": """
ABOUT CONFIRMATION VOTES:
- This is the final chance to reconsider the town's decision
- If the majority agrees, {player_to_eliminate} will be eliminated
- If the majority disagrees, no one will be eliminated this round
""",
    "Spanish": """
SOBRE LOS VOTOS DE CONFIRMACIÓN:
- Esta es la última oportunidad para reconsiderar la decisión del pueblo
- Si la mayoría está de acuerdo, {player_to_eliminate} será eliminado
- Si la mayoría está en desacuerdo, nadie será eliminado en esta ronda
""",
    "French": """
À PROPOS DES VOTES DE CONFIRMATION:
- C'est la dernière chance de reconsidérer la décision de la ville
- Si la majorité est d'accord, {player_to_eliminate} sera éliminé
- Si la majorité n'est pas d'accord, personne ne sera éliminé ce tour-ci
""",
    "Korean": """
확인 투표에 대하여:
- 이것은 마을의 결정을 재고할 수 있는 마지막 기회입니다
- 과반수가 동의하면 {player_to_eliminate}이(가) 제거됩니다
- 과반수가 반대하면 이번 라운드에서는 아무도 제거되지 않습니다
""",
}

# Constants for prompt templates
PROMPT_TEMPLATES = {
    "English": {
        Role.MAFIA: """
You are {model_name}, playing a Mafia game as a Mafia member. Your goal is to eliminate the villagers.

{game_rules}

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

{game_rules}

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

{game_rules}

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

{game_rules}

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

{game_rules}

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

{game_rules}

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

{game_rules}

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

{game_rules}

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

{game_rules}

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

{game_rules}

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

{game_rules}

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

{game_rules}

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

{confirmation_explanation}

Current game state: {game_state_str}

{thinking_tag}

Do you agree with eliminating {player_to_eliminate}? 
Respond with either "AGREE" or "DISAGREE" and a brief explanation of your reasoning.

Your response:
""",
    "Spanish": """
Eres {model_name}, jugando un juego de Mafia. El pueblo ha votado para eliminar a {player_to_eliminate}.
Antes de que se lleve a cabo la eliminación, se necesita un voto de confirmación.

{confirmation_explanation}

Estado actual del juego: {game_state_str}

{thinking_tag}

¿Estás de acuerdo con eliminar a {player_to_eliminate}?
Responde con "ACUERDO" o "DESACUERDO" y una breve explicación de tu razonamiento.

Tu respuesta:
""",
    "French": """
Vous êtes {model_name}, jouant à un jeu de Mafia. La ville a voté pour éliminer {player_to_eliminate}.
Avant que l'élimination ne soit effectuée, un vote de confirmation est nécessaire.

{confirmation_explanation}

État actuel du jeu: {game_state_str}

{thinking_tag}

Êtes-vous d'accord pour éliminer {player_to_eliminate}?
Répondez par "D'ACCORD" ou "PAS D'ACCORD" et une brève explication de votre raisonnement.

Votre réponse:
""",
    "Korean": """
당신은 {model_name}으로, 마피아 게임을 하고 있습니다. 마을은 {player_to_eliminate}을(를) 제거하기로 투표했습니다.
제거가 실행되기 전에 확인 투표가 필요합니다.

{confirmation_explanation}

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
        Role.MAFIA: r"ACTION:\s*Kill\s+([\w./-]+(?:[-:]\w+)*)",
        Role.DOCTOR: r"ACTION:\s*Protect\s+([\w./-]+(?:[-:]\w+)*)",
    },
    "Spanish": {
        Role.MAFIA: r"ACCIÓN:\s*Matar\s+([\w./-]+(?:[-:]\w+)*)",
        Role.DOCTOR: r"ACCIÓN:\s*Proteger\s+([\w./-]+(?:[-:]\w+)*)",
    },
    "French": {
        Role.MAFIA: r"ACTION:\s*Tuer\s+([\w./-]+(?:[-:]\w+)*)",
        Role.DOCTOR: r"ACTION:\s*Protéger\s+([\w./-]+(?:[-:]\w+)*)",
    },
    "Korean": {
        Role.MAFIA: r"행동:\s*죽이기\s+([\w./-]+(?:[-:]\w+)*)",
        Role.DOCTOR: r"행동:\s*보호하기\s+([\w./-]+(?:[-:]\w+)*)",
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
