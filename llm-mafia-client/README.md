# LLM Mafia Game

A 3D web-based implementation of the classic Mafia (Werewolf) party game using Three.js, where you can play with LLM-powered characters.

## Overview

This game is a digital adaptation of the popular social deduction game Mafia (also known as Werewolf). Players are assigned secret roles and must work together or deceive others to achieve their team's objective.

In this implementation:

- The game is rendered in 3D using Three.js
- You play against LLM-powered NPCs (currently simulated with random responses)
- The game features day/night cycles, voting, and special role abilities

## Roles

- **Villager**: A regular townsperson trying to identify and eliminate the Mafia
- **Mafia**: Appears as a villager but secretly eliminates one player each night
- **Detective**: Can investigate one player each night to determine if they are Mafia
- **Doctor**: Can protect one player each night from being eliminated

## Game Flow

1. **Day Phase**: All players discuss and try to identify the Mafia
2. **Voting Phase**: Players vote to eliminate a suspected Mafia member
3. **Night Phase**: Special roles perform their actions
   - Mafia chooses a player to eliminate
   - Detective investigates a player
   - Doctor protects a player

## How to Play

1. Clone the repository
2. Install dependencies with `npm install`
3. Start the development server with `npm run dev`
4. Open your browser to the displayed URL (usually http://localhost:5173)

### Commands

During the day/voting phase:

- Type `vote for Player X` to vote for a player

During the night phase (depending on your role):

- Mafia: Type `kill Player X` to target a player
- Detective: Type `investigate Player X` to check if they're Mafia
- Doctor: Type `save Player X` to protect a player

## Future Improvements

- Integration with actual LLM API for more realistic NPC behavior
- More sophisticated game mechanics and additional roles
- Improved 3D visuals and animations
- Multiplayer support

## Technologies Used

- Three.js for 3D rendering
- TypeScript for type-safe code
- Vite for fast development and building

## License

MIT
