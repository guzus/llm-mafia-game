import { GameState, GamePhase } from "./types";

export function addMessage(
  gameState: GameState,
  text: string,
  type: "player" | "llm" | "system"
) {
  const chatContainer = document.getElementById("chat-container");
  if (chatContainer) {
    const messageElement = document.createElement("div");
    messageElement.classList.add("message", `${type}-message`);
    messageElement.textContent = text;
    chatContainer.appendChild(messageElement);
    chatContainer.scrollTop = chatContainer.scrollHeight;

    gameState.messages.push({
      text,
      sender: type === "player" ? "player" : type === "llm" ? "npc" : "system",
      timestamp: new Date().toISOString(),
    });
  }
}

export function updateGameStatus(gameState: GameState) {
  const statusElement = document.getElementById("game-status");
  if (statusElement) {
    statusElement.textContent = gameState.winner
      ? `Game Over - ${gameState.winner} Win!`
      : `Day ${gameState.day} - ${gameState.phase} Phase`;
  }
}

export function checkWinConditions(gameState: GameState) {
  const { mafia, villager, detective, doctor } = gameState.aliveCount;

  if (mafia >= villager + detective + doctor) {
    gameState.winner = "Mafia";
    gameState.phase = GamePhase.GAME_OVER;
    updateGameStatus(gameState);
    addMessage(gameState, "The Mafia has taken over the village! Mafia wins!", "system");
  } else if (mafia === 0) {
    gameState.winner = "Village";
    gameState.phase = GamePhase.GAME_OVER;
    updateGameStatus(gameState);
    addMessage(gameState, "All members of the Mafia have been eliminated! Village wins!", "system");
  }
}

export function getRandomElement<T>(array: T[]): T {
  return array[Math.floor(Math.random() * array.length)];
}

export function shuffleArray<T>(array: T[]): T[] {
  const shuffled = [...array];
  for (let i = shuffled.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [shuffled[i], shuffled[j]] = [shuffled[j], shuffled[i]];
  }
  return shuffled;
}
