# LLM Mafia Game Competition

## Overview

This project allows multiple Large Language Models (LLMs) to compete against each other in Mafia games. The game is simulated multiple times, and the winning rate of each model is recorded and displayed on a dashboard similar to Chatbot Arena.

## Features

- Uses **OpenRouter API** to interact with different LLMs.
- Simulates **Mafia games** where LLMs take on different roles (Mafia, Villager, Doctor).
- Runs the game **n times** and tracks win rates.
- Stores results in **Firebase** for real-time updates.
- Provides a **Flask-based dashboard** with graphical representation of model performance using **Matplotlib**.

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

## Technologies Used

- **Python** for scripting the Mafia game simulation and dashboard.
- **OpenRouter API** to access LLMs.
- **Firebase** for storing game results.
- **Flask & Matplotlib** for a web-based leaderboard.

## Database Structure

The project uses **Firebase Realtime Database** to store game results and logs of interactions between LLMs. The database contains two main collections:

### 1. **Game Results Table (`mafia_games`)**

- Stores individual game outcomes.
- Fields:
  - `game_id`: Unique identifier for each game.
  - `timestamp`: Timestamp when the game was completed.
  - `game_type`: Type of Mafia game played (e.g., "Classic Mafia", "Advanced Mafia").
  - `participant_count`: The number of LLMs that participated in the game.
  - `winner`: The winning LLM models.
  - `participants`: A dictionary containing each LLM that participated and its assigned role:
    ```json
    {
      "gpt-4": "Mafia",
      "claude-3": "Villager",
      "gemini": "Doctor"
    }
    ```

### 2. **Game Logs Table (`game_logs`)**

- Stores full conversation logs between LLMs and their actions.
- Fields:
  - `game_id`: The associated game.
  - `timestamp`: Timestamp when the game was completed.
  - `game_type`: Type of Mafia game played (e.g., "Classic Mafia", "Advanced Mafia").
  - `participant_count`: The number of LLMs that participated in the game.
  - `rounds`: List of interactions per round, each containing:
    - `round_number`: The round index.
    - `messages`: A list of dialogue exchanges between LLMs, structured as:
      ```json
      [
        { "speaker": "gpt-4", "content": "I suspect mistral is the Mafia." },
        { "speaker": "mistral", "content": "I think gemini is lying!" }
      ]
      ```
    - `actions`: A record of decisions made by each LLM in that round (e.g., attack, protect, vote):
      ```json
      {
        "gpt-4": "Vote mistral",
        "mistral": "Kill claude-3",
        "gemini": "Protect claude-3"
      }
      ```
    - `eliminations`: List of LLMs eliminated that round:
      ```json
      ["claude-3"]
      ```
    - `outcome`: Summary of that round's results, including eliminations and any detected deception.

## Prompt Engineering

To ensure consistent behavior, each LLM receives a role-specific prompt:

### Mafia Prompt Template

```
You are playing a Mafia game as a Mafia member. Your goal is to eliminate the villagers.
Other Mafia members: {mafia_members}
All players: {all_players}
Current game state: {game_state}

During night phase, you must kill a non-Mafia player. Use format: ACTION: Kill [player]
During day phase, convince others you're innocent and vote to eliminate a villager.
Previous discussion: {discussion_history}

Your response:
```

### Doctor Prompt Template

```
You are playing a Mafia game as the Doctor. Your goal is to help villagers by protecting players from Mafia kills.
All players: {all_players}
Current game state: {game_state}

During night phase, you can protect one player. Use format: ACTION: Protect [player]
During day phase, use your observations to help eliminate Mafia members.
Previous discussion: {discussion_history}

Your response:
```

### Villager Prompt Template

```
You are playing a Mafia game as a Villager. Your goal is to identify and eliminate the Mafia.
All players: {all_players}
Current game state: {game_state}

During day phase, discuss with other villagers to identify the Mafia members.
End your message with your vote. Use format: VOTE: [player]
Previous discussion: {discussion_history}

Your response:
```

## Installation

### 1. Clone the Repository

```
git clone https://github.com/your-repo/llm-mafia-game.git
cd llm-mafia-game
```

### 2. Install Dependencies

```
uv sync
```

### 3. Set Up Firebase

- Create a Firebase project and enable the Realtime Database.
- Download your `firebase_credentials.json` and place it in the project directory.
- Update `databaseURL` in the script to match your Firebase URL.

### 4. Set Up OpenRouter API

- Sign up at [OpenRouter](https://openrouter.ai/).
- Get an API key and add it to the script (`OPENROUTER_API_KEY`).

## Configuration

Edit `config.py` to customize:

- `MODELS` - List of LLM models to include in the game
- `NUM_GAMES` - Number of games to simulate
- `PLAYERS_PER_GAME` - Number of players in each game
- `MAFIA_COUNT` - Number of Mafia players
- `GAME_TYPE` - Type of Mafia game to run

## Usage

### 1. Run the Mafia Game Simulation

```
uv run simulate.py
```

This will:

- Run Mafia games `n` times.
- Store the results in Firebase.
- Print the final statistics.

### 2. Start the Dashboard

```
uv run dashboard.py
```

- Open `http://127.0.0.1:5000/` in your browser to view the leaderboard.

## Dashboard Preview

The dashboard displays a **bar chart** of LLM win rates using **Matplotlib**.

## Future Improvements

- Extend to other games beyond Mafia.
- Add more complex roles like Detective, Jester, Sheriff, etc.
