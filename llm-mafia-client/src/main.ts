import * as THREE from "three";
import { OrbitControls } from "three/examples/jsm/controls/OrbitControls.js";
import { GameState, Player, Role, GamePhase } from "./types";
import { setupScene } from "./scene";
import { createCharacter } from "./character";
import { handleChat } from "./chat";
import { addMessage, updateGameStatus } from "./utils";
import { simulateNightActions } from "./game-logic";

const gameState: GameState = {
  phase: GamePhase.SETUP,
  day: 1,
  players: [],
  messages: [],
  aliveCount: { mafia: 0, villager: 0, detective: 0, doctor: 0 },
  playerRole: Role.VILLAGER,
  winner: null,
};

const { scene, camera, renderer, controls } = setupScene();

const playerCharacter = createCharacter(Role.VILLAGER, 0, scene, true);
gameState.players.push({
  id: "player",
  name: "You",
  role: Role.VILLAGER,
  isAlive: true,
  character: playerCharacter,
  isHuman: true,
});

const roles = [Role.MAFIA, Role.MAFIA, Role.DETECTIVE, Role.DOCTOR, Role.VILLAGER, Role.VILLAGER];
roles.forEach((role, index) => {
  const character = createCharacter(role, index + 1, scene, false);
  gameState.players.push({
    id: `npc-${index + 1}`,
    name: `Player ${index + 1}`,
    role,
    isAlive: true,
    character,
    isHuman: false,
  });

  gameState.aliveCount[role.toLowerCase() as keyof typeof gameState.aliveCount]++;
});

function animate() {
  requestAnimationFrame(animate);
  gameState.players.forEach(player => {
    if (player.character?.update) player.character.update();
  });
  controls.update();
  renderer.render(scene, camera);
}

function startGame() {
  handleChat(gameState);
  animate();
  updateGameStatus(gameState);
  addMessage(gameState, "Welcome to LLM Mafia! The game is about to begin...", "system");

  setTimeout(() => {
    gameState.phase = GamePhase.NIGHT;
    updateGameStatus(gameState);
    addMessage(gameState, "Night falls on the village. The Mafia, Detective, and Doctor are active.", "system");
    simulateNightActions(gameState);

    setTimeout(() => {
      gameState.phase = GamePhase.DAY;
      updateGameStatus(gameState);
      addMessage(gameState, "The sun rises. Time for discussion.", "system");
    }, 5000);
  }, 3000);
}

window.addEventListener("load", startGame);
(window as any).gameState = gameState;
