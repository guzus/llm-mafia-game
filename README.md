# LLM Mafia Game Competition

## Overview

This project allows multiple Large Language Models (LLMs) to compete against each other in Mafia games. The game is simulated multiple times, and the winning rate of each model is recorded and displayed on a dashboard similar to Chatbot Arena.

## Features

- Uses **OpenRouter API** to interact with different LLMs.
- Simulates **Mafia games** where LLMs take on different roles (Mafia, Villager, Detective, Doctor).
- Runs the game **n times** and tracks win rates.
- Stores results in **Firebase** for real-time updates.
- Provides a **Flask-based dashboard** with graphical representation of model performance using **Matplotlib**.

## Technologies Used

- **Python** for scripting the Mafia game simulation and dashboard.
- **OpenRouter API** to access LLMs.
- **Firebase** for storing game results.
- **Flask & Matplotlib** for a web-based leaderboard.

## Database Structure

The project uses **Firebase Realtime Database** to store game results and logs of interactions between LLMs. The database contains two main collections:

### 1. **Game Results Table (\*\***`mafia_games`\***\*)**

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
      "mistral": "Detective",
      "gemini": "Doctor"
    }
    ```

### 2. **Game Logs Table (\*\***`game_logs`\***\*)**

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
    - `outcome`: Summary of that round’s results, including eliminations and any detected deception.

This setup allows for detailed analysis of how different models strategize and interact during the game.

## Installation

### 1. Clone the Repository

```sh
git clone https://github.com/your-repo/llm-mafia.git
cd llm-mafia
```

### 2. Install Dependencies

```sh
pip install requests firebase-admin flask matplotlib
```

### 3. Set Up Firebase

- Create a Firebase project and enable the Realtime Database.
- Download your `firebase_credentials.json` and place it in the project directory.
- Update `databaseURL` in the script to match your Firebase URL.

### 4. Set Up OpenRouter API

- Sign up at [OpenRouter](https://openrouter.ai/).
- Get an API key and add it to the script (`OPENROUTER_API_KEY`).

## Usage

### 1. Run the Mafia Game Simulation

```sh
python mafia_game.py
```

This will:

- Run Mafia games `n` times.
- Store the results in Firebase.
- Print the final statistics.

### 2. Start the Dashboard

```sh
python app.py
```

- Open `http://127.0.0.1:5000/` in your browser to view the leaderboard.

## Dashboard Preview

The dashboard displays a **bar chart** of LLM win rates using **Matplotlib**.

## Future Improvements

- Extend to other games beyond Mafia.
