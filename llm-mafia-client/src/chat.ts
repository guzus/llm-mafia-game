import { GameState, GamePhase, Role } from "./types";

// Simple responses for the LLM characters (to be replaced with actual LLM integration)
const mafiaResponses = [
  "I think we should focus on finding the real mafia.",
  "I was just checking on the village last night, I'm innocent.",
  "I suspect Player 3, they've been very quiet.",
  "I'm a villager, I promise!",
  "Let's work together to find the mafia.",
];

const villagerResponses = [
  "I'm just a simple villager trying to survive.",
  "I think Player 2 is acting suspicious.",
  "I didn't see anything unusual last night.",
  "We need to be careful who we vote for.",
  "I trust Player 4, they seem honest.",
];

const detectiveResponses = [
  "I have some information that might help us.",
  "Based on my observations, Player 5 might be suspicious.",
  "Let's think logically about this situation.",
  "I was watching carefully last night.",
  "I think we should vote for Player 1.",
];

const doctorResponses = [
  "I want to help keep the village safe.",
  "I think we should protect each other.",
  "Player 6 seems trustworthy to me.",
  "I'm concerned about the safety of our village.",
  "Let's be careful with our accusations.",
];

// Function to get a random response based on role
function getRandomResponse(role: Role): string {
  const responses = {
    [Role.MAFIA]: mafiaResponses,
    [Role.VILLAGER]: villagerResponses,
    [Role.DETECTIVE]: detectiveResponses,
    [Role.DOCTOR]: doctorResponses,
  };

  const roleResponses = responses[role];
  return roleResponses[Math.floor(Math.random() * roleResponses.length)];
}

