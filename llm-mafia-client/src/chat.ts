import { GameState, GamePhase, Role } from "./types";
import { addMessage, updateGameStatus, checkWinConditions, getRandomElement, shuffleArray } from "./utils";
import { simulateNightActions, processVoting, processNightAction } from "./game-logic";

const ROLE_RESPONSES = {
  [Role.MAFIA]: [
    "I think we should focus on finding the real mafia.",
    "I was just checking on the village last night, I'm innocent.",
    "I suspect Player 3, they've been very quiet.",
    "I'm a villager, I promise!",
    "Let's work together to find the mafia.",
  ],
  [Role.VILLAGER]: [
    "I'm just a simple villager trying to survive.",
    "I think Player 2 is acting suspicious.",
    "I didn't see anything unusual last night.",
    "We need to be careful who we vote for.",
    "I trust Player 4, they seem honest.",
  ],
  [Role.DETECTIVE]: [
    "I have some information that might help us.",
    "Based on my observations, Player 5 might be suspicious.",
    "Let's think logically about this situation.",
    "I was watching carefully last night.",
    "I think we should vote for Player 1.",
  ],
  [Role.DOCTOR]: [
    "I want to help keep the village safe.",
    "I think we should protect each other.",
    "Player 6 seems trustworthy to me.",
    "I'm concerned about the safety of our village.",
    "Let's be careful with our accusations.",
  ],
};

function getRandomResponse(role: Role): string {
  return getRandomElement(ROLE_RESPONSES[role]);
}

function sendPlayerMessage(gameState: GameState, message: string) {
  addMessage(gameState, message, "player");
  processPlayerMessage(gameState, message);
  setTimeout(() => getNPCResponses(gameState), 1000);
}

function processPlayerMessage(gameState: GameState, message: string) {
  if (gameState.phase === GamePhase.DAY || gameState.phase === GamePhase.VOTING) {
    handleDayPhaseCommand(gameState, message);
  } else if (gameState.phase === GamePhase.NIGHT) {
    handleNightPhaseCommand(gameState, message);
  }
}

function handleDayPhaseCommand(gameState: GameState, message: string) {
  const voteMatch = message.match(/vote (?:for )?(?:player )?(\d+)/i);
  if (!voteMatch) return;

  const playerNumber = parseInt(voteMatch[1]);
  const targetPlayer = gameState.players.find(p => p.name === `Player ${playerNumber}`);

  if (targetPlayer) {
    addMessage(gameState, `You voted for ${targetPlayer.name}`, "system");

    if (gameState.phase === GamePhase.DAY) {
      gameState.phase = GamePhase.VOTING;
      updateGameStatus(gameState);
    }

    processVoting(gameState, targetPlayer, () => handleVotingComplete(gameState));
  } else {
    addMessage(gameState, `Player ${playerNumber} not found`, "system");
  }
}

function handleNightPhaseCommand(gameState: GameState, message: string) {
  const { playerRole, players } = gameState;

  const commands = [
    { role: Role.MAFIA, pattern: /kill (?:player )?(\d+)/i, action: "kill" as const },
    { role: Role.DETECTIVE, pattern: /investigate (?:player )?(\d+)/i, action: "investigate" as const },
    { role: Role.DOCTOR, pattern: /save (?:player )?(\d+)/i, action: "save" as const },
  ];

  for (const { role, pattern, action } of commands) {
    if (playerRole !== role) continue;

    const match = message.match(pattern);
    if (match) {
      const playerNumber = parseInt(match[1]);
      const targetPlayer = players.find(p => p.name === `Player ${playerNumber}`);
      if (targetPlayer) {
        processNightAction(gameState, action, targetPlayer);
      }
      break;
    }
  }
}

function handleVotingComplete(gameState: GameState) {
  checkWinConditions(gameState);

  if (!gameState.winner) {
    setTimeout(() => {
      gameState.phase = GamePhase.NIGHT;
      gameState.day++;
      updateGameStatus(gameState);
      addMessage(gameState, "Night falls on the village...", "system");

      const result = simulateNightActions(gameState);

      setTimeout(() => {
        if (result) {
          const msg = result.targetKilled
            ? `${result.target.name} was killed during the night!`
            : "Everyone survived the night!";
          addMessage(gameState, msg, "system");
          if (result.targetKilled) checkWinConditions(gameState);
        }

        if (!gameState.winner) {
          gameState.phase = GamePhase.DAY;
          updateGameStatus(gameState);
          addMessage(gameState, "The sun rises. Time for discussion.", "system");
        }
      }, 5000);
    }, 2000);
  }
}

function getNPCResponses(gameState: GameState) {
  if (gameState.phase !== GamePhase.DAY) return;

  const aliveNPCs = gameState.players.filter(p => !p.isHuman && p.isAlive);
  const responseCount = Math.min(Math.floor(Math.random() * 3) + 1, aliveNPCs.length);
  const respondingNPCs = shuffleArray(aliveNPCs).slice(0, responseCount);

  respondingNPCs.forEach((npc, index) => {
    setTimeout(() => {
      const response = getRandomResponse(npc.role);
      addMessage(gameState, `${npc.name}: ${response}`, "llm");
    }, 1000 * (index + 1));
  });
}

export function handleChat(gameState: GameState) {
  const chatInput = document.getElementById("chat-input") as HTMLInputElement;
  const sendButton = document.getElementById("send-button") as HTMLButtonElement;

  if (!chatInput || !sendButton) {
    console.error("Chat elements not found");
    return;
  }

  const sendMessage = () => {
    const message = chatInput.value.trim();
    if (message) {
      sendPlayerMessage(gameState, message);
      chatInput.value = "";
    }
  };

  sendButton.addEventListener("click", sendMessage);
  chatInput.addEventListener("keypress", (e) => {
    if (e.key === "Enter") sendMessage();
  });
}
