import * as THREE from "../node_modules/@types/three";
import { OrbitControls } from "three/examples/jsm/controls/OrbitControls.js";
import { GameState, Player, Role, GamePhase } from "./types";
import { setupScene } from "./scene";
import { createCharacter } from "./character";
import { handleChat } from "./chat";

// Initialize game state
const gameState: GameState = {
  phase: GamePhase.SETUP,
  day: 1,
  players: [],
  messages: [],
  aliveCount: {
    mafia: 0,
    villager: 0,
    detective: 0,
    doctor: 0,
  },
  playerRole: Role.VILLAGER, // Default role for the human player
  winner: null,
};

// Initialize Three.js scene
const { scene, camera, renderer, controls } = setupScene();

// Add characters to the scene
const playerCharacter = createCharacter(Role.VILLAGER, 0, scene, true);
gameState.players.push({
  id: "player",
  name: "You",
  role: Role.VILLAGER,
  isAlive: true,
  character: playerCharacter,
  isHuman: true,
});

// Add LLM characters (NPCs)
const roles = [
  Role.MAFIA,
  Role.MAFIA,
  Role.DETECTIVE,
  Role.DOCTOR,
  Role.VILLAGER,
  Role.VILLAGER,
];
roles.forEach((role, index) => {
  const character = createCharacter(role, index + 1, scene, false);
  gameState.players.push({
    id: `npc-${index + 1}`,
    name: `Player ${index + 1}`,
    role: role,
    isAlive: true,
    character: character,
    isHuman: false,
  });

  // Update alive count
  gameState.aliveCount[
    role.toLowerCase() as keyof typeof gameState.aliveCount
  ]++;
});

// Update game status display
function updateGameStatus() {
  const statusElement = document.getElementById("game-status");
  if (statusElement) {
    if (gameState.winner) {
      statusElement.textContent = `Game Over - ${gameState.winner} Win!`;
    } else {
      statusElement.textContent = `Day ${gameState.day} - ${gameState.phase} Phase`;
    }
  }
}

// Animation loop
function animate() {
  requestAnimationFrame(animate);

  // Update characters
  gameState.players.forEach((player) => {
    if (player.character && player.character.update) {
      player.character.update();
    }
  });

  controls.update();
  renderer.render(scene, camera);
}

// Start the game
function startGame() {
  // Set up chat handlers
  handleChat(gameState);

  // Start animation loop
  animate();

  // Update game status
  updateGameStatus();

  // Add system message
  addMessage("Welcome to LLM Mafia! The game is about to begin...", "system");

  // Start the game with night phase
  setTimeout(() => {
    gameState.phase = GamePhase.NIGHT;
    updateGameStatus();
    addMessage(
      "Night falls on the village. The Mafia, Detective, and Doctor are active.",
      "system"
    );

    // Simulate night actions from NPCs
    simulateNightActions();

    // Move to day phase after night actions
    setTimeout(() => {
      gameState.phase = GamePhase.DAY;
      updateGameStatus();
      addMessage("The sun rises. Time for discussion.", "system");
    }, 5000);
  }, 3000);
}

// Add message to chat
function addMessage(text: string, type: "player" | "llm" | "system") {
  const chatContainer = document.getElementById("chat-container");
  if (chatContainer) {
    const messageElement = document.createElement("div");
    messageElement.classList.add("message", `${type}-message`);
    messageElement.textContent = text;
    chatContainer.appendChild(messageElement);
    chatContainer.scrollTop = chatContainer.scrollHeight;

    // Add to game state
    gameState.messages.push({
      text,
      sender: type === "player" ? "player" : type === "llm" ? "npc" : "system",
      timestamp: new Date().toISOString(),
    });
  }
}

// Simulate night actions from NPCs
function simulateNightActions() {
  // This would be replaced with actual LLM-based decision making
  // For now, we'll just simulate some basic actions

  // Mafia chooses a target
  const mafiaPlayers = gameState.players.filter(
    (p) => p.role === Role.MAFIA && p.isAlive
  );
  const nonMafiaPlayers = gameState.players.filter(
    (p) => p.role !== Role.MAFIA && p.isAlive
  );

  if (mafiaPlayers.length > 0 && nonMafiaPlayers.length > 0) {
    const randomTarget =
      nonMafiaPlayers[Math.floor(Math.random() * nonMafiaPlayers.length)];
    addMessage(`The Mafia chose to target ${randomTarget.name}`, "system");
  }

  // Detective investigates someone
  const detective = gameState.players.find(
    (p) => p.role === Role.DETECTIVE && p.isAlive
  );
  if (detective) {
    const otherPlayers = gameState.players.filter(
      (p) => p.id !== detective.id && p.isAlive
    );
    if (otherPlayers.length > 0) {
      const investigateTarget =
        otherPlayers[Math.floor(Math.random() * otherPlayers.length)];
      addMessage(
        `The Detective chose to investigate ${investigateTarget.name}`,
        "system"
      );
    }
  }

  // Doctor protects someone
  const doctor = gameState.players.find(
    (p) => p.role === Role.DOCTOR && p.isAlive
  );
  if (doctor) {
    const otherPlayers = gameState.players.filter(
      (p) => p.id !== doctor.id && p.isAlive
    );
    if (otherPlayers.length > 0) {
      const protectTarget =
        otherPlayers[Math.floor(Math.random() * otherPlayers.length)];
      addMessage(`The Doctor chose to protect ${protectTarget.name}`, "system");
    }
  }
}

// Initialize the game when the page loads
window.addEventListener("load", startGame);

// Export for debugging
(window as any).gameState = gameState;
