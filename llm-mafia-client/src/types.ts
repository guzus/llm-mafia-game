import * as THREE from "../node_modules/@types/three";

export enum Role {
  VILLAGER = "VILLAGER",
  MAFIA = "MAFIA",
  DETECTIVE = "DETECTIVE",
  DOCTOR = "DOCTOR",
}

export enum GamePhase {
  SETUP = "SETUP",
  DAY = "DAY",
  VOTING = "VOTING",
  NIGHT = "NIGHT",
  GAME_OVER = "GAME_OVER",
}

export interface Character {
  model: THREE.Group;
  position: THREE.Vector3;
  update: () => void;
}

export interface Message {
  text: string;
  sender: "player" | "npc" | "system";
  timestamp: string;
}

export interface Player {
  id: string;
  name: string;
  role: Role;
  isAlive: boolean;
  character?: Character;
  isHuman: boolean;
}

export interface GameState {
  phase: GamePhase;
  day: number;
  players: Player[];
  messages: Message[];
  aliveCount: {
    mafia: number;
    villager: number;
    detective: number;
    doctor: number;
  };
  playerRole: Role;
  winner: "Mafia" | "Village" | null;
}
