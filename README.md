# LLM Mafia Game

<div align="center">
  <img src="./docs/static/img/banner.png" alt="LLM Mafia Game Banner" width="100%" />
</div>

https://github.com/user-attachments/assets/54976d88-6ef1-4c1c-9737-8635b33fd9f0

## Overview

This project allows multiple LLMs to compete against each other in Mafia games. The game is simulated multiple times, and the winning rate of each model is recorded and displayed on a dashboard. You can also see the full game history of each game. The game rules are based on the [Mafia Game Rules](docs/GAME_RULE.md).

## Quick Start

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

### 5. Run the Mafia Game Simulation

```
uv run src/simulate.py
```

This will:

- Run Mafia games `n` times.
- Store the results in Firebase.
- Print the final statistics.

### 6. Start the Dashboard

```
uv run src/dashboard.py
```

- Open `http://127.0.0.1:5000/` in your browser to view the leaderboard.

## Future Improvements

- Human vs LLMs 3D Mafia Game
- Extend to other games (Poker, etc.) beyond Mafia.
- Create a real-time viewer, chat, and betting system for ongoing games.
- Add more complex roles like Detective, Jester, Sheriff, etc.

## Development

See [DEVELOPMENT.md](docs/DEVELOPMENT.md) for more details on the development process.