// Function to handle chat interactions
export function handleChat(gameState: GameState) {
  const chatInput = document.getElementById("chat-input") as HTMLInputElement;
  const sendButton = document.getElementById(
    "send-button"
  ) as HTMLButtonElement;

  if (!chatInput || !sendButton) {
    console.error("Chat elements not found");
    return;
  }

  // Handle send button click
  sendButton.addEventListener("click", () => {
    sendMessage();
  });

  // Handle enter key press
  chatInput.addEventListener("keypress", (event) => {
    if (event.key === "Enter") {
      sendMessage();
    }
  });

  // Function to send a message
  function sendMessage() {
    const message = chatInput.value.trim();

    if (message) {
      // Add player message to chat
      addMessage(message, "player");

      // Clear input
      chatInput.value = "";

      // Process player message
      processPlayerMessage(message);

      // Get NPC responses (simulating LLM responses)
      setTimeout(() => {
        getNPCResponses();
      }, 1000);
    }
  }

  // Function to add a message to the chat
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
        sender:
          type === "player" ? "player" : type === "llm" ? "npc" : "system",
        timestamp: new Date().toISOString(),
      });
    }
  }

  // Function to process player message
  function processPlayerMessage(message: string) {
    // Check for voting command
    if (
      gameState.phase === GamePhase.DAY ||
      gameState.phase === GamePhase.VOTING
    ) {
      const voteMatch = message.match(/vote (?:for )?(?:player )?(\d+)/i);

      if (voteMatch) {
        const playerNumber = parseInt(voteMatch[1]);
        const targetPlayer = gameState.players.find(
          (p) => p.name === `Player ${playerNumber}`
        );

        if (targetPlayer) {
          addMessage(`You voted for ${targetPlayer.name}`, "system");

          // Move to voting phase if not already
          if (gameState.phase === GamePhase.DAY) {
            gameState.phase = GamePhase.VOTING;
            updateGameStatus();
          }

          // Simulate other players voting
          simulateVoting(targetPlayer);
        } else {
          addMessage(`Player ${playerNumber} not found`, "system");
        }
      }
    }

    // Check for night action commands
    if (gameState.phase === GamePhase.NIGHT) {
      // If player is mafia
      if (gameState.playerRole === Role.MAFIA) {
        const killMatch = message.match(/kill (?:player )?(\d+)/i);

        if (killMatch) {
          const playerNumber = parseInt(killMatch[1]);
          const targetPlayer = gameState.players.find(
            (p) => p.name === `Player ${playerNumber}`
          );

          if (targetPlayer) {
            addMessage(`You chose to kill ${targetPlayer.name}`, "system");
            // Process kill action (would be handled in game logic)
          }
        }
      }

      // If player is detective
      if (gameState.playerRole === Role.DETECTIVE) {
        const investigateMatch = message.match(
          /investigate (?:player )?(\d+)/i
        );

        if (investigateMatch) {
          const playerNumber = parseInt(investigateMatch[1]);
          const targetPlayer = gameState.players.find(
            (p) => p.name === `Player ${playerNumber}`
          );

          if (targetPlayer) {
            addMessage(
              `You chose to investigate ${targetPlayer.name}`,
              "system"
            );
            // Process investigate action (would be handled in game logic)

            // Give result
            setTimeout(() => {
              if (targetPlayer.role === Role.MAFIA) {
                addMessage(
                  `Your investigation reveals that ${targetPlayer.name} is a member of the Mafia!`,
                  "system"
                );
              } else {
                addMessage(
                  `Your investigation reveals that ${targetPlayer.name} is not a member of the Mafia.`,
                  "system"
                );
              }
            }, 2000);
          }
        }
      }

      // If player is doctor
      if (gameState.playerRole === Role.DOCTOR) {
        const saveMatch = message.match(/save (?:player )?(\d+)/i);

        if (saveMatch) {
          const playerNumber = parseInt(saveMatch[1]);
          const targetPlayer = gameState.players.find(
            (p) => p.name === `Player ${playerNumber}`
          );

          if (targetPlayer) {
            addMessage(`You chose to protect ${targetPlayer.name}`, "system");
            // Process save action (would be handled in game logic)
          }
        }
      }
    }
  }

  // Function to get NPC responses
  function getNPCResponses() {
    // Only get responses during day phase
    if (gameState.phase === GamePhase.DAY) {
      // Get 1-3 random NPCs to respond
      const aliveNPCs = gameState.players.filter(
        (p) => !p.isHuman && p.isAlive
      );
      const responseCount = Math.min(
        Math.floor(Math.random() * 3) + 1,
        aliveNPCs.length
      );

      const respondingNPCs = [...aliveNPCs];
      // Shuffle array
      for (let i = respondingNPCs.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        [respondingNPCs[i], respondingNPCs[j]] = [
          respondingNPCs[j],
          respondingNPCs[i],
        ];
      }

      // Take only the number we need
      respondingNPCs.splice(responseCount);

      // Have each NPC respond with a delay
      respondingNPCs.forEach((npc, index) => {
        setTimeout(() => {
          const response = getRandomResponse(npc.role);
          addMessage(`${npc.name}: ${response}`, "llm");
        }, 1000 * (index + 1));
      });
    }
  }

  // Function to simulate voting
  function simulateVoting(targetPlayer: any) {
    // Simulate other players voting
    setTimeout(() => {
      const aliveNPCs = gameState.players.filter(
        (p) => !p.isHuman && p.isAlive
      );
      let voteCount = 1; // Player's vote

      aliveNPCs.forEach((npc, index) => {
        setTimeout(() => {
          // 50% chance to vote for the same target
          const votesForTarget = Math.random() < 0.5;

          if (votesForTarget) {
            addMessage(`${npc.name} votes for ${targetPlayer.name}`, "system");
            voteCount++;
          } else {
            // Vote for a random other player
            const otherPlayers = gameState.players.filter(
              (p) => p.id !== targetPlayer.id && p.isAlive
            );
            const randomPlayer =
              otherPlayers[Math.floor(Math.random() * otherPlayers.length)];
            addMessage(`${npc.name} votes for ${randomPlayer.name}`, "system");
          }

          // Check if all votes are in
          if (index === aliveNPCs.length - 1) {
            // Determine if target is eliminated
            const totalPlayers = gameState.players.filter(
              (p) => p.isAlive
            ).length;
            const votesNeeded = Math.floor(totalPlayers / 2) + 1;

            setTimeout(() => {
              if (voteCount >= votesNeeded) {
                addMessage(
                  `${targetPlayer.name} has been eliminated!`,
                  "system"
                );
                targetPlayer.isAlive = false;

                // Update alive count
                gameState.aliveCount[
                  targetPlayer.role.toLowerCase() as keyof typeof gameState.aliveCount
                ]--;

                // Check win conditions
                checkWinConditions();
              } else {
                addMessage(
                  `Not enough votes to eliminate ${targetPlayer.name}.`,
                  "system"
                );
              }

              // Move to night phase if game is not over
              if (!gameState.winner) {
                setTimeout(() => {
                  gameState.phase = GamePhase.NIGHT;
                  gameState.day++;
                  updateGameStatus();
                  addMessage("Night falls on the village...", "system");

                  // Simulate night actions
                  simulateNightActions();

                  // Move back to day phase after night
                  setTimeout(() => {
                    if (!gameState.winner) {
                      gameState.phase = GamePhase.DAY;
                      updateGameStatus();
                      addMessage(
                        "The sun rises. Time for discussion.",
                        "system"
                      );
                    }
                  }, 5000);
                }, 2000);
              }
            }, 1000);
          }
        }, 1000 * (index + 1));
      });
    }, 1000);
  }

  // Function to simulate night actions
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

      // Only show mafia actions to player if they are mafia
      if (gameState.playerRole === Role.MAFIA) {
        addMessage(`The Mafia chose to target ${randomTarget.name}`, "system");
      }

      // Simulate kill (unless saved by doctor)
      let targetKilled = true;

      // Doctor protection
      const doctorPlayers = gameState.players.filter(
        (p) => p.role === Role.DOCTOR && p.isAlive
      );
      if (doctorPlayers.length > 0) {
        // 30% chance doctor saves the target
        if (Math.random() < 0.3) {
          targetKilled = false;

          // Only show to player if they are doctor
          if (gameState.playerRole === Role.DOCTOR) {
            addMessage(
              `You successfully protected ${randomTarget.name} from the Mafia!`,
              "system"
            );
          }
        }
      }

      // Process kill if not saved
      if (targetKilled) {
        randomTarget.isAlive = false;
        gameState.aliveCount[
          randomTarget.role.toLowerCase() as keyof typeof gameState.aliveCount
        ]--;

        // Announce death in the morning
        setTimeout(() => {
          addMessage(
            `${randomTarget.name} was killed during the night!`,
            "system"
          );

          // Check win conditions
          checkWinConditions();
        }, 5000);
      } else {
        // Announce that no one died
        setTimeout(() => {
          addMessage("Everyone survived the night!", "system");
        }, 5000);
      }
    }

    // Detective investigates someone (only if player is not detective)
    if (gameState.playerRole !== Role.DETECTIVE) {
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
          // This would be processed in game logic
        }
      }
    }

    // Doctor protects someone (only if player is not doctor)
    if (gameState.playerRole !== Role.DOCTOR) {
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
          // This would be processed in game logic
        }
      }
    }
  }

  // Function to check win conditions
  function checkWinConditions() {
    // Mafia wins if they equal or outnumber villagers
    if (
      gameState.aliveCount.mafia >=
      gameState.aliveCount.villager +
        gameState.aliveCount.detective +
        gameState.aliveCount.doctor
    ) {
      gameState.winner = "Mafia";
      gameState.phase = GamePhase.GAME_OVER;
      updateGameStatus();
      addMessage("The Mafia has taken over the village! Mafia wins!", "system");
    }

    // Village wins if all mafia are eliminated
    if (gameState.aliveCount.mafia === 0) {
      gameState.winner = "Village";
      gameState.phase = GamePhase.GAME_OVER;
      updateGameStatus();
      addMessage(
        "All members of the Mafia have been eliminated! Village wins!",
        "system"
      );
    }
  }

  // Function to update game status display
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
}
