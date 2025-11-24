import { GameState, Role, Player } from "./types";
import { addMessage, getRandomElement } from "./utils";

export function simulateNightActions(gameState: GameState) {
  const { players, playerRole } = gameState;

  const mafiaPlayers = players.filter(p => p.role === Role.MAFIA && p.isAlive);
  const nonMafiaPlayers = players.filter(p => p.role !== Role.MAFIA && p.isAlive);

  if (mafiaPlayers.length > 0 && nonMafiaPlayers.length > 0) {
    const target = getRandomElement(nonMafiaPlayers);

    if (playerRole === Role.MAFIA) {
      addMessage(gameState, `The Mafia chose to target ${target.name}`, "system");
    }

    let targetKilled = true;
    const doctorPlayers = players.filter(p => p.role === Role.DOCTOR && p.isAlive);

    if (doctorPlayers.length > 0 && Math.random() < 0.3) {
      targetKilled = false;
      if (playerRole === Role.DOCTOR) {
        addMessage(gameState, `You successfully protected ${target.name} from the Mafia!`, "system");
      }
    }

    if (targetKilled) {
      target.isAlive = false;
      gameState.aliveCount[target.role.toLowerCase() as keyof typeof gameState.aliveCount]--;
    }

    return { target, targetKilled };
  }

  return null;
}

export function processVoting(
  gameState: GameState,
  targetPlayer: Player,
  onComplete: () => void
) {
  setTimeout(() => {
    const aliveNPCs = gameState.players.filter(p => !p.isHuman && p.isAlive);
    let voteCount = 1;

    aliveNPCs.forEach((npc, index) => {
      setTimeout(() => {
        const votesForTarget = Math.random() < 0.5;

        if (votesForTarget) {
          addMessage(gameState, `${npc.name} votes for ${targetPlayer.name}`, "system");
          voteCount++;
        } else {
          const otherPlayers = gameState.players.filter(
            p => p.id !== targetPlayer.id && p.isAlive
          );
          const randomPlayer = getRandomElement(otherPlayers);
          addMessage(gameState, `${npc.name} votes for ${randomPlayer.name}`, "system");
        }

        if (index === aliveNPCs.length - 1) {
          finalizeVoting(gameState, targetPlayer, voteCount, onComplete);
        }
      }, 1000 * (index + 1));
    });
  }, 1000);
}

function finalizeVoting(
  gameState: GameState,
  targetPlayer: Player,
  voteCount: number,
  onComplete: () => void
) {
  const totalPlayers = gameState.players.filter(p => p.isAlive).length;
  const votesNeeded = Math.floor(totalPlayers / 2) + 1;

  setTimeout(() => {
    if (voteCount >= votesNeeded) {
      addMessage(gameState, `${targetPlayer.name} has been eliminated!`, "system");
      targetPlayer.isAlive = false;
      gameState.aliveCount[
        targetPlayer.role.toLowerCase() as keyof typeof gameState.aliveCount
      ]--;
    } else {
      addMessage(gameState, `Not enough votes to eliminate ${targetPlayer.name}.`, "system");
    }

    onComplete();
  }, 1000);
}

export function processNightAction(
  gameState: GameState,
  actionType: "kill" | "investigate" | "save",
  targetPlayer: Player
) {
  switch (actionType) {
    case "kill":
      addMessage(gameState, `You chose to kill ${targetPlayer.name}`, "system");
      break;
    case "investigate":
      addMessage(gameState, `You chose to investigate ${targetPlayer.name}`, "system");
      setTimeout(() => {
        const isMafia = targetPlayer.role === Role.MAFIA;
        addMessage(
          gameState,
          `Your investigation reveals that ${targetPlayer.name} is ${
            isMafia ? "a member of the Mafia!" : "not a member of the Mafia."
          }`,
          "system"
        );
      }, 2000);
      break;
    case "save":
      addMessage(gameState, `You chose to protect ${targetPlayer.name}`, "system");
      break;
  }
}
