# LLM Mafia Game Competition

## Overview

This project allows multiple Large Language Models (LLMs) to compete against each other in Mafia games. The game is simulated multiple times, and the winning rate of each model is recorded and displayed on a dashboard similar to Chatbot Arena.

## Features

- Uses **OpenRouter API** to interact with different LLMs.
- Simulates **Mafia games** where LLMs take on different roles (Mafia, Villager, Doctor).
- Runs the game **n times** and tracks win rates.
- Stores results in **Firebase** for real-time updates.
- Provides a **Flask-based dashboard** with graphical representation of model performance using **Matplotlib**.
- Supports **multiple languages** for game prompts and interactions.

## Dashboard

The dashboard displays:

1. **Win Rates Chart** - Bar chart showing win rates by model and role
2. **Games Played Chart** - Stacked bar chart showing games played by model and role
3. **Model Statistics Table** - Detailed statistics for each model
4. **Recent Games Table** - List of recent games with results

## Future Improvements

- Human vs LLMs 3D Mafia Game
- Extend to other games (Poker!) beyond Mafia.
- Create a real-time viewer for ongoing games.
- Add more complex roles like Detective, Jester, Sheriff, etc.

## Mafia Game Rules

### Roles

1. **Mafia** - Knows who other mafia members are. Can kill one villager each night.
2. **Villager** - Regular citizen with no special abilities. Can vote during the day.
3. **Doctor** - Can protect one player each night from Mafia kills.

### Game Structure

1. **Game Setup**:

   - Assign roles to each LLM randomly
   - Inform Mafia members of each other's identities
   - Other players know only their own roles

2. **Game Phases**:

   - **Night Phase**:
     - Mafia selects a player to kill
     - Doctor selects a player to save
   - **Day Phase**:
     - All surviving players discuss and vote to eliminate one player
     - Player with most votes is eliminated

3. **Win Conditions**:
   - **Mafia wins** when they equal or outnumber the villagers
   - **Villagers win** when all Mafia members are eliminated

### Standard Game Configuration

- 6-8 players total
- 1-2 Mafia members
- 1 Doctor
- Remaining players are Villagers

### Language Support

The game supports multiple languages for prompts and interactions:

- English (default)
- Spanish
- French
- Korean

You can configure the language by:

1. Setting the `LANGUAGE` environment variable
2. Modifying the `LANGUAGE` setting in `config.py`
3. Passing the language parameter when running a simulation

## Game Implementation

### Player Communication

Each LLM receives:

1. Its assigned role with abilities
2. The current game state (alive players, day/night, etc.)
3. Previous discussion history
4. For Mafia: identities of other Mafia members

### Decision Format

LLMs must respond in a structured format:

- **Night Actions**: `ACTION: [target player]` (e.g., "ACTION: Kill Claude" for Mafia, "ACTION: Protect Claude" for Doctor)
- **Day Discussions**: Free-form text followed by `VOTE: [player name]`

### Game Flow Mechanics

1. Initialize game with random role assignments
2. For each round:
   - Execute night phase (collect actions from Mafia and Doctor)
   - Process night actions (resolve kills and protections)
   - If win condition met, end game
   - Execute day phase (LLMs discuss and vote)
   - Eliminate player with most votes
   - If win condition met, end game

## Installation

### 1. Clone the Repository

```
git clone https://github.com/guzus/llm-mafia-game.git
cd llm-mafia-game
```

### 2. Install Dependencies

```
uv sync
```

### 3. Set Up Firebase

- Create a Firebase project and enable the Cloud Firestore.
- Download your `firebase_credentials.json` and place it in the project directory.

### 4. Set Up OpenRouter API

- Sign up at [OpenRouter](https://openrouter.ai/).
- Get an API key and add it to `config.py` (`OPENROUTER_API_KEY`).

## Configuration

Edit `config.py` to customize:

- `MODELS` - List of LLM models to include in the game
- `NUM_GAMES` - Number of games to simulate
- `PLAYERS_PER_GAME` - Number of players in each game
- `MAFIA_COUNT` - Number of Mafia players
- `DOCTOR_COUNT` - Number of Doctor players
- `GAME_TYPE` - Type of Mafia game to run
- `MAX_ROUNDS` - Maximum number of rounds before declaring a draw
- `API_TIMEOUT` - Timeout for API calls (in seconds)
- `RANDOM_SEED` - Random seed for reproducibility (set to None for random behavior)

## Usage

### 1. Run the Mafia Game Simulation

```
uv run src/simulate.py
```

This will:

- Run Mafia games `n` times.
- Store the results in Firebase.
- Print the final statistics.

### 2. Start the Dashboard

```
uv run src/dashboard.py
```

- Open `http://127.0.0.1:5000/` in your browser to view the leaderboard.

## Development

See [DEVELOPMENT.md](DEVELOPMENT.md) for more details on the development process.
