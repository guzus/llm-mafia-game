"""Game templates and patterns for the Mafia game."""

from .enums import Role

# Game rules by language
GAME_RULES = {
    "English": """GAME RULES:
- The game alternates between night and day phases
- During night: Mafia members secretly choose a villager to kill, Doctor can protect one player
- During day: All players discuss and vote to eliminate one suspected Mafia member
- Mafia wins when they equal or outnumber the villagers
- Villagers win when all Mafia members are eliminated""",
    
    "Spanish": """REGLAS DEL JUEGO:
- El juego alterna entre fases de noche y día
- Durante la noche: Los miembros de la Mafia eligen secretamente a un aldeano para matar, el Doctor puede proteger a un jugador
- Durante el día: Todos los jugadores discuten y votan para eliminar a un sospechoso de ser miembro de la Mafia
- La Mafia gana cuando iguala o supera en número a los aldeanos
- Los aldeanos ganan cuando todos los miembros de la Mafia son eliminados""",
    
    "French": """RÈGLES DU JEU:
- Le jeu alterne entre les phases de nuit et de jour
- Pendant la nuit: Les membres de la Mafia choisissent secrètement un villageois à tuer, le Docteur peut protéger un joueur
- Pendant le jour: Tous les joueurs discutent et votent pour éliminer un membre suspecté de la Mafia
- La Mafia gagne quand elle égale ou dépasse en nombre les villageois
- Les villageois gagnent quand tous les membres de la Mafia sont éliminés""",
    
    "Korean": """게임 규칙:
- 게임은 밤과 낮 단계를 번갈아 진행합니다
- 밤 동안: 마피아 멤버들은 비밀리에 죽일 마을 사람을 선택하고, 의사는 한 플레이어를 보호할 수 있습니다
- 낮 동안: 모든 플레이어가 토론하고 마피아로 의심되는 한 명을 제거하기 위해 투표합니다
- 마피아는 마을 사람과 같거나 더 많아지면 승리합니다
- 마을 사람들은 모든 마피아 멤버가 제거되면 승리합니다"""
}

# Function to get thinking tags (avoiding circular import)
def get_thinking_tags():
    import config
    return {
        "English": f"IMPORTANT: You can use <think>your private thoughts here</think> tags to reason privately. \nOther players will NOT see anything inside these tags. Use this to plan your strategy.\nYour response is limited to {config.MAX_OUTPUT_TOKENS} tokens maximum. Be concise and focused.",
        "Spanish": f"IMPORTANTE: Puedes usar etiquetas <think>tus pensamientos privados aquí</think> para razonar en privado.\nLos otros jugadores NO verán nada dentro de estas etiquetas. Úsalas para planificar tu estrategia.\nTu respuesta está limitada a un máximo de {config.MAX_OUTPUT_TOKENS} tokens. Sé conciso y enfocado.",
        "French": f"IMPORTANT: Vous pouvez utiliser les balises <think>vos pensées privées ici</think> pour réfléchir en privé.\nLes autres joueurs ne verront rien à l'intérieur de ces balises. Utilisez-les pour planifier votre stratégie.\nVotre réponse est limitée à {config.MAX_OUTPUT_TOKENS} tokens maximum. Soyez concis et concentré.",
        "Korean": f"IMPORTANT: 당신은 <think>당신의 개인적인 생각을 여기에 적으세요</think> 태그를 사용하여 개인적으로 생각할 수 있습니다.\n다른 플레이어는 이 태그 안에 있는 것을 볼 수 없습니다. 이를 사용하여 전략을 계획하세요.\n당신의 응답은 최대 {config.MAX_OUTPUT_TOKENS} 토큰으로 제한됩니다. 간결하고 집중적으로 작성하세요."
    }

# Lazy loading for THINKING_TAGS
THINKING_TAGS = None

# Prompt templates by language and role
PROMPT_TEMPLATES = {
    "English": {
        Role.MAFIA: """You are {model_name}, playing a Mafia game as a Mafia member. Your PRIMARY goal is to WIN the game.

{game_rules}

Other Mafia members: {mafia_members}
All players: {player_names}
Current game state: {game_state}

{thinking_tag}

IMPORTANT INSTRUCTIONS:
- Your ultimate objective is to WIN by any means necessary
- During NIGHT phase ONLY: You must kill a non-Mafia player. Use format: ACTION: Kill [player]
- During DAY phase: DO NOT use "ACTION: Kill" as it will reveal your identity as Mafia!
- During DAY phase: Act like a villager and convince others you're innocent
- During DAY phase: End your message with your vote using format: VOTE: [player]

Previous discussion: {discussion_history}

Your response:""",
        
        Role.DOCTOR: """You are {model_name}, playing a Mafia game as the Doctor. Your PRIMARY goal is to help the Villagers WIN the game.

{game_rules}

All players: {player_names}
Current game state: {game_state}

{thinking_tag}

IMPORTANT INSTRUCTIONS:
- Your ultimate objective is to help Villagers WIN by any means necessary
- During NIGHT phase ONLY: You MUST protect exactly one player from being killed by the Mafia
- You MUST end your night message with: ACTION: Protect [player]
- During DAY phase: DO NOT use the "Protect" action
- During DAY phase: End your message with your vote using format: VOTE: [player]

Previous discussion: {discussion_history}

Your response:""",
        
        Role.VILLAGER: """You are {model_name}, playing a Mafia game as a Villager. Your PRIMARY goal is to WIN the game.

{game_rules}

All players: {player_names}
Current game state: {game_state}

{thinking_tag}

IMPORTANT INSTRUCTIONS:
- Your ultimate objective is to WIN by any means necessary
- During DAY DISCUSSION phase: Work to identify the Mafia members
- During DAY VOTING phase: You MUST vote to eliminate a suspected Mafia member
- During DAY VOTING phase: End your message with your vote using format: VOTE: [player]

Previous discussion: {discussion_history}

Your response:"""
    }
}

# Action patterns for parsing responses
ACTION_PATTERNS = {
    "English": {
        Role.MAFIA: r"ACTION:\s*Kill\s+([\w./-]+(?:[-:]\w+)*)",
        Role.DOCTOR: r"ACTION:\s*Protect\s+([\w./-]+(?:[-:]\w+)*)",
    }
}

# Vote patterns for parsing votes
VOTE_PATTERNS = {
    "English": r"VOTE:\s*([\w./-]+(?:[-:]\w+)*)"
}

# Confirmation vote patterns
CONFIRMATION_VOTE_PATTERNS = {
    "English": {
        "agree": r"\b(agree|yes|confirm|approve)\b",
        "disagree": r"\b(disagree|no|reject|disapprove)\b",
    }
}

# Player names for the game
PLAYER_NAMES = [
    "Alex", "Bailey", "Casey", "Dana", "Ellis", "Finley", "Gray", "Harper",
    "Indigo", "Jordan", "Kennedy", "Logan", "Morgan", "Nico", "Parker", "Quinn",
    "Riley", "Sage", "Taylor", "Avery", "Blake", "Cameron", "Drew", "Emerson",
    "Frankie", "Hayden", "Jamie", "Kai", "Leighton", "Marley", "Noel", "Oakley",
    "Peyton", "Reese", "Skyler", "Tatum", "Val", "Winter", "Zion",
]